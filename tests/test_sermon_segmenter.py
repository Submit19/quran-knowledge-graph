"""Unit tests for the Khalifa sermon scraper's parsing + speaker segmentation.

The Khalifa-only source rule binds: the corpus may contain only Rashad's own
words. These tests pin the two correctness-critical behaviours —

  1. default-speaker classification from the video title, and
  2. stateful speaker segmentation (a label appears only on speaker *change*).

A regression in either would silently leak another speaker's words into the
corpus (rule violation) or silently drop Rashad's own speech (data loss).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scrape_khalifa_sermons import (  # noqa: E402
    default_speaker_is_rashad,
    parse_vtt,
    segment_rashad,
)


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Friday Sermons 1989 #3 (audio) Dr Rashad Khalifa", True),
        ("Friday Sermon by Dr. Rashad Khalifa", True),
        ("RK audio the end of the world is coming soon part 1", True),
        ("lecture Dr Rashad Khalifa", True),
        ("Khutba on the Quran", True),
        # Community-led sessions: Rashad is NOT the default speaker.
        ("Quran Study by Linda", False),
        ("Submission Quran Study by Edip Yuksel", False),
        ("Sunday Quran Study by Lori", False),
        ("Quran Study session by Kathryn", False),
        # Ambiguous / no speaker named => conservative (not Rashad).
        ("some random title", False),
        ("", False),
    ],
)
def test_default_speaker_classification(title, expected):
    assert default_speaker_is_rashad(title) is expected


def test_parse_vtt_strips_headers_and_timestamps():
    vtt = (
        "WEBVTT\n"
        "Kind: captions\n"
        "Language: en-US\n"
        "\n"
        "00:01:31.360 --> 00:01:32.760\n"
        "Al-Hamdu Lillah\n"
        "\n"
        "00:01:33.360 --> 00:01:34.680\n"
        "we praise God\n"
    )
    cues = parse_vtt(vtt)
    assert cues == ["Al-Hamdu Lillah", "we praise God"]
    assert all("WEBVTT" not in c and "-->" not in c for c in cues)


def test_multiline_cue_joined():
    vtt = (
        "WEBVTT\n\n"
        "00:00:01.000 --> 00:00:03.000\n"
        "and I bear witness that there is no other god\n"
        " besides the one God\n"
    )
    assert parse_vtt(vtt) == [
        "and I bear witness that there is no other god besides the one God"
    ]


def test_segment_default_rashad_keeps_unlabeled_drops_others():
    # Sermon: Rashad is default; a label only marks a speaker change.
    cues = [
        "Al-Hamdu Lillah",  # unlabeled -> Rashad (default)
        "we praise God",  # unlabeled -> still Rashad
        "Ahmad's wife:  he's not here yet",  # switch -> other
        "Rashad:  you are his wife",  # switch back -> Rashad
        "good for you",  # unlabeled -> still Rashad
        "Edip: 8",  # switch -> other
        "Rashad:  letters",  # switch back -> Rashad
    ]
    kept, n_kept, n_drop = segment_rashad(cues, default_rashad=True)
    assert kept == [
        "Al-Hamdu Lillah",
        "we praise God",
        "you are his wife",
        "good for you",
        "letters",
    ]
    assert n_kept == 5
    assert n_drop == 2  # the two other-speaker turns


def test_segment_default_other_keeps_only_explicit_rashad():
    # Study session: leader is default; only explicit Rashad turns are kept.
    cues = [
        "today we will study sura 2",  # unlabeled -> leader (dropped)
        "verse 255 is Ayat al-Kursi",  # unlabeled -> leader (dropped)
        "Rashad:  that is correct",  # switch -> Rashad (kept)
        "and it speaks of God's throne",  # unlabeled -> still Rashad (kept)
        "Linda:  thank you",  # switch -> other (dropped)
    ]
    kept, n_kept, n_drop = segment_rashad(cues, default_rashad=False)
    assert kept == ["that is correct", "and it speaks of God's throne"]
    assert n_kept == 2


def test_numeric_verse_ref_not_treated_as_speaker_label():
    # "4:69" must NOT be parsed as a speaker label (digit start, no name).
    cues = ["the verse is 4:69 which says", "this is the truth"]
    kept, n_kept, _ = segment_rashad(cues, default_rashad=True)
    assert kept == ["the verse is 4:69 which says", "this is the truth"]


@pytest.mark.parametrize(
    "prose",
    [
        "in the famous book: God is doing everything",  # mid-sentence colon
        "he says: I will deliver the message",
        "which means: the soul never dies",
        "but they said: we will not believe",
        "you simply say to god: my Lord",
    ],
)
def test_prose_colon_does_not_flip_speaker(prose):
    # A prose colon ("he says: ...") must NOT be read as a speaker change.
    # The bug: it flipped the default-Rashad speaker OFF mid-monologue and
    # silently dropped the rest of his words (measured -9% / -27.6K words).
    cues = [
        "God is in full control of everything",  # Rashad (default)
        prose,  # prose colon — must stay Rashad
        "and that is the whole point of submission",  # must remain kept
    ]
    kept, n_kept, n_drop = segment_rashad(cues, default_rashad=True)
    assert n_kept == 3
    assert n_drop == 0
    assert kept[2] == "and that is the whole point of submission"
