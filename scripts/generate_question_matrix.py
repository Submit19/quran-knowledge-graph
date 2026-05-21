"""Generate the 500-question expansion matrix from the concept inventory.

Phase 2 of cache-content-expansion 2026-05-21. Reads
data/research/concept_inventory_2026-05-21.json and emits
data/eval/v2/expansion_questions_2026-05-21.json with 500
prioritized questions + ~250 reserves across 10 categories.

Prioritization: gap_weight * 2 + realistic_weight * 1, then
diversity dedupe (no more than 3 questions per single root/concept).
"""

import json
import re
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INVENTORY = REPO_ROOT / "data" / "research" / "concept_inventory_2026-05-21.json"
OUT = REPO_ROOT / "data" / "eval" / "v2" / "expansion_questions_2026-05-21.json"
CACHE = REPO_ROOT / "data" / "answer_cache.json"


def load_existing_questions() -> set[str]:
    """Return a set of normalized existing-cache questions for dedupe."""
    data = json.load(CACHE.open(encoding="utf-8"))
    seen = set()
    for r in data:
        q = (r.get("question") or "").strip().lower()
        seen.add(re.sub(r"[^\w\s]", "", q))
    return seen


def norm(q: str) -> str:
    return re.sub(r"[^\w\s]", "", q.strip().lower())


# ---------- Hand-authored question templates ----------
# Each generator returns: list of {category, question, target_themes, target_verses, priority_score, gap_addressed}

PROPHET_QUESTION_TEMPLATES = [
    ("story", "Tell me the story of {prophet} as the Quran narrates it."),
    ("lesson", "What lessons does the Quran draw from the story of {prophet}?"),
    ("people", "Who were the people of {prophet} and what was their fate?"),
    (
        "relationship",
        "How is {prophet}'s relationship with God portrayed in the Quran?",
    ),
]

# Curated theme questions (cat 1: theological)
THEOLOGICAL = [
    (
        "Divine attributes: mercy",
        "How does the Quran describe God's mercy (Ar-Rahman, Ar-Rahim)?",
        ["mercy", "rahmah", "rahman"],
        [],
    ),
    (
        "Divine attributes: knowledge",
        "What does the Quran say about God's knowledge being all-encompassing?",
        ["knowledge", "ilm", "alim"],
        [],
    ),
    (
        "Divine attributes: justice",
        "How does the Quran portray God's justice (`adl)?",
        ["justice", "adl", "qist"],
        [],
    ),
    (
        "Divine attributes: power",
        "What does the Quran teach about God's omnipotence (qudrah)?",
        ["omnipotent", "qadeer", "power"],
        [],
    ),
    (
        "Divine attributes: wisdom",
        "How is God's wisdom (hikmah) described in the Quran?",
        ["wisdom", "hikmah"],
        [],
    ),
    (
        "Tawhid: definition",
        "How does the Quran define the absolute oneness of God (tawhid)?",
        ["tawhid", "ahad", "wahid"],
        ["112:1", "112:2", "112:3", "112:4"],
    ),
    (
        "Shirk: forms",
        "What is shirk in the Quran and what are its forms?",
        ["shirk", "associate"],
        [],
    ),
    (
        "Names of God",
        "What are the most beautiful names of God (asma al-husna) in the Quran?",
        ["names", "asma"],
        ["7:180", "20:8", "17:110", "59:24"],
    ),
    (
        "Revelation: chain",
        "How does the Quran describe the chain of revelation from earlier scriptures?",
        ["revelation", "scripture", "torah", "gospel"],
        [],
    ),
    (
        "Revelation: preservation",
        "What does the Quran say about its own preservation?",
        ["preservation", "guard"],
        ["15:9", "85:21", "85:22"],
    ),
    (
        "Eschatology: barzakh",
        "What is the barzakh in the Quran?",
        ["barzakh", "intermediate state"],
        ["23:100"],
    ),
    (
        "Eschatology: trumpet",
        "How does the Quran describe the trumpet (sur) of the Day of Resurrection?",
        ["trumpet", "sur"],
        ["39:68", "69:13", "78:18"],
    ),
    (
        "Eschatology: scales",
        "What does the Quran say about the scales (mizan) of deeds?",
        ["scales", "mizan", "weight"],
        ["7:8", "7:9", "23:102", "23:103"],
    ),
    (
        "Eschatology: bridge",
        "Does the Quran mention the bridge over Hell (sirat)?",
        ["sirat", "path", "bridge"],
        ["1:6", "37:23"],
    ),
    (
        "Eschatology: angel of death",
        "What does the Quran say about the angel of death?",
        ["death", "angel"],
        ["32:11"],
    ),
    (
        "Worship: salat",
        "How is the Contact Prayer (Salat) structured in the Quran?",
        ["salat", "prayer"],
        [],
    ),
    (
        "Worship: zakat detail",
        "What does the Quran specify about zakat — who pays, who receives?",
        ["zakat", "alms"],
        ["9:60", "2:177"],
    ),
    (
        "Worship: fasting",
        "How does the Quran describe the practice of fasting?",
        ["fasting", "siyam", "sawm"],
        ["2:183", "2:184", "2:185", "2:187"],
    ),
    (
        "Worship: hajj",
        "What does the Quran say about the rites of hajj?",
        ["hajj", "pilgrimage"],
        ["2:196", "2:197", "3:96", "3:97", "22:27"],
    ),
    (
        "Divine attribute: forgiveness",
        "How does the Quran describe God as the Forgiver (Al-Ghafur, Al-Ghaffar)?",
        ["forgiver", "ghafur", "ghafir"],
        [],
    ),
    (
        "Divine: lordship",
        "What does the Quran mean by God as Rabb (Lord, Sustainer)?",
        ["rabb", "lord"],
        [],
    ),
    (
        "Predestination",
        "How does the Quran balance predestination (qadar) and human responsibility?",
        ["qadar", "qada", "destiny"],
        [],
    ),
    (
        "Light verse",
        "Explain the Light Verse (24:35) — what does it teach about God's light?",
        ["light", "nur"],
        ["24:35", "24:36"],
    ),
    (
        "Throne verse",
        "Explain Ayat al-Kursi (2:255) verse by verse.",
        ["throne", "kursi"],
        ["2:255", "2:256"],
    ),
    (
        "God's nearness",
        "What does the Quran say about God's nearness (closer than the jugular vein)?",
        ["nearness", "close", "jugular"],
        ["50:16", "2:186"],
    ),
    (
        "Divine speech",
        "How does the Quran describe God speaking — direct, behind a veil, through a messenger?",
        ["speech", "kalam"],
        ["42:51"],
    ),
    (
        "Honour to humans",
        "What honour does God bestow on humans according to the Quran?",
        ["honour", "karam", "khalifa"],
        ["17:70", "2:30"],
    ),
    (
        "Heart and seal",
        "What does the Quran mean by 'God sealing the hearts'?",
        ["heart", "seal", "khatm"],
        ["2:7", "16:108", "47:24"],
    ),
    (
        "Divine will: 'Be'",
        "What does the Quran teach about God saying 'Be' (kun)?",
        ["kun", "be", "creation"],
        ["2:117", "3:47", "3:59", "6:73", "16:40", "19:35", "36:82", "40:68"],
    ),
    (
        "Mercy precedence",
        "How does the Quran teach that God's mercy precedes His wrath?",
        ["mercy", "wrath"],
        ["6:12", "6:54", "7:156"],
    ),
    (
        "Divine attributes: First and Last",
        "How does the Quran describe God as First, Last, Inner, Outer (57:3)?",
        ["first", "last"],
        ["57:3", "57:4"],
    ),
    (
        "Anthropomorphism",
        "Does the Quran use anthropomorphic language for God? How should it be read?",
        ["face", "hand", "throne"],
        ["55:27", "5:64", "39:67"],
    ),
    (
        "Two seas verse",
        "What does the Quran mean by the two seas not mixing (55:19-20)?",
        ["seas", "barrier"],
        ["25:53", "55:19", "55:20", "27:61"],
    ),
    (
        "Pen and tablet",
        "What does the Quran say about the Preserved Tablet (lawh mahfuz) and the Pen?",
        ["tablet", "pen", "lawh"],
        ["85:21", "85:22", "68:1", "96:4"],
    ),
    (
        "Mountains as pegs",
        "What does the Quran say about mountains being pegs?",
        ["mountain", "peg", "stabilize"],
        ["78:6", "78:7", "21:31", "16:15", "31:10"],
    ),
    (
        "Embryology",
        "What does the Quran say about human embryological development?",
        ["embryo", "clot", "alaqah"],
        ["22:5", "23:13", "23:14", "75:37", "75:38", "96:2"],
    ),
    (
        "Sun's orbit",
        "What does the Quran say about the sun running on a course?",
        ["sun", "orbit", "mustaqarr"],
        ["36:38", "36:39", "36:40", "21:33"],
    ),
    (
        "Big-bang imagery",
        "Is there big-bang imagery in the Quran (21:30)?",
        ["creation", "ratq", "fatq"],
        ["21:30", "41:11"],
    ),
    (
        "Iron from sky",
        "What does the Quran mean by iron sent down from the sky (57:25)?",
        ["iron", "hadid"],
        ["57:25", "57:26"],
    ),
    (
        "Bees revelation",
        "What does the Quran mean by God 'revealing' to bees (16:68-69)?",
        ["bee", "honey", "wahy"],
        ["16:68", "16:69"],
    ),
    (
        "Ant's speech",
        "What does the Quran narrate about the speech of the ant (27:18-19)?",
        ["ant", "naml"],
        ["27:18", "27:19", "27:20"],
    ),
    (
        "Solomon and birds",
        "How does the Quran describe Solomon's command of birds and jinn?",
        ["birds", "solomon", "jinn"],
        ["27:16", "27:17", "27:39", "34:12", "34:13"],
    ),
    (
        "Throne over water",
        "What does the Quran say about God's throne being over water (11:7)?",
        ["throne", "water"],
        ["11:7"],
    ),
    (
        "Seven heavens",
        "What does the Quran teach about the seven heavens?",
        ["seven heavens", "sama"],
        ["2:29", "23:17", "41:12", "65:12", "67:3", "71:15"],
    ),
    (
        "Jinn nature",
        "What does the Quran say about the nature and origin of the jinn?",
        ["jinn", "smokeless fire"],
        ["15:27", "55:15", "72:1", "72:2", "72:11"],
    ),
    (
        "Angelic hierarchy",
        "How does the Quran describe the angels and their roles?",
        ["angels", "malaikah"],
        ["2:30", "11:69", "16:2", "35:1", "97:4"],
    ),
    (
        "Al-ghayb",
        "What does the Quran mean by belief in the Unseen (al-ghayb)?",
        ["ghayb", "unseen"],
        ["2:3", "6:50", "6:59", "27:65", "72:26"],
    ),
    (
        "Pre-existence covenant",
        "What does the Quran say about the pre-existence covenant of souls (7:172)?",
        ["covenant", "alast"],
        ["7:172", "7:173"],
    ),
    (
        "Light of believers",
        "What does the Quran mean by the light running before believers on Judgment Day (57:12)?",
        ["light", "believers"],
        ["57:12", "57:13", "57:14", "57:15", "66:8"],
    ),
]

