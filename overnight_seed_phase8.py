"""
Phase 8 — third wave of gap-filling questions.

Targets areas still under-represented in the 718-entry cache:
  - Divine attributes by name (asma ul-husna) — individual deep dives (~30)
  - Detailed creation narrative (~20)
  - Specific sin categories (~20)
  - Prayer / worship mechanics deep dives (~20)
  - Unique Quranic vocabulary (hapax/rare words) (~20)
  - Submitter law — concrete situations (~20)
  - Scripture of prior prophets (~15)
  - Angels, jinn, souls taxonomy (~20)
  - Modern-day applications (~15)
"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import json
from pathlib import Path
import overnight_seed as engine


PHASE8_RAW = [
    # ── Divine attributes by name (~30)
    "What does the Quran say about God being Ar-Rahman (the Most Gracious)?",
    "What does the Quran say about God being Ar-Rahim (the Most Merciful)?",
    "What does the Quran say about God being Al-Malik (the Sovereign)?",
    "What does the Quran say about God being Al-Quddus (the Holy)?",
    "What does the Quran say about God being As-Salam (the Source of Peace)?",
    "What does the Quran say about God being Al-Mu'min (the Securer of Faith)?",
    "What does the Quran say about God being Al-Muhaymin (the Guardian)?",
    "What does the Quran say about God being Al-Aziz (the Almighty)?",
    "What does the Quran say about God being Al-Jabbar (the Compeller)?",
    "What does the Quran say about God being Al-Mutakabbir (the Supreme)?",
    "What does the Quran say about God being Al-Khaliq (the Creator)?",
    "What does the Quran say about God being Al-Bari (the Evolver)?",
    "What does the Quran say about God being Al-Musawwir (the Fashioner)?",
    "What does the Quran say about God being Al-Ghaffar (the Forgiver)?",
    "What does the Quran say about God being Al-Qahhar (the Subduer)?",
    "What does the Quran say about God being Al-Wahhab (the Bestower)?",
    "What does the Quran say about God being Ar-Razzaq (the Provider)?",
    "What does the Quran say about God being Al-Fattah (the Opener)?",
    "What does the Quran say about God being Al-Alim (the All-Knowing)?",
    "What does the Quran say about God being Al-Basir (the All-Seeing)?",
    "What does the Quran say about God being As-Sami (the All-Hearing)?",
    "What does the Quran say about God being Al-Hakim (the All-Wise)?",
    "What does the Quran say about God being Al-Adl (the Utterly Just)?",
    "What does the Quran say about God being Al-Latif (the Subtle)?",
    "What does the Quran say about God being Al-Khabir (the All-Aware)?",
    "What does the Quran say about God being Al-Halim (the Forbearing)?",
    "What does the Quran say about God being Al-Hayy (the Ever-Living)?",
    "What does the Quran say about God being Al-Qayyum (the Self-Subsisting)?",
    "What does the Quran say about God being Al-Wadud (the Loving)?",
    "What does the Quran say about God being Al-Haqq (the Truth)?",

    # ── Creation narrative (~20)
    "What does the Quran say about the original state before creation?",
    "What does the Quran say about the first heaven versus the seven heavens?",
    "What does the Quran teach about the throne (arsh) of God?",
    "What does the Quran say about the pen (qalam) and the preserved tablet (lawh mahfuz)?",
    "What does the Quran say about the creation of time and its markers?",
    "What does the Quran say about the creation of jinn from smokeless fire?",
    "What does the Quran say about angels and their hierarchies?",
    "What does the Quran say about the primordial clay of human creation?",
    "What does the Quran say about the breathing of God's spirit into Adam?",
    "What does the Quran say about Adam's instruction in the names of all things?",
    "What does the Quran say about the prostration of the angels to Adam?",
    "What does the Quran say about Iblis's refusal and self-comparison?",
    "What does the Quran say about the creation of the mate from Adam?",
    "What does the Quran say about the tree in the garden and God's warning?",
    "What does the Quran say about the descent of Adam and Eve to earth?",
    "What does the Quran say about the creation of clouds and rain cycles?",
    "What does the Quran say about the creation of pairs (male/female) in everything?",
    "What does the Quran say about life emerging from water?",
    "What does the Quran say about the day, night, and their alternation as creation?",
    "What does the Quran say about the earth being spread out for habitation?",

    # ── Specific sin categories (~20)
    "What does the Quran say about shirk — associating partners with God?",
    "What does the Quran say about murder and intentional killing?",
    "What does the Quran say about adultery and fornication?",
    "What does the Quran say about false accusations (qadhf)?",
    "What does the Quran say about theft and its punishment?",
    "What does the Quran say about highway robbery (haraba)?",
    "What does the Quran say about lying and false testimony?",
    "What does the Quran say about usury and interest?",
    "What does the Quran say about gambling and games of chance?",
    "What does the Quran say about intoxicants (khamr)?",
    "What does the Quran say about consuming forbidden foods (pig, blood, carrion)?",
    "What does the Quran say about breaking oaths and promises?",
    "What does the Quran say about pride as a sin?",
    "What does the Quran say about envy and its consequences?",
    "What does the Quran say about malice and hatred toward others?",
    "What does the Quran say about mocking or ridiculing others?",
    "What does the Quran say about spying and investigating others' private affairs?",
    "What does the Quran say about eating others' property wrongfully?",
    "What does the Quran say about oppression (zulm) in its various forms?",
    "What does the Quran say about abandoning the orphan and needy?",

    # ── Prayer / worship mechanics (~20)
    "What does the Quran say about the times when prayer is inappropriate?",
    "What does the Quran say about shortening prayer during fear?",
    "What does the Quran say about combining prayers during travel?",
    "What does the Quran say about the imam leading the prayer?",
    "What does the Quran say about dry ablution (tayammum) in absence of water?",
    "What does the Quran say about the opening of prayer with takbir?",
    "What does the Quran say about reciting Al-Fatihah in every prayer?",
    "What does the Quran say about bowing (ruku) and prostration (sujud)?",
    "What does the Quran say about silent versus audible recitation in prayer?",
    "What does the Quran say about making specific du'as within prayer?",
    "What does the Quran say about invoking God in times and places of distress?",
    "What does the Quran say about the value of a single prostration?",
    "What does the Quran say about praying for protection from evil?",
    "What does the Quran say about asking God for specific worldly needs?",
    "What does the Quran say about dhikr (remembrance) after prescribed prayers?",
    "What does the Quran say about the morning and evening remembrances?",
    "What does the Quran say about praying for one's parents?",
    "What does the Quran say about praying for one's spouse and offspring?",
    "What does the Quran say about prayer as a refuge from difficulty?",
    "What does the Quran say about maintaining prayer throughout life?",

    # ── Unique Quranic vocabulary (~20)
    "What does the Quranic word 'Kawthar' mean and where does it appear?",
    "What does the Quranic word 'Tasnim' mean (paradise spring)?",
    "What does the Quranic word 'Illiyyun' mean (record of the righteous)?",
    "What does the Quranic word 'Sijjin' mean (record of the wicked)?",
    "What does the Quranic word 'Barzakh' mean and how is it used?",
    "What does the Quranic word 'Sidrat al-Muntaha' mean?",
    "What does the Quranic phrase 'Ummul-Kitab' mean (mother of the book)?",
    "What does the Quranic word 'Ruh al-Qudus' refer to (Holy Spirit)?",
    "What does the Quranic word 'Sakinah' mean (tranquility from God)?",
    "What does the Quranic word 'Kalimatullah' mean (God's word)?",
    "What does the Quranic phrase 'Hablul-Matin' mean (strong rope)?",
    "What does the Quranic word 'Siraatal-Mustaqeem' mean (straight path)?",
    "What does the Quranic word 'Dhikr' encompass in the Quran?",
    "What does the Quranic word 'Furqan' mean (criterion)?",
    "What does the Quranic word 'Mulk' mean (dominion)?",
    "What does the Quranic word 'Rabb' mean versus 'Ilah'?",
    "What does the Quranic word 'Khalifah' mean (successor/representative)?",
    "What does the Quranic word 'Fatir' mean (originator)?",
    "What does the Quranic word 'Hanif' mean and who is associated with it?",
    "What does the Quranic word 'Aayat' encompass (signs and verses)?",

    # ── Submitter law — concrete situations (~20)
    "What does the Quran say about distributing zakat to 8 specific categories?",
    "What does the Quran say about the percentage of zakat on different wealth types?",
    "What does the Quran say about witnesses needed for a loan contract?",
    "What does the Quran say about the rights of a child in breastfeeding duration?",
    "What does the Quran say about the waiting period (iddah) after divorce?",
    "What does the Quran say about divorce pronouncements and their revocability?",
    "What does the Quran say about polygamy conditions and justice requirement?",
    "What does the Quran say about the dower (mahr) as a right of the woman?",
    "What does the Quran say about inheritance shares for sons and daughters?",
    "What does the Quran say about wills and their limits?",
    "What does the Quran say about adoption and calling children by their fathers' names?",
    "What does the Quran say about contracts and fulfilling agreements?",
    "What does the Quran say about just weights and measures in trade?",
    "What does the Quran say about slaves: freeing as righteousness?",
    "What does the Quran say about eating from others' houses when entering?",
    "What does the Quran say about seeking permission to enter private quarters?",
    "What does the Quran say about the times of privacy for sleeping rooms?",
    "What does the Quran say about hunting during pilgrimage?",
    "What does the Quran say about consumption of food sacrificed to idols?",
    "What does the Quran say about sea food versus land food for Muslims?",

    # ── Scripture of prior prophets (~15)
    "What does the Quran say about the Suhuf (scripture) of Abraham?",
    "What does the Quran say about the Tawrah (Torah) given to Moses?",
    "What does the Quran say about the Zabur (Psalms) given to David?",
    "What does the Quran say about the Injeel (Gospel) given to Jesus?",
    "What does the Quran say about the preservation of its own text?",
    "What does the Quran say about alterations to prior scripture?",
    "What does the Quran say about common themes in all divine scriptures?",
    "What does the Quran say about its confirmation of what preceded it?",
    "What does the Quran say about how God sent messengers to every nation?",
    "What does the Quran say about the language variation of each message?",
    "What does the Quran say about the duty of prior scripture holders to believe?",
    "What does the Quran say about hiding knowledge given in scripture?",
    "What does the Quran say about truth and guidance being sent as light?",
    "What does the Quran say about prior scripture describing the coming messenger?",
    "What does the Quran say about those who sold God's verses for a small price?",

    # ── Angels, jinn, souls (~20)
    "What does the Quran say about Gabriel (Jibril) specifically?",
    "What does the Quran say about Michael (Mikail)?",
    "What does the Quran say about Israfil and the trumpet?",
    "What does the Quran say about the angel of death (Malik al-Mawt)?",
    "What does the Quran say about the scribes on the shoulders (kiraman katibin)?",
    "What does the Quran say about the angels who ask 'why did you die in this state'?",
    "What does the Quran say about Malik the keeper of hell?",
    "What does the Quran say about the guardians of paradise?",
    "What does the Quran say about Iblis and his nature as jinn?",
    "What does the Quran say about jinn who believed versus those who did not?",
    "What does the Quran say about Solomon's authority over jinn?",
    "What does the Quran say about witchcraft and the two angels of Babylon?",
    "What does the Quran say about the three types of nafs (ammarah/lawwamah/mutma'inna)?",
    "What does the Quran say about the taking of the soul at death?",
    "What does the Quran say about the journey of the soul after death?",
    "What does the Quran say about intermediate state before resurrection?",
    "What does the Quran say about dreams as partial reveals?",
    "What does the Quran say about sleep being a taking of the soul?",
    "What does the Quran say about the soul being more than the body?",
    "What does the Quran say about the soul hearing the call of God?",

    # ── Modern-day applications (~15)
    "What does the Quran say about the ethical use of technology and media?",
    "What does the Quran say about global environmental stewardship?",
    "What does the Quran say about treating people of other faiths today?",
    "What does the Quran say about climate change in terms of corruption on land and sea?",
    "What does the Quran say about the ethics of scientific research?",
    "What does the Quran say about economic systems and just wealth distribution?",
    "What does the Quran say about organ donation in light of its principles?",
    "What does the Quran say about genetic engineering and altering creation?",
    "What does the Quran say about using social media ethically?",
    "What does the Quran say about food production and avoiding waste?",
    "What does the Quran say about mental health and spiritual well-being?",
    "What does the Quran say about the proper role of government?",
    "What does the Quran say about ethical investing and interest-free finance?",
    "What does the Quran say about how we consume information and opinions?",
    "What does the Quran say about the ethics of war in a nuclear era?",
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
    fresh = filter_new(PHASE8_RAW)
    print(f"[phase8] total={len(PHASE8_RAW)}, after dedup={len(fresh)}")
    sf = Path("overnight_seed.state.json")
    if sf.exists():
        try:
            st = json.loads(sf.read_text(encoding="utf-8"))
            st["done"] = [q for q in st.get("done", []) if q in fresh]
            st["failed"] = []
            sf.write_text(json.dumps(st, indent=2), encoding="utf-8")
            print(f"[phase8] state pruned to {len(st['done'])} matching done entries")
        except Exception as e:
            print(f"[phase8] state prune failed: {e}")
    engine.QUESTIONS = fresh
    engine.main()
