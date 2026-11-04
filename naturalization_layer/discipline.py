"""Discipline clusters and the keyword fallback classifier (single source of truth)."""

DISCIPLINES = ("SCI_TECH", "AUTOMATION_CONTROL", "AGRI_MED", "HUM_POL_ECON", "ARTS_SPORTS", "UNIVERSAL")

# Checked in order; first match wins. Russian stems + English keywords.
_KEYWORDS = (
    ("AUTOMATION_CONTROL", ("управление", "робот", "автоматиз", "регулятор", "динамик",
                            "control", "robot", "automat", "cybernetic", "feedback")),
    ("AGRI_MED", ("биолог", "медиц", "клетк", "терап", "ген",
                  "biolog", "medic", "cell", "gene", "patient", "clinical", "dna", "rna")),
    ("SCI_TECH", ("физик", "хими", "сплав", "материал", "энерг",
                  "physic", "chemic", "material", "alloy", "thermodynamic", "mechanic")),
    ("HUM_POL_ECON", ("эконом", "полити", "гуманитар", "истори", "обществ",
                      "econom", "polit", "social", "humanit", "history", "societ")),
    ("ARTS_SPORTS", ("искусств", "спорт", "культур", "музык",
                     "art", "sport", "cultur", "music", "athlet", "paint")),
)


def detect_discipline_by_keywords(text: str) -> str:
    text_lower = text.lower()
    for discipline, words in _KEYWORDS:
        if any(w in text_lower for w in words):
            return discipline
    return "UNIVERSAL"