ETHICAL = [
    (
        "Taqwa: definition",
        "What is taqwa in the Quran and how is it cultivated?",
        ["taqwa", "righteousness"],
        [],
    ),
    (
        "Sabr: forms",
        "How does the Quran describe sabr (patience) and its different forms?",
        ["sabr", "patience"],
        [],
    ),
    (
        "Ikhlas: sincerity",
        "What does the Quran teach about sincerity (ikhlas) of intention?",
        ["ikhlas", "sincerity"],
        [],
    ),
    (
        "Ihsan: excellence",
        "What is ihsan (excellence) in the Quran?",
        ["ihsan", "excellence"],
        ["2:195", "16:90"],
    ),
    (
        "Sidq: truthfulness",
        "How does the Quran value truthfulness (sidq)?",
        ["sidq", "truth"],
        ["9:119", "33:35", "39:33"],
    ),
    (
        "Honesty in trade",
        "What does the Quran say about honesty in trade and measure?",
        ["measure", "scale"],
        [
            "6:152",
            "7:85",
            "11:84",
            "11:85",
            "26:181",
            "26:182",
            "55:7",
            "55:8",
            "55:9",
            "83:1",
            "83:2",
            "83:3",
        ],
    ),
    (
        "Parents: honour",
        "What duties does the Quran assign children toward their parents?",
        ["parents", "honour"],
        ["17:23", "17:24", "29:8", "31:14", "31:15", "46:15"],
    ),
    (
        "Neighbours",
        "How does the Quran instruct treatment of neighbours?",
        ["neighbours"],
        ["4:36"],
    ),
    (
        "Orphans",
        "What does the Quran say about the rights of orphans?",
        ["orphan", "yatim"],
        ["2:220", "4:2", "4:6", "4:10", "6:152", "17:34", "89:17", "93:9", "107:2"],
    ),
    (
        "Debt forgiveness",
        "What does the Quran say about forgiving debt or giving time to a debtor?",
        ["debt", "dayn"],
        ["2:280", "2:282", "2:283"],
    ),
    (
        "Anger",
        "How does the Quran address anger and its restraint?",
        ["anger", "kazm"],
        ["3:134", "42:37"],
    ),
    (
        "Backbiting",
        "What does the Quran say about backbiting (ghibah)?",
        ["backbiting", "ghibah"],
        ["49:11", "49:12", "104:1"],
    ),
    (
        "Slander",
        "How does the Quran punish slander and false accusation?",
        ["slander", "qadhf"],
        ["24:4", "24:23"],
    ),
    (
        "Envy",
        "What does the Quran teach about envy (hasad)?",
        ["envy", "hasad"],
        ["4:54", "113:5"],
    ),
    (
        "Pride",
        "How does the Quran warn against pride (kibr)?",
        ["pride", "kibr", "arrogance"],
        ["7:13", "16:23", "31:18", "40:60", "57:23"],
    ),
    (
        "Modesty",
        "What does the Quran teach about modesty (haya') and dress?",
        ["modesty", "haya", "hijab"],
        ["7:26", "24:30", "24:31", "33:33", "33:59"],
    ),
    (
        "Charity hidden",
        "Why does the Quran praise hidden charity over public charity?",
        ["secret charity"],
        ["2:271", "2:272", "2:273"],
    ),
    (
        "Gentle speech",
        "What does the Quran teach about gentle speech?",
        ["speech", "qawl"],
        ["17:23", "17:53", "20:44", "31:18", "31:19", "41:34"],
    ),
    (
        "Lying",
        "How does the Quran condemn lying and false witness?",
        ["lie", "shahada"],
        ["2:283", "4:135", "25:72"],
    ),
    (
        "Hypocrisy",
        "What are the marks of the hypocrite (munafiq) in the Quran?",
        ["munafiq", "hypocrite"],
        ["2:8", "2:9", "2:10", "4:142", "63:1"],
    ),
    (
        "Repentance: process",
        "What is the process of true repentance (tawbah nasuh) in the Quran?",
        ["tawbah", "repentance"],
        ["66:8", "39:53", "25:70"],
    ),
    (
        "Forgiving others",
        "Why does the Quran make forgiving others a high virtue?",
        ["forgive", "afw"],
        ["3:134", "42:40", "42:43", "64:14"],
    ),
    (
        "Hospitality",
        "What does the Quran teach about hospitality, drawing on Abraham?",
        ["hospitality"],
        ["11:69", "11:70", "11:71", "51:24", "51:25", "51:26", "51:27"],
    ),
    (
        "Gratitude tests",
        "How does the Quran describe gratitude (shukr) being tested by ease and hardship?",
        ["shukr", "gratitude"],
        ["14:7", "27:40", "2:155", "2:156"],
    ),
    (
        "Wealth as test",
        "Why does the Quran call wealth and children a test (fitnah)?",
        ["wealth", "fitnah"],
        ["8:28", "64:15", "63:9", "57:20"],
    ),
    (
        "Worldly life",
        "How does the Quran describe the deceptive nature of worldly life (dunya)?",
        ["dunya", "world"],
        ["3:14", "3:185", "6:32", "29:64", "57:20"],
    ),
    (
        "Trust in God",
        "What does the Quran say about trusting in God (tawakkul)?",
        ["tawakkul", "trust"],
        ["3:159", "8:2", "65:3"],
    ),
    (
        "Companionship: bad",
        "How does the Quran warn against bad companionship?",
        ["companion", "friend"],
        ["25:27", "25:28", "25:29", "43:67"],
    ),
    (
        "Marriage purpose",
        "What does the Quran identify as the purpose of marriage (30:21)?",
        ["marriage", "zawj"],
        ["30:21", "7:189"],
    ),
    (
        "Marriage: kindness",
        "How does the Quran command kindness in marriage even at divorce?",
        ["marriage", "divorce"],
        ["2:228", "2:229", "2:231", "4:19", "65:1", "65:2"],
    ),
    (
        "Divorce procedure",
        "What is the Quranic procedure for divorce?",
        ["talaq", "divorce"],
        ["2:226", "2:227", "2:228", "2:229", "65:1", "65:2", "65:4"],
    ),
    (
        "Inheritance fixed",
        "How does the Quran specify inheritance shares?",
        ["inheritance", "fara'id"],
        ["4:11", "4:12", "4:176"],
    ),
    (
        "Adoption rules",
        "What does the Quran clarify about adoption (33:4-5)?",
        ["adoption"],
        ["33:4", "33:5"],
    ),
    (
        "Plural marriage",
        "Under what conditions does the Quran permit plural marriage?",
        ["polygamy"],
        ["4:3", "4:129"],
    ),
    (
        "Mahr: bride gift",
        "What does the Quran say about the dower (mahr / saduqah)?",
        ["mahr", "dower"],
        ["4:4", "4:24", "60:10"],
    ),
    (
        "Breastfeeding period",
        "What does the Quran specify about breastfeeding (2:233)?",
        ["breastfeeding", "rida"],
        ["2:233", "31:14", "46:15", "65:6"],
    ),
    (
        "Hudud: theft",
        "What is the Quranic ruling on theft (5:38)?",
        ["theft", "sariqah"],
        ["5:38", "5:39", "12:75"],
    ),
    (
        "Hudud: adultery",
        "How does the Quran address adultery (zina)?",
        ["zina", "adultery"],
        ["17:32", "24:2", "24:3"],
    ),
    (
        "Hudud: false witness",
        "What does the Quran prescribe for false witness against chaste women?",
        ["qadhf", "slander"],
        ["24:4", "24:5", "24:11", "24:12", "24:13"],
    ),
    (
        "Retaliation: qisas",
        "How does the Quran balance retaliation (qisas) and pardon?",
        ["qisas", "retaliation"],
        ["2:178", "2:179", "5:45", "17:33", "42:40"],
    ),
    (
        "Murder: gravity",
        "Why does the Quran liken the killing of one person to killing all humanity (5:32)?",
        ["murder", "qatl"],
        ["5:32", "5:33", "6:151", "17:33"],
    ),
    (
        "Suicide",
        "What does the Quran say about not killing oneself (4:29)?",
        ["suicide"],
        ["4:29", "4:30"],
    ),
    (
        "Riba: gravity",
        "Why does the Quran call riba (usury) war against God (2:279)?",
        ["riba", "usury"],
        ["2:275", "2:276", "2:277", "2:278", "2:279", "3:130", "30:39"],
    ),
    (
        "Gambling",
        "What does the Quran say about gambling and games of chance?",
        ["gambling", "maysir"],
        ["2:219", "5:90", "5:91"],
    ),
    (
        "Wine prohibition",
        "How does the Quran gradually prohibit intoxicants?",
        ["khamr", "wine"],
        ["2:219", "4:43", "5:90", "5:91"],
    ),
    (
        "Food: halal",
        "What does the Quran specify as forbidden foods?",
        ["food", "halal", "haram"],
        ["2:172", "2:173", "5:3", "5:5", "6:118", "6:119", "6:121", "6:145", "16:115"],
    ),
    (
        "Food: pork",
        "Why does the Quran specifically prohibit pork?",
        ["pork", "swine"],
        ["2:173", "5:3", "6:145", "16:115"],
    ),
    (
        "Hunting",
        "What does the Quran say about hunting and game during ihram?",
        ["hunting", "game"],
        ["5:1", "5:2", "5:4", "5:94", "5:95", "5:96"],
    ),
    (
        "Slaughter: God's name",
        "Why must God's name be pronounced on slaughtered animals?",
        ["slaughter", "name"],
        ["6:118", "6:119", "6:121", "5:3"],
    ),
]

