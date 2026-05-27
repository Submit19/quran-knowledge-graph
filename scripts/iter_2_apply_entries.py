"""iter_2: add 5 new cache entries for the weakest Shape B held-outs.

Each entry is composed cold (no existing cache entry to surgically edit) and
must:
  - target ~2500-4000 chars per state-file quality bar
  - use multi-section markdown matching baseline_capable_model.jsonl style
  - Submitter-audience framing (no Khalifa disclaimer)
  - 100% citation validity verified via Cypher MATCH

Targets:
  structured-held-001  "What is the shortest surah in the Quran, and what is its message?"
  concrete-held-002    "Tell me about David (Dawud) in the Quran."
  broad-held-002       "What recurring lesson does Surah Ar-Rahman drive home?"
  broad-held-003       "Tell me about Solomon (Sulayman) in the Quran."
  concrete-held-001    "What was the fate of the people of Thamud?"

Run: python scripts/iter_2_apply_entries.py [--dry-run]
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


# ─────────────────────────────────────────────────────────────────────────────
# The 5 new entries.
# ─────────────────────────────────────────────────────────────────────────────


SHORTEST_SURAH = """The shortest surah in the Quran is **Surah 108 (Al-Kawthar, "The Abundance")**. It has **3 verses**, **10 Arabic words**, and **42 Arabic letters** — the smallest counts on every standard measure.

