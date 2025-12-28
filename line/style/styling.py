import matplotlib.font_manager as fm
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import numpy as np

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
    "Battery Charge": "#8FD3F4",   # lighter blue
    "Curtailment": "#FFE08A",      # lighter yellow
    "Other": "#D6D6D6",
    "Imports": "#BBBBBB",
    "Hydro": "#A7A7A7",
    "Gas": "#919191",
    "Unmet Demand": "#BBBBBB",
}

component_colors = {
    # Direct inheritance from stack
    "Solar CAPEX": STACK_COLOURS["Solar"],
    "BESS Energy CAPEX": STACK_COLOURS["Battery Discharge"],

    # Variant of BESS colour
    "BESS Power CAPEX": "#00316E",

    # Cost-only components (explicit semantic colours)
    "Augmentation": "#E377C2", # "#DD8452",   # pink / salmon
    "Opex": "#E377C2",           # pink
}

capacity_colors = {
    "Solar": STACK_COLOURS["Solar"],
    "BESS Energy": STACK_COLOURS["Battery Discharge"],
    "BESS Power": component_colors["BESS Power CAPEX"]
}

GREENS = {
    2030: "#4CAF50", 2025: "#66BB6A", 2020: "#81C784", 2015: "#A5D6A7"
}

REDS = {
    2030: "#a70000", 2025: "#FF474D", 2020: "#ff5252", 2015: "#ff7b7b" # ff2e2e
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

def lerp_color(c1, c2, t):
    c1 = np.array(mcolors.to_rgb(c1))
    c2 = np.array(mcolors.to_rgb(c2))
    return tuple(c1 + t * (c2 - c1))

def year_colors(anchor):
    years = sorted(anchor)
    out = {}

    for y in range(years[0], years[-1] + 1):
        if y in anchor:
            out[y] = mcolors.to_rgb(anchor[y])
        else:
            y0 = max(yr for yr in years if yr < y)
            y1 = min(yr for yr in years if yr > y)
            t = (y - y0) / (y1 - y0)
            out[y] = lerp_color(anchor[y0], anchor[y1], t)

    return out

CLEAN_YEARS  = year_colors(GREENS)
FOSSIL_YEARS = year_colors(REDS)

def build_color_lookup(tech_years):
    return {
        (s["tech"], s["year"]):
            (CLEAN_YEARS if TECH_FAMILY[s["tech"]] == "clean" else FOSSIL_YEARS)[s["year"]]
        for s in tech_years
    }