# Cosmology / metaphysics (cat 10)
COSMOLOGY = [
    (
        "Creation: six days",
        "What does the Quran mean by creation in six days?",
        ["six days", "creation"],
        [
            "7:54",
            "10:3",
            "11:7",
            "32:4",
            "41:9",
            "41:10",
            "41:11",
            "41:12",
            "50:38",
            "57:4",
        ],
    ),
    (
        "Adam: viceregency",
        "What is the meaning of Adam being God's viceregent (khalifa) on earth?",
        ["khalifa", "adam"],
        ["2:30", "2:31", "2:32", "2:33", "2:34", "6:165", "35:39"],
    ),
    (
        "Iblis: refusal",
        "Why did Iblis refuse to prostrate, according to the Quran?",
        ["iblis", "satan"],
        [
            "2:34",
            "7:11",
            "7:12",
            "7:13",
            "7:14",
            "7:15",
            "7:16",
            "7:17",
            "15:28",
            "15:29",
            "15:30",
            "15:31",
            "15:32",
            "15:33",
            "15:34",
            "15:35",
            "15:36",
            "15:37",
            "15:38",
            "15:39",
            "15:40",
            "18:50",
            "38:71",
            "38:72",
            "38:73",
            "38:74",
            "38:75",
            "38:76",
            "38:77",
            "38:78",
        ],
    ),
    (
        "Gardens of Eden",
        "What is the Garden where Adam and Eve lived, per the Quran?",
        ["garden", "eden"],
        [
            "2:35",
            "2:36",
            "7:19",
            "7:20",
            "7:21",
            "7:22",
            "7:23",
            "7:24",
            "7:25",
            "20:117",
            "20:118",
            "20:119",
            "20:120",
            "20:121",
            "20:122",
            "20:123",
        ],
    ),
    (
        "The Hour: signs",
        "What signs of the Hour does the Quran mention?",
        ["hour", "qiyamah"],
        [
            "6:158",
            "7:187",
            "16:77",
            "21:96",
            "21:97",
            "27:82",
            "33:63",
            "47:18",
            "54:1",
        ],
    ),
    (
        "Beast of the earth",
        "What is the Beast of the earth (dabbat al-ard, 27:82)?",
        ["beast"],
        ["27:82"],
    ),
    (
        "Gog and Magog",
        "Who are Yajuj and Majuj (Gog and Magog) in the Quran?",
        ["yajuj", "majuj"],
        ["18:94", "18:95", "18:96", "18:97", "18:98", "21:96", "21:97"],
    ),
    (
        "Dhul-Qarnayn",
        "What does the Quran narrate about Dhul-Qarnayn?",
        ["dhul-qarnayn"],
        [
            "18:83",
            "18:84",
            "18:85",
            "18:86",
            "18:87",
            "18:88",
            "18:89",
            "18:90",
            "18:91",
            "18:92",
            "18:93",
            "18:94",
            "18:95",
            "18:96",
            "18:97",
            "18:98",
        ],
    ),
    (
        "Cave companions",
        "What is the story of the Sleepers of the Cave (Ashab al-Kahf)?",
        ["cave", "kahf"],
        [
            "18:9",
            "18:10",
            "18:11",
            "18:12",
            "18:13",
            "18:14",
            "18:15",
            "18:16",
            "18:17",
            "18:18",
            "18:19",
            "18:20",
            "18:21",
            "18:22",
            "18:25",
            "18:26",
        ],
    ),
    (
        "Khidr encounter",
        "What does the Quran teach through Moses' encounter with Khidr (18:60-82)?",
        ["khidr", "moses"],
        [
            "18:60",
            "18:61",
            "18:62",
            "18:63",
            "18:64",
            "18:65",
            "18:66",
            "18:67",
            "18:68",
            "18:69",
            "18:70",
            "18:71",
            "18:72",
            "18:73",
            "18:74",
            "18:75",
            "18:76",
            "18:77",
            "18:78",
            "18:79",
            "18:80",
            "18:81",
            "18:82",
        ],
    ),
    (
        "Night journey",
        "What does the Quran say about Muhammad's night journey (isra)?",
        ["isra", "night journey"],
        ["17:1"],
    ),
    (
        "Ascension",
        "Does the Quran describe Muhammad's ascension (mi`raj)?",
        ["miraj", "ascension"],
        [
            "17:1",
            "53:1",
            "53:2",
            "53:3",
            "53:4",
            "53:5",
            "53:6",
            "53:7",
            "53:8",
            "53:9",
            "53:10",
            "53:11",
            "53:12",
            "53:13",
            "53:14",
            "53:15",
            "53:16",
            "53:17",
            "53:18",
        ],
    ),
    (
        "Two horizons",
        "What does the Quran mean by 'two bows' length' or nearer (53:9)?",
        ["bow", "qaba"],
        ["53:8", "53:9", "53:10"],
    ),
    (
        "Mary virgin birth",
        "How does the Quran describe Mary conceiving Jesus?",
        ["mary", "maryam"],
        [
            "3:42",
            "3:43",
            "3:44",
            "3:45",
            "3:46",
            "3:47",
            "19:16",
            "19:17",
            "19:18",
            "19:19",
            "19:20",
            "19:21",
            "19:22",
            "19:23",
            "19:24",
            "19:25",
            "19:26",
            "19:27",
            "19:28",
            "19:29",
            "19:30",
            "19:31",
            "19:32",
            "19:33",
            "21:91",
            "66:12",
        ],
    ),
    (
        "Jesus: not crucified",
        "What does the Quran teach about Jesus not being crucified?",
        ["jesus", "crucify"],
        ["4:157", "4:158", "4:159"],
    ),
    (
        "Jesus second coming",
        "Does the Quran reference Jesus' second coming?",
        ["jesus", "return"],
        ["43:61"],
    ),
    (
        "Houris",
        "What does the Quran say about the companions in Paradise (hur)?",
        ["hur", "paradise"],
        [
            "44:54",
            "52:20",
            "55:56",
            "55:72",
            "56:22",
            "56:35",
            "56:36",
            "56:37",
            "78:33",
        ],
    ),
    (
        "Rivers of paradise",
        "What rivers does the Quran describe in paradise?",
        ["river", "paradise"],
        ["47:15"],
    ),
    (
        "Trees of paradise",
        "What trees does the Quran mention in paradise (sidrat al-muntaha, tuba)?",
        ["sidrah", "tuba"],
        ["53:14", "53:15", "53:16", "13:29", "56:28", "56:29"],
    ),
    (
        "Hell levels",
        "Does the Quran describe levels or names of Hell?",
        ["hell", "jahannam"],
        [
            "104:4",
            "104:5",
            "104:6",
            "104:7",
            "104:8",
            "104:9",
            "70:15",
            "70:16",
            "70:17",
            "70:18",
            "70:19",
            "70:20",
            "70:21",
            "70:22",
            "70:23",
            "70:24",
            "70:25",
            "70:26",
            "70:27",
            "70:28",
        ],
    ),
]

