"""
Phase 6 seeding — fresh question bank targeting gaps in the 500-entry cache.

Focus areas:
  - Single-verse deep dives (~60)  — "Explain verse X:Y" for high-value verses
  - Practice-focused questions for Submitters (~30)
  - Life-situation / applied questions (~25)
  - Cross-verse thematic pulls (~30)
  - Arabic word studies in new directions (~15)
"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import json
from pathlib import Path
import overnight_seed as engine


PHASE6_RAW = [
    # ── Single-verse deep dives (~60)
    "Explain verse 2:3 — who are the believers that walk in the unseen?",
    "Explain verse 2:62 — what does it mean about Jews, Christians, and Sabians having their reward?",
    "Explain verse 2:115 — what does 'to God belongs the east and west' mean?",
    "Explain verse 2:148 — what does 'race to good deeds' command us to do?",
    "Explain verse 2:152 — what does 'remember Me and I will remember you' mean?",
    "Explain verse 2:156 — the Istirjaa verse, what does it teach about calamity?",
    "Explain verse 2:163 — the declaration of one God, its implications?",
    "Explain verse 2:186 — what does it promise about God answering prayers?",
    "Explain verse 2:216 — what does 'you may hate a thing that is good for you' teach?",
    "Explain verse 2:255 — Ayat al-Kursi, what does each phrase say about God?",
    "Explain verse 2:286 — what does it say about God not burdening a soul beyond capacity?",
    "Explain verse 3:8 — what does it mean to ask for steadfastness after guidance?",
    "Explain verse 3:54 — what does it mean that God is the best of schemers?",
    "Explain verse 3:103 — what does 'hold fast to the rope of God' teach?",
    "Explain verse 3:190 — what does it say about signs for those of understanding?",
    "Explain verse 4:36 — the comprehensive command of rights, what does it include?",
    "Explain verse 4:59 — what does 'obey God, the messenger, and those in authority' mean?",
    "Explain verse 5:32 — what does 'whoever kills one soul' teach about human life?",
    "Explain verse 5:48 — what does 'to each We gave a law and a way' teach?",
    "Explain verse 6:59 — what does it say about God's knowledge of the unseen?",
    "Explain verse 7:31 — what does 'dress well for every masjid' command?",
    "Explain verse 7:180 — what does it teach about God's most beautiful names?",
    "Explain verse 9:51 — what does 'nothing befalls us but what God has written' teach?",
    "Explain verse 10:62 — who are the allies of God and what is their state?",
    "Explain verse 11:112 — the command to remain steadfast, what does it require?",
    "Explain verse 12:87 — what does 'do not despair of God's mercy' teach?",
    "Explain verse 13:28 — what does 'hearts find rest in the remembrance of God' mean?",
    "Explain verse 14:7 — what does 'if you are grateful, I will increase you' teach?",
    "Explain verse 15:9 — what does God's promise to preserve the reminder mean?",
    "Explain verse 16:90 — the threefold command of justice, goodness, and kinship?",
    "Explain verse 16:97 — what does 'whoever does good, male or female, with faith' promise?",
    "Explain verse 17:23 — what does the command to honor parents include?",
    "Explain verse 17:36 — what does 'do not pursue that of which you have no knowledge' teach?",
    "Explain verse 17:82 — what does it mean that the Quran is healing and mercy?",
    "Explain verse 18:28 — what does 'restrain yourself with those who call on God' teach?",
    "Explain verse 18:110 — the conclusion of Al-Kahf, its teaching on worship?",
    "Explain verse 19:96 — what does it promise for those who believe and do good?",
    "Explain verse 20:14 — 'establish the prayer to remember Me', what does it teach?",
    "Explain verse 20:124 — what does turning away from God's remembrance bring?",
    "Explain verse 21:107 — 'we sent you as a mercy to the worlds', who is addressed?",
    "Explain verse 24:35 — the Light verse, what metaphor does it build?",
    "Explain verse 25:63 — who are the servants of the Most Merciful?",
    "Explain verse 25:70 — what does it promise about evil deeds being replaced with good?",
    "Explain verse 28:77 — what does 'seek the abode of the Hereafter through what God has given you' teach?",
    "Explain verse 29:69 — what does 'those who strive in Us, We guide to Our ways' promise?",
    "Explain verse 30:21 — what does it teach about marriage as a sign of God?",
    "Explain verse 31:13 — Luqman's warning to his son about idolatry, why is it profound?",
    "Explain verse 33:35 — what categories of believers are listed and what reward?",
    "Explain verse 35:15 — what does 'you are the poor in need of God' teach?",
    "Explain verse 39:53 — 'do not despair of God's mercy', what hope does it offer?",
    "Explain verse 41:30 — what does it promise those who say 'our Lord is God' then remain steadfast?",
    "Explain verse 42:30 — what does it teach about affliction being from our own hands?",
    "Explain verse 49:10 — what does it say about believers being brothers?",
    "Explain verse 49:13 — 'We created you into nations and tribes', its message on dignity?",
    "Explain verse 50:16 — 'We are closer to him than his jugular vein', what does it teach?",
    "Explain verse 55:13 — the refrain 'which of your Lord's favors will you deny?'",
    "Explain verse 64:11 — what does 'no calamity strikes except by God's leave' teach?",
    "Explain verse 65:3 — what does 'whoever trusts in God, He is sufficient for him' promise?",
    "Explain verse 93:5 — God's promise to His messenger, what solace does it offer?",
    "Explain verse 103:1-3 — Al-Asr, the three conditions for not being in loss?",

    # ── Submitter practice questions (~30)
    "How should a Submitter begin their day according to the Quran?",
    "How does the Quran describe performing the five daily prayers?",
    "What Quranic evidence supports the Dawn (Fajr) and Afternoon (Asr) prayers?",
    "What Quranic evidence supports the Sunset (Maghrib) and Night (Isha) prayers?",
    "What does the Quran say about praying while traveling?",
    "What does the Quran say about the contact prayer (Salah) positions?",
    "How does the Quran describe the Sabbath and do Submitters observe it?",
    "What does the Quran say about the direction of Kaaba as a qiblah?",
    "What Quranic verses support the annual pilgrimage practices?",
    "What does the Quran say about reciting in Arabic versus understanding the meaning?",
    "How does the Quran describe the Night of Decree (Laylat al-Qadr)?",
    "What does the Quran say about fasting during Ramadan and exceptions?",
    "What does the Quran say about reading the Quran in audible voice at night?",
    "How does the Quran instruct regarding charity's proper amount and receivers?",
    "What does the Quran say about vowing or making pledges to God?",
    "What does the Quran say about celebrating holidays not mentioned in it?",
    "What does the Quran say about following hadith or sunnah beyond itself?",
    "How does Rashad Khalifa's translation treat the Basmalah as a verse?",
    "What does the Quran say about invoking only God during prayer?",
    "How does the Quran describe asking forgiveness from God directly?",
    "What Quranic verses discuss the role of the Messenger of the Covenant?",
    "What does the Quran say about claiming prophethood or messengerhood?",
    "What does the Quran say about mathematical signs over 19 in the Quran?",
    "What does the Quran say about dedicating worship purely to God (ikhlas)?",
    "How does the Quran instruct regarding the distribution of inheritance by fixed shares?",
    "What Quranic verses support ritual cleanliness before prayer?",
    "What does the Quran say about reciting in prayer versus silent contemplation?",
    "How does the Quran guide the voice during Fajr recitation?",
    "What does the Quran say about praying for those who died in unbelief?",
    "What does the Quran say about praying out of habit versus sincerity?",

    # ── Applied / life situation questions (~25)
    "What guidance does the Quran offer when one faces injustice at work?",
    "What guidance does the Quran offer when dealing with a controlling family member?",
    "What does the Quran say about how to treat someone who insults your faith?",
    "How does the Quran guide one going through a painful divorce?",
    "How does the Quran guide someone struggling with addiction?",
    "How does the Quran guide one whose parents follow different beliefs?",
    "How does the Quran guide someone facing persecution for their convictions?",
    "How does the Quran advise dealing with financial hardship or debt?",
    "How does the Quran advise the loss of a child or young spouse?",
    "How does the Quran advise those struggling with self-worth?",
    "How does the Quran advise choosing between two permissible paths?",
    "How does the Quran advise on forgiving someone who hurt you deeply?",
    "How does the Quran guide someone who made a grave sin and feels unforgivable?",
    "How does the Quran advise raising children in a non-believing society?",
    "How does the Quran guide leaders in positions of political power?",
    "How does the Quran advise on making decisions under uncertainty?",
    "How does the Quran guide someone leaving a faith community?",
    "How does the Quran advise when facing a terminal illness?",
    "How does the Quran advise when one discovers their parents are wrong?",
    "How does the Quran address unrequited love?",
    "How does the Quran advise on dealing with workplace gossip?",
    "How does the Quran guide someone who feels spiritually dry or disconnected?",
    "How does the Quran advise parents on children leaving the faith?",
    "How does the Quran guide during times of public unrest or war?",
    "How does the Quran advise when witnessing wrongdoing and fearing consequences?",

    # ── Cross-verse thematic pulls (~30)
    "What does the Quran say about water as a symbol and substance?",
    "What does the Quran say about fire in its various roles?",
    "What does the Quran say about gardens and their symbolism?",
    "What does the Quran say about mountains throughout its teaching?",
    "What does the Quran say about stars and celestial bodies?",
    "What does the Quran say about wind as a divine instrument?",
    "What does the Quran say about food and eating etiquette?",
    "What does the Quran say about dreams and their interpretation?",
    "What does the Quran say about music and poetry?",
    "What does the Quran say about writing and the pen?",
    "What does the Quran say about clothing and modesty for men and women?",
    "What does the Quran say about sleep as a divine sign?",
    "What does the Quran say about the human body as a creation?",
    "What does the Quran say about animal creation and its purposes?",
    "What does the Quran say about the embryonic stages of human creation?",
    "What does the Quran say about night and day as metaphors?",
    "What does the Quran say about seasons and time cycles?",
    "What does the Quran say about milk and honey as sustenance?",
    "What does the Quran say about iron as a unique creation?",
    "What does the Quran say about pearls as imagery?",
    "What does the Quran say about scales of weight and measurement?",
    "What does the Quran say about markets and commerce ethics?",
    "What does the Quran say about medicine and healing?",
    "What does the Quran say about spiders and their webs?",
    "What does the Quran say about bees and their work?",
    "What does the Quran say about cattle and their benefits?",
    "What does the Quran say about ships and seafaring?",
    "What does the Quran say about cities and civilizations that fell?",
    "What does the Quran say about the valley and its role in prophetic stories?",
    "What does the Quran say about gold and silver?",

    # ── Arabic word studies — new directions (~15)
    "What are the Quranic meanings of the word 'fitrah' (original nature)?",
    "What are the Quranic meanings of the word 'nafs' (soul/self)?",
    "What are the Quranic meanings of the word 'ruh' (spirit)?",
    "What are the Quranic meanings of the word 'qalb' (heart)?",
    "What are the Quranic meanings of the word 'aql' (intellect)?",
    "What are the Quranic meanings of the word 'haqq' (truth/right)?",
    "What are the Quranic meanings of the word 'baatil' (falsehood/void)?",
    "What are the Quranic meanings of the word 'rahma' (mercy)?",
    "What are the Quranic meanings of the word 'rizq' (provision)?",
    "What are the Quranic meanings of the word 'dunya' (worldly life)?",
    "What are the Quranic meanings of the word 'akhirah' (Hereafter)?",
    "What are the Quranic meanings of the word 'ghayb' (unseen)?",
    "What are the Quranic meanings of the word 'ayat' (signs/verses)?",
    "What are the Quranic meanings of the word 'kitab' (book/scripture)?",
    "What are the Quranic meanings of the word 'nur' (light)?",
]


def filter_new(questions, cache_path="data/answer_cache.json"):
    try:
        cache = json.loads(Path(cache_path).read_text(encoding="utf-8"))
        seen = {e.get("question", "").strip().lower() for e in cache}
    except Exception:
        seen = set()
    new = [q for q in questions if q.strip().lower() not in seen]
    return new


if __name__ == "__main__":
    fresh = filter_new(PHASE6_RAW)
    print(f"[phase6] total={len(PHASE6_RAW)}, after dedup={len(fresh)}")
    engine.QUESTIONS = fresh
    # OpenRouter primary; engine auto-flips to local on 3+ back-to-back 429s
    # Also clear state, since state file has old Phase 5 "done" entries that don't match these
    from pathlib import Path as _P
    sf = _P("overnight_seed.state.json")
    if sf.exists():
        try:
            st = json.loads(sf.read_text(encoding="utf-8"))
            st["done"] = [q for q in st.get("done", []) if q in fresh]
            st["failed"] = []
            sf.write_text(json.dumps(st, indent=2), encoding="utf-8")
            print(f"[phase6] state pruned to {len(st['done'])} matching done entries")
        except Exception as e:
            print(f"[phase6] state prune failed: {e}")
    engine.main()
