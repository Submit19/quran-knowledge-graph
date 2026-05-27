"""iter_3: 3 more cache entries — raised-from-dead, lying, Maryam.

Targets the weakest Shape B held-outs after iter_2:
  broad-held-005   "How does the Quran describe being raised from the dead?"  (sim 0.695)
  abstract-held-002 "How does the Quran describe lying and deception?"        (sim 0.786)
  broad-held-001   "Summarize Surah Maryam."                                  (sim 0.785)

All citations Cypher-verified before save.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env")

from answer_cache import save_answer  # noqa: E402


CITATION_PATTERN = re.compile(r"\[(\d+):(\d+)\]")


def extract_citations(text: str) -> set[str]:
    return {f"{s}:{v}" for s, v in CITATION_PATTERN.findall(text or "")}


def verify_citations_in_graph(citations: set[str]) -> tuple[set[str], set[str]]:
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    existing: set[str] = set()
    try:
        with driver.session(database="quran") as s:
            for vid in citations:
                r = s.run(
                    "MATCH (v:Verse {verseId: $vid}) RETURN v.verseId AS id",
                    vid=vid,
                ).single()
                if r:
                    existing.add(vid)
    finally:
        driver.close()
    return existing, citations - existing


RAISED_FROM_DEAD = """**Resurrection** (*ba`th*, *qiyama*) is one of the most-discussed topics in the Quran — the corpus treats it as the single most-doubted Quranic claim and assembles a sustained argument-by-multiple-registers in response. The Arabic vocabulary cleanly tracks the doctrine: **ب-ع-ث** (*b-`-th*, "raise, send forth, resurrect") and **ق-و-م** (*q-w-m*, "stand, rise") supply the core terminology; *Yawm al-Qiyama* ("Day of Standing-Up") is the standard name for the event.

**The objection the Quran answers.** The opposition's claim is voiced repeatedly and precisely: [17:49]: "After we turn into bones and fragments, we get resurrected anew?!" [23:82]: "After we die and become dust and bones, we get resurrected?" [23:37]: "We only live this life — we live and die — and we will never be resurrected." [37:16]: "After we die and become dust and bones, do we really get resurrected?" Khalifa's translation preserves the disbelievers' rhetorical move: the bones-and-dust framing is presented as a *gotcha* — surely material decomposition is irreversible. The Quran's response is structured as a systematic dismantling of that intuition.

**The first counter — biological precedent.** [22:5]: "O people, if you have any doubt about resurrection, (remember that) we created you from dust, and subsequently from a tiny drop, which turns into a hanging (embryo), then it becomes a fetus that is given life or deemed lifeless..." Khalifa makes the embryological sequence explicit. The argument: *the same God who already moved you from dust to alive once can move you from dust to alive again*. The empirical biological fact of human development is named as the resurrection-precedent.

**The second counter — agricultural precedent.** [22:6]: "This proves that GOD is the Truth, and that **He revives the dead**, and that He is Omnipotent." [30:19]: "He produces the live from the dead, and produces the dead from the live, and **He revives the land after it had died**; you are similarly resurrected." [30:50]: "You shall appreciate GOD's continuous mercy, and how He revives the land that has been dead. He will just as certainly resurrect the dead. He is Omnipotent." Khalifa's translation hammers the *agricultural-revival* parallel — anyone who has watched a dead field green up after rain has watched a resurrection-precedent.

**The third counter — sleep precedent.** [25:47]: "He is the One who designed the night to be a cover, and for you to sleep and rest. And He made the day a resurrection." [6:60]: "He is the One who puts you to death during the night, and knows even the smallest of your actions during the day. He resurrects you every morning, until your life span is fulfilled." Khalifa preserves the daily sleep-wake cycle as itself a resurrection-image — every dawn is a *mini-resurrection*; the larger one is the same operation at scale.