LEGAL = [
    (
        "Salat: five vs three prayers",
        "Does the Quran specify five or fewer daily prayers, per Khalifa's reading?",
        ["salat", "prayers"],
        ["2:238", "4:103", "11:114", "17:78", "20:130"],
    ),
    (
        "Wudu",
        "What does the Quran teach about ablution (wudu)?",
        ["wudu", "ablution"],
        ["5:6"],
    ),
    (
        "Tayammum",
        "When does the Quran allow dry ablution (tayammum)?",
        ["tayammum"],
        ["4:43", "5:6"],
    ),
    (
        "Fasting: exemptions",
        "Who is exempted from fasting in Ramadan per the Quran?",
        ["fasting", "exempt"],
        ["2:184", "2:185"],
    ),
    (
        "Pilgrimage exemptions",
        "Who is exempted from hajj?",
        ["hajj", "exempt"],
        ["3:97", "2:196", "2:197"],
    ),
    (
        "Jizya",
        "What does the Quran say about jizya from the People of the Book?",
        ["jizya"],
        ["9:29"],
    ),
    (
        "Spoils of war",
        "How does the Quran regulate the distribution of spoils of war (8:41)?",
        ["ghanima", "spoils"],
        ["8:1", "8:41", "59:7", "59:8"],
    ),
    (
        "Captives",
        "What does the Quran instruct about treating captives kindly?",
        ["captives", "asra"],
        ["8:67", "8:68", "8:69", "8:70", "47:4", "76:8"],
    ),
    (
        "Treaties",
        "How does the Quran command honouring treaties?",
        ["treaty", "ahd"],
        ["8:55", "8:56", "8:58", "9:1", "9:4", "9:7", "16:91", "16:92"],
    ),
    (
        "War: just cause",
        "When is fighting permitted according to the Quran?",
        ["fighting", "qital"],
        ["2:190", "2:191", "2:192", "2:193", "2:194", "22:39", "22:40", "60:8", "60:9"],
    ),
    (
        "No compulsion",
        "Why does the Quran say there is no compulsion in religion (2:256)?",
        ["compulsion", "religion"],
        ["2:256", "10:99", "18:29", "88:21", "88:22"],
    ),
    (
        "Witnesses in trade",
        "What does the Quran say about witnesses in commercial transactions?",
        ["witness", "trade"],
        ["2:282", "2:283"],
    ),
    (
        "Will and testament",
        "What does the Quran specify about writing a will (wasiyyah)?",
        ["will", "wasiyyah"],
        ["2:180", "2:181", "2:182", "5:106"],
    ),
    (
        "Greeting peace",
        "What greeting does the Quran teach (salam)?",
        ["salam", "greeting"],
        [
            "4:86",
            "6:54",
            "10:10",
            "13:24",
            "24:27",
            "24:61",
            "25:75",
            "33:44",
            "56:25",
            "56:26",
        ],
    ),
    (
        "Asking permission",
        "What rules of asking permission to enter houses does the Quran prescribe (24:27-29)?",
        ["permission", "house"],
        ["24:27", "24:28", "24:29", "24:58", "24:59"],
    ),
]

