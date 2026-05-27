"""iter_4 (FINAL): 3 cache entries — taqwa, peace/reconciliation, envy.

Targets the last cluster of weak-coverage Shape B held-outs:
  abstract-held-003  "What place does the fear of God (taqwa) hold in the Quran?"  (sim 0.785)
  abstract-held-005  "How does the Quran describe peace and reconciliation?"       (sim 0.814)
  abstract-held-001  "Where does envy (hasad) appear in the Quranic moral landscape?" (sim 0.837)

All citations Cypher-verified before save.

Per the cache-eval-loop discipline, iter_4 is the LAST iteration regardless
of outcome. The FINAL_REPORT.md follows.
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


TAQWA = """**Taqwa** (تَقْوَى, from the root **و-ق-ي** *w-q-y*, "to guard, protect, shield") is one of the Quran's most-load-bearing virtue-words — Khalifa's translation consistently renders it as **"reverence" / "righteousness"** rather than the older "fear of God" gloss, capturing the protective-orientation sense the Arabic carries. The root family appears in approximately **250 verse-level mentions**; the *taqwa*-derived nominal and verbal forms saturate the text.

**The opening claim.** [2:2]: "This scripture is infallible; a beacon for the righteous." Khalifa renders *li-l-muttaqin* ("for those-who-have-taqwa") as "for the righteous" — and the very second verse of the Quran's longest surah identifies the scripture's *target audience* as the taqwa-possessing. The Quran is self-identified as a guidebook for a specific orientation, not a universal manual; the orientation is named in the second verse.

**The definitional verse.** [2:177]: "Righteousness is not turning your faces towards the east or the west. Righteous are those who believe in GOD, the Last Day, the angels, the scripture, and the prophets; and they give the money, cheerfully, to the relatives, the orphans, the needy, the traveling alien, the beggars, and to free the slaves; and they observe the Contact Prayers (Salat) and give the obligatory charity (Zakat); and they keep their word whenever they make a promise; and they steadfastly persevere in the face of persecution, hardship, and war. These are the truthful; these are the righteous." Khalifa preserves the operational seven-part definition: *taqwa* is named not as an interior state but as a *complete behavioural-belief package* — belief content + financial giving + ritual + integrity + endurance. The verse is one of the Quran's most cited definitional passages.

**The threshold qualifier.** [49:13]: "**The best among you in the sight of GOD is the most righteous.**" Khalifa's translation makes the meritocracy explicit — the Quran rejects ethnic, tribal, and class-based valuations and substitutes *taqwa-degree* as the operative ranking principle. The verse is paired earlier in the same chapter with "We created you from the same male and female" — the levelling clause sets up the *taqwa* hierarchy.