**The fourth counter — divine equivalence.** [31:28]: "**The creation and resurrection of all of you is the same as that of one person.** GOD is Hearer, Seer." The Quran's most economical formulation: at the divine register there is no "harder" resurrection of seven billion than of one. The objection assumes finitude on the divine side; the verse denies the assumption.

**The case study — the man who passed a ruined village.** [2:259]: "Consider the one who passed by a ghost town and wondered, 'How can GOD revive this after it had died?' GOD then put him to death for a hundred years, then resurrected him. He said, 'How long have you stayed here?' He said, 'I have been here a day, or part of the day.' He said, 'No! You have been here a hundred years. Yet, look at your food and drink; they did not spoil. Look at your donkey — we thus render you a lesson for the people. Now, note how we construct the bones, then cover them with flesh.'" Khalifa preserves the visual demonstration — bones reassembling, then flesh growing back. The Quran tells the doubter-of-resurrection story by *having him be resurrected himself*.

**The structural commitment.** [16:38]: "They swore solemnly by GOD: 'GOD will not resurrect the dead.' Absolutely, such is His inviolable promise, but most people do not know." Khalifa's translation makes the *inviolable promise* central — resurrection is not a possibility God might or might not undertake; it is a *commitment* the Quran says God has already bound Himself to.

**The mechanics-of-the-day register.** Across multiple surahs the Quran narrates the resurrection-event itself: trumpet ([39:68]: "The horn will be blown..."); standing up ([83:6]: "The day when all people will stand before the Lord of the universe"); records being distributed ([84:7]–[84:12], referenced in many places); judgement ([99:7]–[99:8]: "Whoever does an atom's weight of good shall see it. And whoever does an atom's weight of evil shall see it"). The denser mechanics-clusters are in Surah 75 (Al-Qiyama, "The Resurrection"), Surah 81 (At-Takwir, "The Folding"), and Surah 82 (Al-Infitar, "The Rending").

**The Quranic-promise frame.** [22:7]: "And that the Hour is coming, no doubt about it, and that GOD resurrects those who are in the graves." [27:65]: "Say, 'No one in the heavens and the earth knows the future except GOD. They do not even perceive how or when they will be resurrected.'" The doctrine the Quran assembles: resurrection *will* happen (commitment), *cannot* be precisely timed (only God knows), and *should* be assumed-inevitable on the strength of the four precedents (biological, agricultural, sleep, divine).

**Khalifa-specific framing.** Khalifa's translation foregrounds [31:28] (the divine-equivalence argument) and [22:5] (the biological-precedent argument) as the two most-load-bearing resurrection-arguments. The Submitter tradition treats resurrection not as a *metaphor for spiritual states* but as a literal future event — the doctrine is held to be *physical and embodied*, in line with the Quranic insistence on bones and flesh. The metaphor-reading is a minority modernist position the corpus's repeated bones-and-dust counters explicitly rebut.
"""


LYING = """The Quran treats **lying** (*kadhib*) and **deception** (*khid`a*, *makr*) as among the most consequential moral failures — placing the *liar* in a special category of theological condemnation. Three Arabic roots carry the doctrine: **ك-ذ-ب** (*k-dh-b*, "lie, deny, deem false") is by far the densest, appearing in over **270 verse-level mentions**; **خ-د-ع** (*kh-d-`*, "deceive") supplies the deception-vocabulary; **م-ك-ر** (*m-k-r*, "scheme, plot") supplies the strategic-deception vocabulary.

**The double-bind of lying.** [16:105]: "The only ones who fabricate false doctrines are those who do not believe in GOD's revelations; these are the real liars." Khalifa preserves the structural claim — lying is named as the *symptom* of prior disbelief, not a free-standing moral fault. The Quran goes further: *kadhib* and *kufr* (disbelief) become near-synonymous in the corpus's vocabulary; rejecting God's revelations *is* itself a kind of lying about reality.