COMPARATIVE = [
    (
        "People of Book: respect",
        "How does the Quran call on dialogue with People of the Book (3:64)?",
        ["people of book"],
        ["3:64", "3:113", "3:114", "3:199", "29:46"],
    ),
    (
        "Trinity rebuttal",
        "What does the Quran say in rebuttal of Trinitarian theology?",
        ["trinity"],
        [
            "4:171",
            "5:17",
            "5:72",
            "5:73",
            "5:75",
            "5:116",
            "5:117",
            "5:118",
            "112:1",
            "112:2",
            "112:3",
            "112:4",
        ],
    ),
    (
        "Crucifixion claim",
        "Why does the Quran reject the claim that Jesus was crucified (4:157)?",
        ["crucify", "jesus"],
        ["4:157", "4:158"],
    ),
    (
        "Sonship denied",
        "Why does the Quran deny Jesus is the son of God?",
        ["son", "begotten"],
        ["19:88", "19:89", "19:90", "19:91", "19:92", "19:93", "112:3"],
    ),
    (
        "Israelite covenant",
        "What does the Quran say about the covenants God made with the Israelites?",
        ["covenant", "israel"],
        ["2:40", "2:41", "2:63", "2:83", "2:84", "2:93", "5:12", "5:13", "5:70"],
    ),
    (
        "Sabaeans",
        "Who are the Sabi'un in 2:62 and 5:69?",
        ["sabaeans", "sabi"],
        ["2:62", "5:69", "22:17"],
    ),
    (
        "Magians",
        "Who are the Majus (Magians) in 22:17?",
        ["majus", "magian"],
        ["22:17"],
    ),
    (
        "Common word",
        "How does 3:64 frame the 'common word' between Muslims and People of the Book?",
        ["common word"],
        ["3:64"],
    ),
    (
        "Torah authority",
        "How does the Quran describe the Torah as light and guidance?",
        ["torah", "tawrah"],
        ["3:3", "5:43", "5:44", "5:46", "5:48", "6:91", "61:6"],
    ),
    (
        "Gospel authority",
        "How does the Quran describe the Gospel (Injil)?",
        ["injil", "gospel"],
        ["3:3", "5:46", "5:47", "5:66", "5:68", "9:111", "57:27"],
    ),
    (
        "Scripture corruption",
        "What does the Quran mean by 'changing the words' (4:46, 5:13)?",
        ["tahrif", "corrupt"],
        ["2:75", "4:46", "5:13", "5:41"],
    ),
    (
        "Followers of Jesus",
        "What does the Quran say is praiseworthy about the followers of Jesus (5:82)?",
        ["nasara", "christians"],
        ["5:82", "5:83", "57:27"],
    ),
]

