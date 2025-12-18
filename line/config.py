COUNTRY = "Spain"
TITLE = f"In {COUNTRY}, solar and BESS can compete with gas for more than 70% of demand"

DEFAULT_FOSSIL_LF = [0.7]

TECH_YEARS = [
    {"tech": "Solar+BESS", "year": 2015},
    {"tech": "Solar+BESS", "year": 2025},
    {"tech": "Gas",        "year": 2025},
    {"tech": "Gas", "year": 2015},
]

TECH_RENDER = {
    "Solar+BESS": "curve",
    "Gas": "horizontal",
    "Coal": "horizontal",
}

TECH_LABEL_MODE = {
    "Solar+BESS": "angled",
    "Gas": "end",
    "Coal": "end",
}