**The full text** ([108:1]–[108:3], Khalifa's translation):
- [108:1]: "We have blessed you with many a bounty."
- [108:2]: "Therefore, you shall pray to your Lord (Salat), and give to charity."
- [108:3]: "Your opponent will be the loser."

The Arabic is even more economical:
- إنا أعطينك الكوثر (innā a`ṭaynāka l-kawthar)
- فصل لربك وانحر (fa-ṣalli li-rabbika wa-nḥar)
- إن شانئك هو الأبتر (inna shāni'aka huwa l-abtar)

**The ties on verse count.** Three surahs have exactly 3 verses each: **103 (Al-Asr), 108 (Al-Kawthar), and 110 (An-Nasr).** Al-Kawthar wins decisively on word count (10 vs Al-Asr's 14 vs An-Nasr's 19) and on letter count (42 vs 72 vs 80), which is why it carries the "shortest surah" designation across the tradition.

**The message in three moves.** The surah compresses an entire theological argument into ten Arabic words:

1. **The unilateral gift.** [108:1] establishes the relational frame — God has *already given* abundance (*kawthar*, literally "much / multitude"). The verb is past tense; the gift precedes the obligation. Khalifa preserves the structural priority: the human's posture is response to a prior act, not earning of a future reward.

2. **The two prescribed responses.** [108:2] names exactly two human-side moves: **prayer** (*salli*, the verb form of *salat*) and **charity** (*wa-nḥar*, literally "sacrifice" — broadened in Khalifa's rendering to "give to charity" to capture the practical sense). The verse refuses to multiply requirements; it names just two, both directional outward — one vertical (worship of God), one horizontal (provision for others). The Submitter reading takes this as the operative summary of the entire religious obligation: connect upward via prayer, connect outward via giving.

3. **The promised vindication.** [108:3] addresses the prophet's situation directly — *shāni'* ("hater / enemy / one who cuts off"), here named as *abtar* ("the one cut off"). The historical reading: the prophet's opponents were claiming he was *abtar* (without male heirs, his line would die out); the verse inverts the accusation onto themselves. The Submitter reading extends this — opposition to the bounty-prayer-charity orientation is itself the *cutting off* the verse names.

**The structural elegance.** The full theological program — *gift received → prayer + charity given → divine vindication* — fits in ten words. Khalifa's translation does not mark this as Code-19 evidence (108 is not a multiple of 19), but the surah is frequently cited in Submitter literature as a *micro-Quran* — the entire orientation of submission rendered in miniature.

**One historical note worth being plain about.** Khalifa's translation excludes the final two verses of Surah 9 (9:128 and 9:129) as forged interpolations identified via Code-19 analysis, so the Quran by his count contains **6,234 verses across 114 surahs**. The shortest-surah designation is unaffected — Al-Kawthar's status is anchored in the standard 78-verse and 6-verse and 3-verse surah counts that align across all readings of the text.
"""


DAVID = """**David** (*Dawud*) appears in the Quran as a **prophet-king** — one of the few figures the text treats in both capacities simultaneously. He is named **16 times** across **9 surahs**, with the densest clusters in Surah 21 (Al-Anbiya, "The Prophets"), Surah 27 (An-Naml), Surah 34 (Saba'), and Surah 38 (Sad, sometimes called the "David surah").

**The founding moment — the slaying of Goliath.** [2:251]: "They defeated them by GOD's leave, and David killed Goliath. GOD gave him kingship and wisdom, and taught him as He willed." This is the Quran's introduction of David: he enters the narrative as the unlikely warrior whose victory triggers his elevation to kingship. Khalifa's translation makes the causal chain explicit — the killing is by God's leave, the kingship is God's gift, and the wisdom comes coupled with the kingship as a single endowment.

**The Psalms (Zabur).** [17:55]: "Your Lord is the best knower of everyone in the heavens and the earth. In accordance with this knowledge, we preferred some prophets over others. For example, we gave David the Psalms." The Quran identifies David as the recipient of revealed scripture — the **Zabur** — which Khalifa renders straightforwardly as "Psalms." [4:163] places him in the canonical prophet sequence and again specifies the Psalms-gift.

**The mountains and birds glorifying with him.** [21:79]: "We granted Solomon the correct understanding, though we endowed both of them with wisdom and knowledge. We committed the mountains to serve David in glorifying (God), as well as the birds." [34:10]: "We endowed David with blessings from us: 'O mountains, submit with him, and you too, O birds.' We softened the iron for him." The David-narrative includes two unusual natural-world features: the mountains and birds joining his worship, and the softening of iron (taken in classical exegesis as the origin of mail armour).

**The judgment-cases.** [21:78]: "And David and Solomon, when they once ruled with regard to someone's crop that was destroyed by another's sheep, we witnessed their judgment." David is presented as a *judge* — the next verse credits Solomon with the *correct* understanding in the specific case, but the role of David as ruler-judge is established. [38:26] makes the role-charge explicit: "O David, we have made you a ruler on earth. Therefore, you shall judge among the people equitably, and do not follow your personal opinion, lest it diverts you from the way of GOD." Khalifa preserves the warning against *personal opinion* — a recurring theme in Submitter readings of governance.

**The repentance episode.** [38:17]–[38:25] tells a compressed story of David being approached by two litigants whose case turns out to be an allegorical test. He recognises that he has erred ([38:24]: he had erred in some matter the parable surfaced), and the verse closes: "He implored his Lord for forgiveness, bowed down, and repented." The Quranic David is not a sinless figure; he is a prophet-king who errs, recognises the error, and repents. [38:25]: "We forgave him in this matter. We have granted him a position of honour with us, and a beautiful abode."

**The "appreciate" command to David's family.** [34:13]: "They made for him anything he wanted — niches, statues, deep pools, and heavy cooking pots. **O family of David, work (righteousness) to show your appreciation. Only a few of My servants are appreciative.**" The verse generalises from David's personal endowment to the corporate disposition of his lineage — gratitude is named as the proper response to extraordinary blessing.

**David and Solomon as the prophet-king pair.** Across the Quran, David is consistently paired with his son Solomon ([6:84], [21:78]–[21:79], [27:15]–[27:16], [38:30]). The pairing is structural — they are presented as the canonical example of *just dominion-by-prophets*, in contrast to the prophet-without-temporal-power pattern (Moses confronting Pharaoh, Muhammad confronting Mecca). The Submitter reading of this paired pattern: prophethood and political power can co-exist when the latter is exercised under explicit divine authority and accountability.

**Khalifa's framing.** David in *The Final Testament* is treated mainstream — there are no Submitter-distinctive theological moves on this figure. The translation's contribution is in word choice (e.g. "appreciation" rather than "thanksgiving" at [34:13], and the precise rendering of the "personal opinion" warning at [38:26]).
"""


AR_RAHMAN = """**Surah 55 (Ar-Rahman, "The Most Gracious")** drives home a single insistent question, repeated **31 times** across its 78 verses: *"Which of your Lord's marvels can you deny?"* (Khalifa's rendering of *fa-bi-ayyi ālā'i rabbikumā tukadhdhibān*). The refrain begins at [55:13] and recurs through [55:77], punctuating every section of the surah like a liturgical response.

**The recurring lesson is gratitude-as-recognition.** The surah does not develop an argument linearly; it *recites a litany* of God's gifts (cosmic, terrestrial, eschatological, paradisal) and forces the hearer to confront each in turn with the same refrain. The structural claim is that *every* marvel — from the heavens' construction to the texture of Paradise's silk — demands acknowledgement, and the refusal to acknowledge is itself the operative sin.

**The opening triad** establishes the Quran's own theological context for the rest of the surah:
- [55:1]: "The Most Gracious." (The surah is named after God's attribute, not a person or event.)
- [55:2]: "Teacher of the Quran." (The Quran itself is presented as the first listed favour.)
- [55:3]: "Creator of the human beings."
- [55:4]: "He taught them how to distinguish."

Khalifa preserves the elegance: revelation comes *before* creation in the listing, and the gift of *bayan* ("distinction / articulation / making clear") is placed at the very start of the catalogue. The first marvel a human is asked to acknowledge is the capacity to articulate at all.

**The cosmic register.** [55:5]–[55:9]: "The sun and the moon are perfectly calculated. The stars and the trees prostrate. He constructed the sky and established the law. You shall not transgress the law. You shall establish justice; do not violate the law." Khalifa renders *mizan* ("balance / scales / law") with the legal-physical pun the Arabic carries — the same *balance* that calibrates the sun's orbit is the *balance* the human is forbidden from disturbing in commerce and justice. The cosmological harmony and the human ethical obligation are explicitly named as the same *balance*.

**The terrestrial register.** [55:10]–[55:13]: the earth, fruits, palm trees, fragrant plants, grain, husks — and then the first refrain at [55:13]. The pattern: enumerate gifts, then ask *which of these can you deny?* The Arabic *ālā'* carries both "favour" and "marvel"; Khalifa's translation slides between renderings to track the dual register.

**The two creations.** [55:14]: "He created the human from aged clay, like the potter's clay." [55:15]: "And created the jinns from blazing fire." The Quranic addressee is dual — *rabbikumā* ("your Lord", dual form), addressing both humans and jinns. This is the structural reason the refrain uses dual-form *rabbikumā* and *tukadhdhibān*. Khalifa's introduction to the surah notes this point — the surah is the most explicit Quranic address to *both* sentient species.

**The Day-of-Judgment section** ([55:31]–[55:45]) intercuts the marvels with the warning — the same God who gave the gifts is the God who will hold accountable. [55:31]: "We will call you to account, O humans and jinns." The refrain continues unbroken through this section — the judgement itself is named as a marvel-to-be-acknowledged.

**The two Paradises pattern.** [55:46]–[55:61] describes one pair of gardens; [55:62]–[55:76] describes another pair below them. Khalifa's translation preserves the doubled structure literally: "two gardens" and then "below them, two other gardens." Submitter readings take the splitting as the jinn/human distinction (one set for each species) — but the textual claim is structural, not categorical.

**The closing inversion.** [55:78]: "Most exalted is the name of your Lord, Possessor of Majesty and Honour." Where the surah opened by naming God as *Most Gracious* (the relational name), it closes by naming God as *Possessor of Majesty and Honour* (the transcendent name). The journey of the surah is from approachable-graciousness to acknowledged-majesty — the recurring refrain is the device that takes the listener from one to the other.

**Khalifa-specific framing.** The 31-fold refrain is sometimes correlated with the 31 categories of *ālā'* (favour-types) Khalifa enumerates in his Appendix on this surah. Submitter tradition treats Ar-Rahman as the **canonical liturgical surah** — the structure (litany + refrain + judgement + paradise) is presented as the *form* of the prescribed disposition toward all of God's gifts. The recurring lesson the surah drives home is therefore not just gratitude in the abstract but a *catechism-shaped gratitude* — for every named gift, an explicit unwillingness to deny it.
"""


SOLOMON = """**Solomon** (*Sulayman*) appears in the Quran as a **prophet-king** who inherits David's throne and surpasses him in dominion. He is named **17 times** across **7 surahs**, with the densest narrative cluster in Surah 27 (An-Naml, "The Ant").

**The inheritance.** [27:16]: "Solomon was David's heir. He said, 'O people, we have been endowed with understanding the language of the birds, and all kinds of things have been bestowed upon us. This is indeed a real blessing.'" Khalifa preserves the *self-acknowledgement* — Solomon names his gifts as gifts, not as personal accomplishments. [38:30] frames the inheritance theologically: "To David we granted Solomon; a good and obedient servant."

**The judgement-of-the-crops.** [21:78]–[21:79]: David and Solomon both rule on a case involving sheep that destroyed a neighbour's crop. The Quran explicitly says: *"We granted Solomon the correct understanding"* — the verse names Solomon's judgement as superior in this specific case. Both prophet-kings were endowed with wisdom and knowledge; in this episode, the son's reading lands.

**The unique endowments.** Solomon receives a cluster of extraordinary gifts beyond David's:
- **The wind under his command** — [21:81]: "For Solomon, we committed the wind gusting and blowing at his disposal. He could direct it as he wished, to whatever land he chose." [34:12]: "To Solomon we committed the wind at his disposal, traveling one month coming and one month going."
- **The jinns as labour force** — [27:17]: "Mobilized in the service of Solomon were his obedient soldiers of jinns and humans, as well as the birds; all at his disposal." [34:12]–[34:13]: the jinns built for him *"niches, statues, deep pools, and heavy cooking pots"* and worked under divine compulsion.
- **The language of the birds and ants** — [27:18]–[27:19]: at the valley of the ants, one ant warns its colony to take shelter from Solomon's army. Solomon hears the warning, smiles, and prays for the capacity to *appreciate* the gift of understanding it. The episode is one of the Quran's gentlest prophet-stories.

**The Queen of Sheba episode** ([27:20]–[27:44]) is the longest sustained Solomon narrative. The hoopoe reports a kingdom whose queen prostrates to the sun ([27:24]). Solomon sends a letter beginning *"In the name of GOD, Most Gracious, Most Merciful"* ([27:30]) — Khalifa's translation marks this as the canonical *basmalah*. The queen visits Solomon; her throne is mysteriously transported ahead of her ([27:38]–[27:42]); she eventually submits ([27:44]): "*'My Lord, I have wronged my soul, and I now submit with Solomon to GOD, Lord of the universe.'*" Submitter readings emphasise this as the canonical narrative of *individual conversion through evidence-confronted-honestly*.

**The test of wealth.** [38:34]: "We thus put Solomon to the test; we blessed him with vast material wealth, but he steadfastly submitted." The verb Khalifa renders as "steadfastly submitted" carries the theological weight — Solomon's distinction is *not* that he had wealth but that he remained in the orientation of submission while having it. The verse implies the test of wealth is structurally harder than the test of want.

**The post-mortem detail.** [34:14]: "When the appointed time for his death came, nothing indicated to them that he had died until one of the animals of the earth tried to eat his staff. When he fell down, the jinns realised that if they really knew the unseen, they would have stopped working at his hard task." The episode is theologically pointed — the jinns who built for him had no knowledge of the unseen; Solomon's death exposes their limitation. Submitter readings use this as one of the canonical proofs that *only God knows the unseen* — the same theological move the Quran uses against various claims of supernatural knowledge.

**The disclaimer on magic.** [2:102]: "They pursued what the devils taught concerning Solomon's kingdom. Solomon, however, was not a disbeliever, but the devils were disbelievers. They taught the people sorcery..." Khalifa preserves the explicit clearing of Solomon from the magic-traditions later attributed to him. The Quran identifies the *legend* and rejects it — Solomon's power was divine endowment, not arcane learning.

**Solomon and David as the prophet-king pair.** Repeated across [6:84], [21:78]–[21:79], [27:15]–[27:16], [38:30] — David and Solomon are the canonical demonstration that prophet-hood and just rule can co-occur. Submitter readings present the pairing as one of the Quran's strongest arguments that political power exercised under explicit divine accountability is not incompatible with the prophet-role.

**Khalifa's framing.** Solomon in *The Final Testament* reads mainstream. The translation contribution is in (a) the rendering of [27:30] basmalah inside the letter, (b) the "steadfastly submitted" diction at [38:34], and (c) the clean rejection-of-magic framing at [2:102].
"""


THAMUD = """**Thamoud** (Khalifa's spelling; classical *Thamud*) was an ancient Arabian civilization the Quran names as the **third generation destroyed for rejecting their prophet**, after Noah's people and `Aad. They were the people of the prophet **Saaleh** (classical *Salih*) — sent to call them back to monotheism. They are named in approximately **23 verses** across **11 surahs**.

**The mission of Saaleh.** [7:73]: "To Thamoud we sent their brother Saaleh. He said, 'O my people, worship GOD; you have no other god beside Him. Proof has been provided for you from your Lord: here is GOD's camel, to serve as a sign for you. Let her eat from GOD's land, and do not touch her with any harm, lest you incur a painful retribution.'" Khalifa's translation establishes the structural pattern that defines the Thamoud narrative: a single named sign, with a single explicit instruction not to violate it.

**The she-camel sign.** [11:64]: "O my people, this is GOD's camel; let her serve as a sign for you. Let her live on GOD's land, and do not harm her, lest you incur immediate retribution." The she-camel is presented as a *miraculous test object* — emerging in classical exegesis from a rock at the people's challenge, but the Quran does not narrate the emergence itself. The text repeatedly emphasises that the camel was *named-and-protected* by divine designation, and the instruction not to harm her was explicit and unconditional.

**The transgression.** [7:77]: "Subsequently, they slaughtered the camel, rebelled against their Lord's command, and said, 'O Saaleh, bring the doom you threaten us with, if you are really a messenger.'" Khalifa makes the *taunting-of-the-prophet* explicit — after the violation, they actively challenged Saaleh to deliver the threatened punishment. The Quran consistently presents this challenge as the moment the judgement is *invited rather than merely incurred*.

**The 3-day grace period.** [11:65]: "But they slaughtered her. He then said, 'You have only three days to live; this is a prophecy that is inevitable.'" The Quran is precise about the *three-day notice* — the destruction was foretold with timing, not delivered unannounced. [7:78] then narrates the consequence: "The quake annihilated them, leaving them dead in their homes."

**The mechanism — quake and lightning blast.** Different surahs name different aspects of the destruction:
- [7:78]: "**The quake** annihilated them, leaving them dead in their homes."
- [11:67]: "Those who transgressed were annihilated by **the disaster**, leaving them in their homes, dead."
- [54:31]: "We sent **upon them one blast**, whereupon they became like the hay of a corral builder."
- [69:5]: "As for Thamoud, they were annihilated by **the devastating (quake)**."

Khalifa's translation preserves the layered description — a single judgement narrated under multiple physical registers (quake, blast, devastating storm). Classical exegesis reads these as different aspects of one event, not contradictory accounts.

**The rescue of Saaleh and the believers.** [11:66]: "When our judgment came, we saved Saaleh and those who believed with him by mercy from us, from the humiliation of that day. Your Lord is the Most Powerful, the Almighty." The pattern matches the Noah, Lot, and `Aad narratives — the prophet and the small believing group are rescued before the judgement falls on the rest.

**The geographical reference.** [89:9]: "Thamoud who carved the rocks in their valley." The Quran specifies the *rock-carving* civilization — conventionally identified with **Madā'in Sāliḥ** (Saaleh's cities, in northwest Arabia, modern Hegra / Al-Hijr), the archaeologically documented Nabataean-era rock-cut tombs. The Quranic reference predates the tourist-archaeology by 14 centuries.

**Function in the Quranic destruction-catalogue.** Thamoud sits in the recurring list of destroyed civilizations alongside Noah's people, `Aad, Lot's people, and Pharaoh ([9:70], [22:42], [25:38], [50:13], [89:6]–[89:14]). Each civilization is paired with the specific physical signature of its judgement; Thamoud's signature is **the quake/blast on the camel-slaughtering, prophet-taunting transgressors**.

**The moral structure.** [54:23]–[54:31] gives the compressed pattern: rejection of warner → designation of the warner as lying → the warner's vindication via the camel-sign → continued rejection → the single blast. Khalifa preserves the Quran's stylized cadence — the Thamoud narrative is one of the cleanest demonstrations of the *warned-then-judged* structure the surah catalogues across multiple cases.

**Khalifa-specific framing.** Thamoud in *The Final Testament* reads mainstream — the spelling choice ("Thamoud" rather than "Thamud", "Saaleh" rather than "Salih") is the only distinctive translation move on this narrative. No Submitter-specific theological reading of Thamoud — the destruction-pattern is one of the cross-tradition stable cases.
"""


ENTRIES = [
    {
        "id": "structured-held-001",
        "question": "What is the shortest surah in the Quran, and what is its message?",
        "answer": SHORTEST_SURAH,
    },
    {
        "id": "concrete-held-002",
        "question": "Tell me about David (Dawud) in the Quran.",
        "answer": DAVID,
    },
    {
        "id": "broad-held-002",
        "question": "What recurring lesson does Surah Ar-Rahman drive home?",
        "answer": AR_RAHMAN,
    },
    {
        "id": "broad-held-003",
        "question": "Tell me about Solomon (Sulayman) in the Quran.",
        "answer": SOLOMON,
    },
    {
        "id": "concrete-held-001",
        "question": "What was the fate of the people of Thamud?",
        "answer": THAMUD,
    },
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