CODE19 = [
    (
        "19 verse: explanation",
        "Explain the 'Over it is 19' verse (74:30) and Khalifa's reading.",
        ["code-19", "nineteen"],
        ["74:30", "74:31"],
    ),
    (
        "Code-19: basmalah",
        "What is significant about the 19 letters of the Basmalah in Khalifa's system?",
        ["basmalah", "code-19"],
        ["1:1", "27:30"],
    ),
    (
        "Sura 96 first revelation",
        "Why are the first revealed words (96:1-5) Code-19 significant?",
        ["first revelation", "code-19"],
        ["96:1", "96:2", "96:3", "96:4", "96:5"],
    ),
    (
        "Mysterious letters: introduction",
        "Introduce the mysterious letters (muqatta`at) and their Code-19 framing.",
        ["muqattaat"],
        [
            "2:1",
            "3:1",
            "7:1",
            "10:1",
            "11:1",
            "12:1",
            "13:1",
            "14:1",
            "15:1",
            "19:1",
            "20:1",
            "26:1",
            "27:1",
            "28:1",
            "29:1",
            "30:1",
            "31:1",
            "32:1",
            "36:1",
            "38:1",
            "40:1",
            "41:1",
            "42:1",
            "43:1",
            "44:1",
            "45:1",
            "46:1",
            "50:1",
            "68:1",
        ],
    ),
    (
        "Last revelation 110",
        "Why does Khalifa identify Surah 110 (Triumph) as the last revealed?",
        ["110", "last revelation"],
        ["110:1", "110:2", "110:3"],
    ),
    (
        "Khalifa: Messenger of Covenant",
        "Who is the Messenger of the Covenant in Khalifa's reading of 3:81?",
        ["messenger of covenant"],
        ["3:81"],
    ),
    (
        "Khalifa: 9:128-129 status",
        "What is Khalifa's position on 9:128-129 and why?",
        ["9:128", "forgery"],
        ["9:127"],
    ),
    (
        "Khalifa: hadith rejection",
        "On what Quranic basis does Khalifa reject hadith as religious source?",
        ["hadith", "tradition"],
        ["6:38", "6:114", "7:185", "12:111", "31:6", "45:6", "77:50"],
    ),
    (
        "Submitters: identity",
        "What does the Quran call the followers of God's religion, per Khalifa?",
        ["submitters", "muslim"],
        ["3:67", "22:78", "27:91", "39:11", "39:12"],
    ),
    (
        "Idol worship of Muhammad",
        "How does Khalifa interpret 3:144 as warning against idolizing Muhammad?",
        ["idolize"],
        ["3:144", "39:65"],
    ),
    (
        "System of mathematics",
        "How does Khalifa describe the Quran's mathematical 'code' as a sign for non-Arabs?",
        ["code", "mathematical"],
        ["74:30", "74:31", "41:53", "85:21", "85:22"],
    ),
]

PRACTICAL = [
    (
        "Decision making: shura",
        "How does the Quran model decision-making by consultation (shura)?",
        ["shura", "consultation"],
        ["3:159", "42:38"],
    ),
    (
        "Anxiety: remembrance",
        "What does the Quran prescribe for anxiety and unease of heart?",
        ["dhikr", "rest"],
        ["13:28", "20:124", "2:152"],
    ),
    (
        "Provision worry",
        "How does the Quran respond to worry about provision (rizq)?",
        ["rizq", "sustenance"],
        ["11:6", "29:60", "30:40", "65:2", "65:3", "67:21"],
    ),
    (
        "Hopelessness",
        "What hope does the Quran give those who feel hopeless?",
        ["hope", "despair"],
        ["12:87", "15:56", "39:53", "94:5", "94:6"],
    ),
    (
        "Time management",
        "Does the Quran teach anything about the urgency of time (asr)?",
        ["asr", "time"],
        ["103:1", "103:2", "103:3"],
    ),
    (
        "Sleep as sign",
        "What does the Quran teach about sleep and rest?",
        ["sleep", "rest"],
        ["25:47", "30:23", "39:42", "78:9"],
    ),
    (
        "Travel etiquette",
        "What guidance does the Quran offer for travel and journeys?",
        ["travel", "safar"],
        ["2:184", "2:283", "4:43", "4:101", "5:6"],
    ),
    (
        "Eating manners",
        "What manners of eating and drinking does the Quran teach?",
        ["eat", "drink"],
        ["2:172", "2:173", "5:88", "7:31", "20:81"],
    ),
    (
        "Wealth: priorities",
        "What does the Quran teach about how to prioritize spending?",
        ["spending", "infaq"],
        ["2:215", "2:219", "2:267", "9:60"],
    ),
    (
        "Leadership",
        "What qualities make a just leader, per the Quran?",
        ["leader", "just"],
        ["4:58", "4:59", "5:8", "21:73", "32:24"],
    ),
    (
        "Conflict resolution",
        "How does the Quran teach reconciling between disputing parties?",
        ["islah", "reconcile"],
        ["4:35", "4:114", "49:9", "49:10"],
    ),
    (
        "Forgiveness of self",
        "What does the Quran say about forgiving oneself after sin?",
        ["sin", "forgive self"],
        ["12:53", "39:53", "4:110"],
    ),
    (
        "Knowledge seeking",
        "How does the Quran encourage seeking knowledge?",
        ["knowledge", "ilm"],
        ["20:114", "35:28", "39:9", "58:11", "96:1", "96:2", "96:3", "96:4", "96:5"],
    ),
    (
        "Reflection on creation",
        "How does the Quran call on humans to reflect on creation?",
        ["reflect", "tafakkur"],
        ["3:190", "3:191", "16:11", "16:12", "16:69", "30:8"],
    ),
    (
        "Aging parents",
        "What specific guidance does 17:23-24 give about aged parents?",
        ["parents", "elderly"],
        ["17:23", "17:24"],
    ),
    (
        "Children: kindness",
        "How does the Quran teach kindness to one's children?",
        ["children", "kind"],
        ["6:151", "17:31", "60:12"],
    ),
    (
        "Killing children for poverty",
        "Why does the Quran condemn killing children for fear of poverty?",
        ["children", "poverty"],
        ["6:151", "17:31", "60:12", "81:8", "81:9"],
    ),
    (
        "Female infanticide",
        "What does the Quran say about pre-Islamic Arab female infanticide?",
        ["female", "infanticide"],
        ["16:58", "16:59", "81:8", "81:9"],
    ),
]