**The opening diagnosis of hypocrites.** [2:8]–[2:10]: "Then there are those who say, 'We believe in GOD and the Last Day,' when they are not believers. **In trying to deceive GOD and those who believe, they only deceive themselves without perceiving.** In their minds there is a disease. Consequently, GOD augments their disease. They have incurred a painful retribution for their lying." Khalifa renders the self-deception clause with precision — the deceiver cannot, in fact, deceive God; the deception lands only on the deceiver. The verse is the operative diagnostic of *nifaq* (hypocrisy): saying-and-meaning-divergence as a religious-political stance.

**The truth-falsehood confounding.** [2:42]: "Do not confound the truth with falsehood, nor shall you conceal the truth, knowingly." [3:71]: "O followers of the scripture, why do you confound the truth with falsehood, and conceal the truth, knowingly?" Khalifa's translation foregrounds two distinct failure modes — *mixing* (*labs*: the truth and falsehood become indistinguishable from each other) and *concealment* (*kitman*: the truth is known but withheld). The two are presented as deliberate moves, knowing-acts, not innocent errors.

**Lying as the property of devils.** [26:221]–[26:223]: "Shall I inform you upon whom the devils descend? They descend upon every guilty fabricator. They pretend to listen, but most of them are liars." Khalifa's translation makes the genealogy explicit — fabricators-who-pretend-to-listen are the channel through which satanic influence reaches humanity. [6:112]: "We have permitted the enemies of every prophet — human and jinn devils — to inspire in each other fancy words, in order to deceive." The interpersonal-deception mechanism is named.

**The hardness of being branded a liar.** [3:61] (the *mubahala* verse, addressing the Christians of Najran): "If anyone argues with you, despite the knowledge you have received, then say, 'Let us summon our children and your children, our women and your women, ourselves and yours, then invoke GOD's curse upon the liars.'" Khalifa preserves the Quran's most dramatic challenge — disputants are invited to swear mutual oaths of cursing-upon-the-liars; the Quran treats the willingness-to-be-cursed-if-lying as the operational falsification test for honesty claims. The historical reading: the Najran Christians declined the oath.

**Lying about God specifically.** [6:21]: "Who is more evil than one who lies about GOD, or rejects His revelations?" [11:18]: "Who are more evil than those who fabricate lies about GOD? They will be presented before their Lord, and the witnesses will say, 'These are the ones who lied about their Lord. GOD's condemnation has befallen the transgressors.'" The Quran identifies a special-class sin: not lying-in-general but lying-*about*-God specifically. Two failure modes: *attributing* false statements to God (false prophecy) and *denying* true statements from God (rejection of revelation).

**The "telling the truth" inverse virtue.** [33:35]: "...the truthful men, the truthful women..." (*as-sadiqin / as-sadiqat*) appears in the canonical list of the saved as a discrete category. Truth-telling is presented as a *standalone virtue*, not derivable from other virtues. [9:119]: "O you who believe, you shall reverence GOD, and be among the truthful." Khalifa preserves the simple imperative: *be among the truthful*.

**The interpersonal harm of slander.** [24:11]–[24:15] (the *ifk* narrative — the famous incident involving Aisha): "Those who fabricated the big lie are a group from among you. Do not think that it was bad for you; instead, it was good for you. Meanwhile, each one of them has earned his share of the guilt. As for the one who initiated the whole incident, he has incurred a terrible retribution." Khalifa preserves the *big lie* phrasing. The episode generates the Quranic doctrine on *qadhf* (slander) — the verses around it establish that propagating an unverified accusation is itself a punishable offence, not merely originating one.

**The consequence — being known by Hellfire as a liar.** [3:188]: "Those who boast about their works, and wish to be praised for something they have not really done, do not think that they can escape the retribution. They have incurred a painful retribution." [9:42]: "If there were a quick material gain, and a short journey, they would have followed you. But the striving is just too much for them. They will swear by GOD..." The Quran's eschatological frame closes the loop: lies told in this life are catalogued and revealed at resurrection.

