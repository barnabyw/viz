import matplotlib.font_manager as fm
import matplotlib.cm as cm
import matplotlib.colors as mcolors

# ===============================================================
# Fonts
# ===============================================================
font_dir = r"C:\Users\barna\AppData\Local\Microsoft\Windows\Fonts"

paths = {
    "regular": fr"{font_dir}\Montserrat-Regular.ttf",
    "medium": fr"{font_dir}\Montserrat-Medium.ttf",
    "semi":    fr"{font_dir}\Montserrat-SemiBold.ttf",
    "bold":    fr"{font_dir}\Montserrat-Bold.ttf",
}

for p in paths.values():
    fm.fontManager.addfont(p)

FONT_REGULAR   = fm.FontProperties(fname=paths["regular"])
FONT_MEDIUM    = fm.FontProperties(fname=paths["medium"])
FONT_SEMI_BOLD = fm.FontProperties(fname=paths["semi"])
FONT_BOLD      = fm.FontProperties(fname=paths["bold"])

small_font = 22
medium_font = 24
large_font = 27

# ===============================================================
# Colours
# ===============================================================
BLACK = "#000000"
DARK_GREY = "#373737"
CLOUD = "#C5C6D0"
BACKGROUND = "#FBFBFB"

# ---------------------------------------------------------------
# Custom gradients
# ---------------------------------------------------------------
CLEAN_COLORS = [
    "#edf8e9",  # very light green
    "#74c476",  # mid green
    "#006d2c",  # dark green
]

FOSSIL_COLORS = [
    "#ff9b9b",  # light vibrant red
    "#ef3b2c",  # mid strong red
    "#b10026",  # dark deep red
]

STACK_COLOURS = {
    "Solar": "#FFBB00",
    "Battery Discharge": "#0F9ED5",
    "Nuclear": "#F2F2F2",
    "Wind": "#E0E0E0",
    "Battery Charge": "#CDCDCD",
    "Other": "#D6D6D6",
    "Imports": "#BBBBBB",
    "Hydro": "#A7A7A7",
    "Gas": "#919191",
    "Unmet Demand": "#BBBBBB"
}

CLEAN_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "clean_green", CLEAN_COLORS
)

FOSSIL_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "fossil_red", FOSSIL_COLORS
)

# Tech → colour family
TECH_FAMILY = {
    "Solar+BESS": "clean",
    "Solar": "clean",
    "Wind": "clean",
    "Gas": "fossil",
    "Coal": "fossil",
}

COLORMAPS = {
    "clean": CLEAN_CMAP,
    "fossil": FOSSIL_CMAP,
}


def build_color_lookup(tech_years):
    """
    Returns {(tech, year): color}
    Darker = more recent year, normalised per family.
    """
    family_years = {}
    for s in tech_years:
        fam = TECH_FAMILY[s["tech"]]
        family_years.setdefault(fam, set()).add(s["year"])

    normalisers = {
        fam: mcolors.Normalize(vmin=min(yrs), vmax=max(yrs))
        for fam, yrs in family_years.items()
    }

    lookup = {}
    for s in tech_years:
        tech, year = s["tech"], s["year"]
        fam = TECH_FAMILY[tech]
        cmap = COLORMAPS[fam]
        norm = normalisers[fam]

        # Avoid extreme ends of the colormap
        t = 0.35 + 0.55 * norm(year)
        lookup[(tech, year)] = cmap(t)

    return lookup