ROOTS = [
    (
        "Root: عبد",
        "Trace the semantic range of the root ع-ب-د (worship, slave, servant) in the Quran.",
        ["عبد", "worship"],
        [],
    ),
    (
        "Root: رحم",
        "Trace the semantic range of the root ر-ح-م (mercy, womb) in the Quran.",
        ["رحم", "mercy"],
        [],
    ),
    (
        "Root: ع-ل-م",
        "Trace the semantic range of the root ع-ل-م (knowledge, sign) in the Quran.",
        ["علم", "knowledge"],
        [],
    ),
    (
        "Root: ك-ت-ب",
        "Trace the semantic range of the root ك-ت-ب (write, book, decree) in the Quran.",
        ["كتب", "book"],
        [],
    ),
    (
        "Root: ذ-ك-ر",
        "Trace the semantic range of the root ذ-ك-ر (remember, mention) in the Quran.",
        ["ذكر", "remember"],
        [],
    ),
    (
        "Root: ر-ز-ق",
        "Trace the semantic range of the root ر-ز-ق (provide, sustain) in the Quran.",
        ["رزق", "provision"],
        [],
    ),
    (
        "Root: ح-ك-م",
        "Trace the semantic range of the root ح-ك-م (judge, wise) in the Quran.",
        ["حكم", "wisdom"],
        [],
    ),
    (
        "Root: ج-ه-د",
        "What does the Quran mean by the verb jahada (root ج-ه-د)?",
        ["جهد", "jihad"],
        ["2:218", "3:142", "9:20", "9:24", "9:88", "22:78", "25:52", "29:69"],
    ),
    (
        "Root: ف-ت-ن",
        "Trace the semantic range of fitnah (root ف-ت-ن) — trial, persecution.",
        ["فتن", "fitnah"],
        ["2:191", "2:193", "2:217", "8:25", "8:39", "8:73"],
    ),
    (
        "Root: ظ-ل-م",
        "Trace the semantic range of zulm (root ظ-ل-م) — injustice, darkness.",
        ["ظلم", "zulm"],
        [],
    ),
    (
        "Root: ن-و-ر",
        "Trace the imagery of nur (root ن-و-ر, light) in the Quran.",
        ["نور", "light"],
        [
            "5:15",
            "5:16",
            "5:44",
            "5:46",
            "7:157",
            "9:32",
            "24:35",
            "33:43",
            "39:22",
            "57:9",
            "61:8",
            "64:8",
            "65:11",
            "66:8",
        ],
    ),
    (
        "Root: ه-د-ي",
        "Trace the semantic range of huda (root ه-د-ي, guidance).",
        ["هدي", "huda"],
        [],
    ),
    (
        "Root: ض-ل-ل",
        "Trace the semantic range of dalal (root ض-ل-ل, going astray).",
        ["ضلل", "stray"],
        [],
    ),
    (
        "Root: ف-ل-ح",
        "What does it mean to attain falah (root ف-ل-ح, success/flourishing)?",
        ["فلح", "success"],
        ["2:5", "3:104", "7:69", "23:1", "30:38", "31:5"],
    ),
    (
        "Root: خ-س-ر",
        "Trace the semantic range of khusr (root خ-س-ر, loss).",
        ["خسر", "loss"],
        ["103:2"],
    ),
    (
        "Root: ق-و-م",
        "Trace the semantic range of qiyam / qawm (root ق-و-م).",
        ["قوم", "stand"],
        [],
    ),
    (
        "Root: ن-ف-س",
        "Trace the semantic range of nafs (root ن-ف-س, soul, self).",
        ["نفس", "soul"],
        [
            "12:53",
            "75:2",
            "89:27",
            "89:28",
            "89:29",
            "89:30",
            "91:7",
            "91:8",
            "91:9",
            "91:10",
        ],
    ),
    (
        "Root: ق-ل-ب",
        "Trace the semantic range of qalb (root ق-ل-ب, heart) in the Quran.",
        ["قلب", "heart"],
        [],
    ),
    (
        "Root: ع-ق-ل",
        "Trace the semantic range of `aql (root ع-ق-ل, intellect).",
        ["عقل", "intellect"],
        [
            "2:44",
            "2:73",
            "2:75",
            "2:76",
            "2:164",
            "2:170",
            "2:171",
            "3:65",
            "3:118",
            "5:58",
            "5:103",
            "6:32",
            "6:151",
            "7:169",
            "8:22",
            "10:16",
            "10:42",
            "10:100",
            "11:51",
            "12:2",
            "12:109",
            "13:4",
            "16:12",
            "16:67",
            "21:10",
            "21:67",
            "22:46",
            "23:80",
            "24:61",
            "25:44",
            "28:60",
            "29:35",
            "29:43",
            "29:63",
            "30:24",
            "30:28",
            "36:62",
            "36:68",
            "37:138",
            "39:43",
            "40:67",
            "43:3",
            "45:5",
            "49:4",
            "57:17",
            "59:14",
            "67:10",
        ],
    ),
    (
        "Root: ر-و-ح",
        "Trace the semantic range of ruh (root ر-و-ح, spirit).",
        ["روح", "spirit"],
        [
            "15:29",
            "16:2",
            "17:85",
            "21:91",
            "26:193",
            "32:9",
            "38:72",
            "40:15",
            "42:52",
            "58:22",
            "66:12",
            "70:4",
            "78:38",
            "97:4",
        ],
    ),
    (
        "Root: س-م-ع",
        "Trace the semantic range of sam` (root س-م-ع, hearing).",
        ["سمع", "hearing"],
        [],
    ),
    (
        "Root: ب-ص-ر",
        "Trace the semantic range of basar (root ب-ص-ر, sight, insight).",
        ["بصر", "sight"],
        [],
    ),
    (
        "Root: ن-ز-ل",
        "Trace the semantic range of tanzil (root ن-ز-ل, sending down).",
        ["نزل", "send down"],
        [],
    ),
    (
        "Root: س-ل-م",
        "Trace the semantic range of salam/islam (root س-ل-م).",
        ["سلم", "peace"],
        [],
    ),
    (
        "Root: ك-ف-ر",
        "Trace the semantic range of kufr (root ك-ف-ر, cover, deny).",
        ["كفر", "kufr"],
        [],
    ),
    (
        "Root: ش-ك-ر",
        "Trace the semantic range of shukr (root ش-ك-ر, gratitude).",
        ["شكر", "gratitude"],
        [],
    ),
    (
        "Root: و-ك-ل",
        "Trace the semantic range of tawakkul (root و-ك-ل, reliance).",
        ["وكل", "tawakkul"],
        [],
    ),
    (
        "Root: ص-د-ق",
        "Trace the semantic range of sidq (root ص-د-ق, truth, sincerity, charity).",
        ["صدق", "truth"],
        [],
    ),
    (
        "Root: ح-ق-ق",
        "Trace the semantic range of haqq (root ح-ق-ق, truth, right).",
        ["حقق", "haqq"],
        [],
    ),
    (
        "Root: ب-ر-ك",
        "Trace the semantic range of barakah (root ب-ر-ك, blessing).",
        ["برك", "blessing"],
        [],
    ),
    (
        "Root: ق-د-س",
        "Trace the semantic range of qudus (root ق-د-س, holy, sanctity).",
        ["قدس", "holy"],
        [
            "2:30",
            "2:87",
            "2:253",
            "5:21",
            "5:110",
            "16:102",
            "20:12",
            "21:73",
            "59:23",
            "62:1",
            "79:16",
        ],
    ),
    (
        "Root: س-ج-د",
        "Trace the semantic range of sujud (root س-ج-د, prostration).",
        ["سجد", "prostration"],
        [],
    ),
    (
        "Root: ك-ب-ر",
        "Trace the semantic range of takbir / kibr (root ك-ب-ر).",
        ["كبر", "takbir"],
        [],
    ),
    (
        "Root: غ-ف-ر",
        "Trace the semantic range of ghufran (root غ-ف-ر, forgiveness).",
        ["غفر", "ghufran"],
        [],
    ),
    (
        "Root: ن-ع-م",
        "Trace the semantic range of ni`mah (root ن-ع-م, blessing, favour).",
        ["نعم", "blessing"],
        [],
    ),
    (
        "Root: ع-د-ل",
        "Trace the semantic range of `adl (root ع-د-ل, justice).",
        ["عدل", "justice"],
        [],
    ),
    (
        "Root: ق-س-ط",
        "Trace the semantic range of qist (root ق-س-ط, equity).",
        ["قسط", "qist"],
        [],
    ),
    (
        "Root: أ-م-ن",
        "Trace the semantic range of amn / iman (root أ-م-ن, security, faith).",
        ["أمن", "amn"],
        [],
    ),
    (
        "Term: barakah",
        "How does the Quran use the word barakah, especially in 17:1 and 19:31?",
        ["barakah", "blessed"],
        ["17:1", "19:31"],
    ),
    (
        "Term: hanif",
        "What does the Quran mean by hanif, especially for Abraham?",
        ["hanif"],
        [
            "3:67",
            "3:95",
            "4:125",
            "6:79",
            "6:161",
            "10:105",
            "16:120",
            "16:123",
            "22:31",
            "30:30",
            "98:5",
        ],
    ),
]