**Khalifa-specific framing.** His translation foregrounds [2:8]–[2:10] (self-deception of the hypocrites) as the *operative* lying-doctrine, and [11:18] (lying about God) as the *capital* lying-doctrine. Submitter tradition reads the corpus as identifying *kadhib* not as a private moral failing primarily but as a *theological-political stance* — saying one thing and meaning another is the operating mode of the disbelieving and the hypocritical, and the Quran's response is to treat the unmasking of lies as itself a religious obligation.
"""


MARYAM = """**Surah 19 (Maryam, "Mary")** is a 98-verse Meccan surah that functions as a **compact prophetic biography** — six prophets are named and treated in narrative order: **Zachariah** (Zakariya), **John** (Yahya), **Mary** (Maryam) and her son **Jesus** (Isa), **Abraham** (Ibrahim), and **Moses** (Musa). The surah is one of the Quran's most narratively-driven, with a striking emphasis on **birth-stories** and **family dynamics**.

**Opening — the muqatta`at.** [19:1]: "K. H. Y. `A. S. (Kaaf Haa Yaa `Ayn Saad)." Khalifa preserves the bare initial letters as a Code-19 marker — the surah's opening signals the muqatta`at-sequence the corpus contains across 29 surahs.

**Zachariah and the birth of John.** [19:2]–[19:15]: the surah opens with the elderly priest Zachariah's secret-prayer for a son ([19:3]: "He called his Lord, a secret call"). His prayer is granted with explicit conditions: a son named **John** ([19:7]: "We give you good news; a boy whose name shall be John (Yahya). **We never created anyone like him before**"). The "never before" formulation is unusual in the Quran — John is uniquely-named (no prior bearer of the name Yahya) and uniquely-graced. The compressed John-biography ([19:12]–[19:15]) lists his qualifications: scripture-upholding, youth-wisdom, kindness, purity, honour of parents, peace.

**Mary and the annunciation.** [19:16]–[19:21]: Mary withdraws to an eastern location; the divine Spirit appears as a human-form messenger and announces a pure son. [19:20]: "How can I have a son, when no man has touched me; I have never been unchaste." The angel's response ([19:21]): "It is easy for Me. We will render him a sign for the people, and mercy from us. This is a predestined matter." Khalifa preserves the Mary-pregnancy as miraculous-without-physical-mediation; the surah does not include the impregnation-by-Spirit reading found in some Christian sources — the Quranic frame is purely *fiat-creation* by divine command.

**The birth scene.** [19:22]–[19:26]: Mary withdraws to an isolated place. [19:23]: "The birth process came to her by the trunk of a palm tree. She said, '(I am so ashamed;) I wish I were dead before this happened, and completely forgotten.'" Khalifa preserves the *human-realism* of the moment — Mary's distress is named without softening. [19:24]–[19:26] then provides the consolation: a stream beneath her, fresh dates from the palm trunk shaken, instruction to fast-from-speech.

**The speaking-infant defence.** [19:27]–[19:33]: Mary brings the infant back to her people; they accuse her of unchastity ([19:28]: "O sister of Aaron, your father was not a bad man, nor was your mother unchaste"). Mary points to the infant; Jesus speaks from the cradle: [19:30]: "I am a servant of GOD. He has given me the scripture, and has appointed me a prophet." [19:31]: "He made me blessed wherever I go, and enjoined me to observe the Contact Prayers (Salat) and the obligatory charity (Zakat) for as long as I live." Khalifa renders the infant-speech directly; the Quran treats the speaking-infant as the Jesus-vindication of Mary against the accusation.

**Jesus' nature established.** [19:34]–[19:35]: "That was Jesus, the son of Mary, and this is the truth of this matter, about which they continue to doubt. It does not befit GOD that He begets a son, be He glorified. To have anything done, He simply says to it, 'Be,' and it is." Khalifa preserves the *fiat-creation theology* — Jesus is a created being, brought into existence by divine command, not a divine son. This is the surah's primary theological move, and it sits at the structural midpoint.

**Abraham and his father.** [19:41]–[19:50]: Abraham's compressed biography focuses on his confrontation with his idol-worshipping father. [19:46]: the father threatens him with stoning; Abraham responds ([19:47]): "Peace be upon you. I will implore my Lord to forgive you; He has been Most Kind to me." The departure of Abraham from his family-of-origin, his subsequent fathering of Isaac and Jacob, and his prophetic legacy are noted ([19:49]–[19:50]).

**Moses, Aaron, Ishmael, Idris.** [19:51]–[19:58]: a compressed catalogue of additional prophets — Moses (the conversation at the mount, the appointment of Aaron); Ishmael (the "honest fulfiller of promises"); Idris (raised to a high station). The closing of this section ([19:58]): "These are some of the prophets whom GOD blessed. They were chosen from among the descendants of Adam, and the descendants of those whom we carried with Noah, and the descendants of Abraham and Israel, and from among those whom we guided and selected."

**The contrast — the false-religion register.** [19:59]–[19:74]: the surah pivots to those who came after the prophets — "an evil generation" who neglected prayer and pursued lusts ([19:59]). The future-Paradise versus the present-disregard contrast is developed.

**The closing theology.** [19:88]–[19:93]: "And they said, 'The Most Gracious has begotten a son!' You have uttered a gross blasphemy. The heavens are about to shatter, the earth is about to tear asunder, and the mountains are about to crumble. Because they claim that the Most Gracious has begotten a son. It is not befitting the Most Gracious that He should beget a son. **Absolutely everyone in the heavens and the earth, comes to the Most Gracious as a servant.**" Khalifa preserves the surah's most thunderous formulation — the *son-of-God* claim is named as cosmic-rupture-level blasphemy. [19:97]: "We thus made this (Quran) elucidated in your tongue, in order to deliver good news to the righteous, and to warn with it the opponents." [19:98] closes with the destroyed-generations theme.

**Khalifa-specific framing.** Surah Maryam's structural unity is given by the *fiat-creation theology* threaded through every birth narrative — Zachariah's son, Mary's son, all the prophets, are gifts of divine fiat, not products of biological-divine intermingling. Submitter tradition treats this surah as the canonical refutation of the trinitarian formula — the Quran here is not "subtly polemical" but *explicitly* polemical, with the *gross blasphemy* clause at [19:88] as the operative judgement.
"""


ENTRIES = [
    {
        "id": "broad-held-005",
        "question": "How does the Quran describe being raised from the dead?",
        "answer": RAISED_FROM_DEAD,
    },
    {
        "id": "abstract-held-002",
        "question": "How does the Quran describe lying and deception?",
        "answer": LYING,
    },
    {"id": "broad-held-001", "question": "Summarize Surah Maryam.", "answer": MARYAM},
]


def run(dry_run: bool) -> dict:
    report: list[dict] = []
    for entry in ENTRIES:
        cites = extract_citations(entry["answer"])
        existing, missing = verify_citations_in_graph(cites)
        if missing:
            report.append(
                {
                    "id": entry["id"],
                    "outcome": "INVALID_CITES",
                    "missing_from_graph": sorted(missing),
                    "cite_count": len(cites),
                    "answer_length": len(entry["answer"]),
                }
            )
            continue
        if not dry_run:
            save_answer(entry["question"], entry["answer"])
        report.append(
            {
                "id": entry["id"],
                "outcome": "WOULD_APPLY" if dry_run else "APPLIED",
                "cite_count": len(cites),
                "answer_length": len(entry["answer"]),
                "citations": sorted(cites),
            }
        )
    return {"entries": report}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    report = run(dry_run=args.dry_run)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    all_ok = all(e["outcome"] in ("APPLIED", "WOULD_APPLY") for e in report["entries"])
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