**The protective-orientation gloss.** [2:21]: "O people, worship only your Lord — the One who created you and those before you — that you may be saved" (Khalifa's translation of *la-`allakum tattaqun* — literally "that you may guard yourselves"). The root-meaning is preserved: the *muttaqi* is one who *guards against* — guards the soul, guards relationships, guards the structure of obedience. The protective stance, not the affective fear, is the operative metaphor.

**The taqwa-equivalence with righteousness in food/dress.** [5:96]: "All fish of the sea are made lawful for you to eat. During pilgrimage, this may provide for you during your journey. You shall not hunt throughout the pilgrimage. You shall reverence GOD, before whom you will be summoned." [7:26]: "O children of Adam, we have provided you with garments to cover your bodies, as well as for luxury. But the best garment is the garment of righteousness." Khalifa's translation of *libas at-taqwa* as *garment of righteousness* captures the metaphor — *taqwa* is depicted as worn, as enclosing, as protective.

**The path-marker function.** [3:133]: "You should eagerly race towards forgiveness from your Lord and a Paradise whose width encompasses the heavens and the earth; it awaits the righteous." [3:134]: the righteous are defined as those "who give to charity during the good times, as well as the bad times. They are suppressors of anger, and pardoners of the people. GOD loves the charitable." The verses sequence belief-conduct-Paradise into a clean three-step chain anchored in *taqwa*.

**The fasting-and-taqwa link.** [2:183]: "O you who believe, fasting is decreed for you, as it was decreed for those before you, that you may attain salvation" (Khalifa's *la-`allakum tattaqun* — "that you may become righteous / guard yourselves"). The ritual of fasting is given an explicit instrumental purpose: it cultivates *taqwa*. Khalifa's translation makes the instrumental relation explicit; the ritual is means, the orientation is end.

**The taqwa-of-prophets formula.** [3:102]: "O you who believe, you shall observe GOD as He should be observed, and do not die except as Submitters" — Khalifa renders *ittaqu-Llaha haqqa tuqatih* as "observe GOD as He should be observed," capturing the *full-measure-of-taqwa* formulation. The verse is one of the highest standards the Quran sets — perfect-measure *taqwa* is the prophet-equivalent disposition.

**The provision-promise.** [65:2]–[65:3]: "Anyone who reverences GOD, He will create an exit for him, and will provide for him whence he never expected. Anyone who trusts in GOD, He suffices him." Khalifa preserves the unconditional promise. *Taqwa* is presented not just as obligation but as *operative cause* of unexpected provision and crisis-escape — the verse is one of the most-cited Submitter "trust in God" anchor passages.

**The contrasts.** The Quran consistently pairs *taqwa* against *fujur* (debauchery, [91:8]: "Then showed it its wickedness, and its righteousness") and against *ghaflah* (heedlessness). The opposite of *taqwa* is not "evil intent" but *unguardedness* — the failure to maintain the protective stance. This linguistic move is important: *taqwa* is not depicted as moral high-effort heroism but as default-careful-attention.

**Khalifa-specific framing.** His translation systematically replaces "fear of God" with "reverence" / "righteousness", capturing the protective-orientation sense of the root rather than the affective-fear sense the older translations leaned on. Submitter tradition treats *taqwa* as the *single most operative virtue* in the Quranic moral vocabulary — the disposition that, if cultivated, automatically generates the other virtues (charity, truthfulness, patience, etc.) as derivatives. The corpus's repeated *"the best among you is the most righteous"* formulations make this prioritization explicit.
"""


PEACE = """The Quran develops **peace and reconciliation** (*salam, sulh*) as both a divine attribute and a human obligation. The root **س-ل-م** (*s-l-m*, "be whole, be at peace, submit") supplies the broader vocabulary — including *Islam* itself (literally "submission-into-peace"), *salam* ("peace"), and the divine name *As-Salam* ("The Source of Peace"). The corpus treats peace not as conflict-absence merely but as the *structural orientation* the religion is named for.

**As-Salam as divine name.** [59:23]: "He is the One GOD; there is no other god beside Him. The King, the Most Sacred, the Peace, the Faithful, the Supreme..." Khalifa preserves *As-Salam* in the canonical "Beautiful Names" list at the end of Surah Al-Hashr. God is named *Peace* — the relational endpoint to which the believer orients.

**Paradise as the Abode of Peace.** [10:25]: "GOD invites to the abode of peace, and guides whoever wills (to be guided) in a straight path." [6:127]: "They have deserved the abode of peace at their Lord; He is their Lord and Master, as a reward for their works." Khalifa's *dar al-salam* ("abode of peace") rendering preserves the eschatological frame — Paradise itself is structurally named after peace.

**The greeting of Paradise.** [14:23]: "...the believers and the righteous have gardens with flowing streams, abiding therein forever in accordance with the will of their Lord. Their greeting therein is: 'Peace.'" [36:58]: "'Peace' is the proclamation from a Most Merciful Lord." Khalifa preserves the *salam*-greeting as the ambient verbal posture of the saved.

**Peace among believers in this life.** [4:114]: "There is nothing good about their private conferences, except for those who advocate charity, or righteous works, or making peace among the people. Anyone who does this, in response to GOD's teachings, we will grant him a great recompense." Khalifa makes the *sulh-bayn-an-nas* ("peace between the people") clause its own virtue. Peacemaking is named as one of three private-conference exemptions.

**Marital reconciliation.** [2:226]: "Those who intend to divorce their wives shall wait four months (cooling off); if they change their minds and reconcile, then GOD is Forgiver, Merciful." [4:128]: "If a woman senses oppression or desertion from her husband, the couple shall try to reconcile their differences, for conciliation is best for them." [4:35]: "If a couple fears separation, you shall appoint an arbitrator from his family and an arbitrator from her family; if they decide to reconcile, GOD will help them get together." Khalifa renders all three with *reconcile* explicit — the Quran institutionalizes structured-mediation as the prescribed first response to marital crisis.

**Reconciliation among believers generally.** [49:9]: "If two groups of believers fought with each other, you shall reconcile them. If one group aggresses against the other, you shall fight the aggressing group until they submit to GOD's command. Once they submit, you shall reconcile the two groups equitably. You shall maintain justice; GOD loves those who are just." [49:10]: "**The believers are members of one family; you shall make peace among your family members and reverence GOD, that you may attain mercy.**" Khalifa preserves the structural claim — believers are *family* and reconciliation is a *family-obligation*, not a discretionary nicety.

**Peace as default state in inter-group relations.** [4:90]–[4:91]: "Exempted are those who join people with whom you have signed a peace treaty, and those who come to you wishing not to fight you, nor fight their relatives. Had GOD willed, He could have permitted them to fight against you. Therefore, if they leave you alone, refrain from fighting them, and offer them peace, GOD gives you no excuse to fight them." [4:94]: "Do not say to one who offers you peace, 'You are not a believer,' seeking the spoils of this world." Khalifa renders the *peace-as-default* clauses literally — the burden of proof is on the war-pursuer, not the peace-seeker.

**The general principle at [8:61].** "**If they resort to peace, so shall you, and put your trust in GOD.** He is the Hearer, the Omniscient." Khalifa preserves the unilateral acceptance: *if* the other side resorts to peace, the believer's response is non-conditional acceptance, with trust-in-God replacing the strategic-doubt that would otherwise reject the offer.

**Heart-reconciliation as divine work.** [3:103]: "You shall hold fast to the rope of GOD, all of you, and do not be divided. Recall GOD's blessings upon you — you used to be enemies and He reconciled your hearts. By His grace, you became brethren." [8:63]: "He has reconciled their hearts. If you spent all the money on earth, you could not reconcile their hearts. But GOD did reconcile them." Khalifa preserves the theological claim — interpersonal-reconciliation at scale is *divine action*, not purely human effort.

**Peace with parents specifically.** [19:14]: of John (Yahya): "He honored his parents, and was never a disobedient tyrant." [19:32]: of Jesus from the cradle: "I am to honor my mother; He did not make me a disobedient tyrant." Family-peace and parent-honour are paired as one of the operational expressions of *taqwa*.

**The peace-departure formula.** [19:47] (Abraham to his father): "**Peace be upon you.** I will implore my Lord to forgive you; He has been Most Kind to me." Khalifa preserves the Quran's depicted *salam-on-departure* — even in the rupture from a father who threatens stoning, Abraham's parting word is *salam*. The verse functions as the operational example: peace can be offered unilaterally even where it cannot be received.

**The closing surah's peace-framing.** [97:5] (Surah Al-Qadr, Night of Power): "Peaceful it is until the advent of the dawn." Khalifa renders *salamun hiya* literally — the night of revelation is itself characterized as peaceful, suggesting the revelation-event and the peace-state are linked at the structural level.

**Khalifa-specific framing.** His translation foregrounds [49:9]–[49:10] (the believers-as-family reconciliation duty) and [8:61] (unilateral acceptance of peace offers) as the operative inter-group peace doctrine, and [4:35], [4:128], [2:226] as the marital-reconciliation institutional framework. Submitter tradition treats *salam* as the Quran's *master orientation* — Islam is etymologically named for it, Paradise is structurally named for it, and the prescribed dispositions (toward enemies who offer peace, toward spouses, toward feuding believers) are all peace-oriented as default. The Quran's reading is that conflict is exceptional, peace is the structural norm.
"""


ENVY = """**Envy** (*hasad*, root **ح-س-د** *h-s-d*) appears in the Quran as a structural moral failure rather than a fleeting emotion — the corpus names it in approximately **5 explicit verse-level mentions** of the root, plus a denser set of *jealousy / resentment* (often translated from *baghy* — حسد-adjacent — or related diction) that totals around **15 verses**. The doctrine is consistent across these: envy is the *operative motive* of disbelievers' opposition to the prophets, and it is the *internal-state remedied* in Paradise.

**The seek-refuge anchor verse.** [113:5]: "**From the evils of the envious when they envy.**" The penultimate surah of the Quran (Al-Falaq, "The Daybreak") includes *the envious one's envy* in its short list of evils-to-seek-refuge-from. Khalifa preserves the Arabic structure: *hasidin idha hasad* — "the envier when he envies" — indicating that envy is dangerous specifically *in its expressed action*, not in latent feeling. The verse names envy alongside (a) the evils of darkness, (b) the evils of magic-workers, and (c) the evils of whisperers — placing it in the most-final-warning theological category.

**The diagnostic of religious resentment.** [2:109]: "Many followers of the scripture would rather see you revert to disbelief, now that you have believed. This is due to **jealousy** on their part, after the truth has become evident to them. You shall pardon them and leave them alone, until GOD issues His judgment." Khalifa renders *hasadan min `indi anfusihim* ("jealousy from their own selves") as making the source-attribution explicit — the resistance to truth is named as self-sourced envy, not principled doubt. The corrective is striking: *pardon them and leave them alone*. Envy from others is met with non-engagement, not retaliation.

**The doctrinal-dispute genealogy.** [45:17]: "We have given them herein clear commandments. Ironically, they did not dispute this until the knowledge had come to them. This is due to **jealousy** on their part. Surely, your Lord will judge them on the Day of Resurrection regarding everything they have disputed." [42:14]: "Ironically, they broke up into sects only after the knowledge had come to them, due to **jealousy and resentment** among themselves." Khalifa's translation makes the historical claim explicit: religious sectarianism is named as *envy-driven*, not as honest disagreement. The Quran offers an unflattering reading of dispute-history — clear teaching exists, the dispute-after-the-teaching is sourced from envy among scholars.

**The Joseph paradigm.** Surah 12 (Yusuf) is the Quran's longest-sustained envy-narrative — Joseph's brothers conspire against him because of their father's preference ([12:8]: "We are a tribe yet our father preferred him over us. Our father has gone astray"). The envy drives the whole sequence: the well, the slavery, the false-shirt-with-blood. Khalifa preserves the moral arc: at [12:91] the brothers eventually confess, "By GOD, GOD has truly preferred you over us. We were definitely wrong." Joseph's response ([12:92]): "There is no blame upon you today. May GOD forgive you. Of all the merciful ones, He is the Most Merciful." The Quranic prescription for the envy-target is *forgiveness-and-continued-relation*, not separation.

**Envy at the messenger-cousin level.** [15:88]: "Do not be jealous of what we bestowed upon the other (messengers), and do not be saddened (by the disbelievers), and lower your wing for the believers." Khalifa addresses the directive to the Prophet himself — even at the messenger level, the corrective for cross-messenger jealousy is named. The verse implies that envy can arise toward *peers in religious endowment*, not just toward unbelievers.

**Envy at the inheritance level.** [4:54]: "Are they envious of the people because GOD has showered them with His blessings? We have given Abraham's family the scripture, and wisdom; we granted them a great authority." Khalifa preserves the rhetorical question — envy-of-divine-favour is named as an irrational stance, since the favour is at God's discretion, not the envier's.

**Removal of envy as feature of Paradise.** [7:43]: "**We will remove all jealousy from their hearts.** Rivers will flow beneath them, and they will say, 'GOD be praised for guiding us. We could not possibly be guided, if it were not that GOD has guided us.'" [15:47]: "We remove all jealousy from their hearts. Like one family, they will be on adjacent furnishings." Khalifa preserves the eschatological move: envy is named as one of the operative *barriers to communion* that Paradise specifically dissolves. The implication is profound — the Quran identifies envy as *the obstacle to brotherhood*, and Paradise's defining feature includes its surgical removal.

**The "do not desire what is denied" doctrine.** [4:32]: "**You shall not covet** the qualities bestowed upon each other by GOD; the men enjoy certain qualities, and the women enjoy certain qualities. You may implore GOD to shower you with His grace. GOD is fully aware of all things." Khalifa renders *la tatamannaw* ("do not desire / wish") as "do not covet" — naming the specific cognitive move (coveting-what-was-not-given-to-you) as the operative envy-precursor. The corrective: *ask God for grace directly*, rather than envying what others received.

**Doctrinal synthesis.** Five recurring claims emerge across the *hasad* texts:
1. **Envy is the operative motive of religious opposition** — disbelievers oppose the prophets because of envy, not because of honest doubt.
2. **Envy is also a within-group risk** — sects form within the same religious community via envy among the learned.
3. **Envy is sourced from the envier**, not from the target's actions — the corrective addresses the envier's inner state, not the target's circumstance.
4. **Envy is something to seek refuge from**, as a category of evil meriting protective prayer.
5. **Envy is one of the features Paradise specifically removes**, by structural intervention.

**Khalifa-specific framing.** His translation foregrounds [113:5] (seek-refuge anchor), [7:43] / [15:47] (Paradise removes envy), and [4:32] (do-not-covet) as the operative envy-doctrine. Submitter tradition reads the corpus as identifying envy not primarily as a personal moral failing but as *the structural sin of those-who-have-the-scripture-but-resist-correction* — the failure mode the Quran most worries about for the religiously-instructed. The seek-refuge prescription is the prophylactic; forgiveness-without-engagement is the response when one is the target.
"""


ENTRIES = [
    {
        "id": "abstract-held-003",
        "question": "What place does the fear of God (taqwa) hold in the Quran?",
        "answer": TAQWA,
    },
    {
        "id": "abstract-held-005",
        "question": "How does the Quran describe peace and reconciliation?",
        "answer": PEACE,
    },
    {
        "id": "abstract-held-001",
        "question": "Where does envy (hasad) appear in the Quranic moral landscape?",
        "answer": ENVY,
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