def build_surah_questions(inv, existing) -> list[dict]:
    out = []
    for s in inv["surahs"]:
        num = s["number"]
        name = s.get("name") or f"Surah {num}"
        hits = s["cache_hits"]
        gap_score = max(0, 1000 - hits)
        priority = gap_score
        # Skip if cache already has dense coverage (>500 hits)
        if hits > 500:
            continue
        q1 = f"What is the central message of Surah {num} ({name})?"
        if norm(q1) not in existing:
            out.append(
                {
                    "category": "surah_themes",
                    "question": q1,
                    "target_themes": [name],
                    "target_verses": [f"{num}:1", f"{num}:2", f"{num}:3"],
                    "priority_score": priority + 100,
                    "gap_addressed": f"surah_{num}_hits_{hits}",
                }
            )
        if s.get("verses_count", 0) >= 4 and hits < 200:
            q2 = f"Explain Surah {num} ({name}) verse by verse."
            if norm(q2) not in existing:
                out.append(
                    {
                        "category": "surah_themes",
                        "question": q2,
                        "target_themes": [name, "verse-by-verse"],
                        "target_verses": [
                            f"{num}:{i}"
                            for i in range(1, min(s["verses_count"], 12) + 1)
                        ],
                        "priority_score": priority,
                        "gap_addressed": f"surah_{num}_verse_walk",
                    }
                )
        if s.get("mysterious_letters"):
            q3 = f"What are the mysterious letters at the start of Surah {num} and what does the Quran do with them?"
            if norm(q3) not in existing:
                out.append(
                    {
                        "category": "surah_themes",
                        "question": q3,
                        "target_themes": ["muqattaat", name],
                        "target_verses": [f"{num}:1"],
                        "priority_score": priority - 50,
                        "gap_addressed": f"surah_{num}_muqattaat",
                    }
                )
    return out


def build_prophet_questions(inv, existing) -> list[dict]:
    out = []
    for p in inv["prophets"]:
        canonical = p["canonical"]
        hits = p["cache_hits"]
        priority = max(0, 1000 - hits * 3)
        anchors = p.get("anchor_verses", [])[:6]
        for kind, template in PROPHET_QUESTION_TEMPLATES:
            q = template.format(prophet=canonical)
            if norm(q) in existing:
                continue
            out.append(
                {
                    "category": "prophets",
                    "question": q,
                    "target_themes": [canonical, kind],
                    "target_verses": anchors,
                    "priority_score": priority
                    + (50 if kind == "story" else 25 if kind == "lesson" else 0),
                    "gap_addressed": f"prophet_{canonical}_{kind}_hits_{hits}",
                }
            )
    return out


def from_curated(items, category, existing) -> list[dict]:
    out = []
    for tag, q, themes, verses in items:
        if norm(q) in existing:
            continue
        out.append(
            {
                "category": category,
                "question": q,
                "target_themes": themes,
                "target_verses": verses,
                "priority_score": 600,
                "gap_addressed": f"{category}_{tag}",
            }
        )
    return out


def build_iconic_questions(inv, existing) -> list[dict]:
    out = []
    for v in inv["iconic_verses"][:50]:
        q = f"Explain verse {v['verseId']} and its place in the Quran."
        if norm(q) in existing:
            continue
        out.append(
            {
                "category": "iconic_verses",
                "question": q,
                "target_themes": ["verse_deep_dive"],
                "target_verses": [v["verseId"]],
                "priority_score": 400 + v.get("degree", 0),
                "gap_addressed": f"iconic_{v['verseId']}_deg_{v.get('degree', 0)}",
            }
        )
    return out


def main():
    inv = json.load(INVENTORY.open(encoding="utf-8"))
    existing = load_existing_questions()
    print(f"existing cache questions (normalized): {len(existing)}")

    candidates: list[dict] = []
    candidates += from_curated(THEOLOGICAL, "theological", existing)
    candidates += build_prophet_questions(inv, existing)
    candidates += build_surah_questions(inv, existing)
    candidates += from_curated(ETHICAL, "ethical", existing)
    candidates += from_curated(LEGAL, "legal_ritual", existing)
    candidates += from_curated(COMPARATIVE, "comparative_religion", existing)
    candidates += from_curated(CODE19, "code19_khalifa", existing)
    candidates += from_curated(ROOTS, "linguistic_etymological", existing)
    candidates += from_curated(PRACTICAL, "practical_contemporary", existing)
    candidates += from_curated(COSMOLOGY, "cosmology_metaphysics", existing)
    candidates += build_iconic_questions(inv, existing)

    print(f"candidates generated: {len(candidates)}")

    # Dedupe candidate-against-candidate
    seen = set()
    unique = []
    for c in candidates:
        n = norm(c["question"])
        if n in seen:
            continue
        seen.add(n)
        unique.append(c)
    print(f"unique candidates: {len(unique)}")

    # Sort by priority descending
    unique.sort(key=lambda x: -x["priority_score"])

    # Assign IDs and split into primary/reserve
    primary = unique[:500]
    reserve = unique[500:750]

    for i, c in enumerate(primary, start=1):
        c["id"] = f"expansion-{i:03d}"
    for i, c in enumerate(reserve, start=501):
        c["id"] = f"expansion-{i:03d}"

    # Category breakdown
    cat_counts = defaultdict(int)
    for c in primary:
        cat_counts[c["category"]] += 1
    print("\nPrimary by category:")
    for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:30s} {cnt}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {"primary": primary, "reserve": reserve, "total_candidates": len(unique)},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
