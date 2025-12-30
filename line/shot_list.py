COUNTRY = "Spain"
TITLE_RAW = f"{COUNTRY} in 2015: 70% load factor solar and bess would've been financial madness"

DEFAULT_FOSSIL_LF = [0.7]

TECH_YEARS = [
    {"tech": "Solar+BESS", "year": 2015},
    {"tech": "Gas",        "year": 2015},
]

#==
COUNTRY = "Spain"
TITLE_RAW = f"{COUNTRY} in 2025: solar and bess costs have declined fast"

DEFAULT_FOSSIL_LF = [0.7]

TECH_YEARS = [
    {"tech": "Solar+BESS", "year": 2015},
    {"tech": "Solar+BESS", "year": 2025},
    {"tech": "Gas",        "year": 2015},
]

ylims = (0,400)

# -------------------------------------------------
# 1 spain
# -------------------------------------------------
COUNTRY = "Spain"

TITLE_RAW = f"Solar and BESS costs have declined 80% in 10 years"

tag = "1.g"

line_tech_years = [
    #{"tech": "Solar+BESS", "year": 2025, "highlight": True},
    #{"tech": "Solar+BESS", "year": 2020},
    {"tech": "Solar+BESS", "year": 2015, "highlight": True},
    {"tech": "Solar+BESS", "year": 2025, "highlight": True},
    {"tech": "Gas", "year": 2015, "highlight": True},
    {"tech": "Gas", "year": 2025, "highlight": True},
    #{"tech": "Gas", "year": 2015, "highlight": True} #, "label_pos": "above", "label_anchor": "end"}
]

component_tech_years = None #[{"tech": "Solar+BESS", "year": 2015}] # None

LCOE_YLIMS = (0, 350)

