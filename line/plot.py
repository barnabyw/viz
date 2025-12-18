import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm

# ===============================================================
# CONFIGURATION
# ===============================================================
COUNTRY = "China"
TITLE = f"In the {COUNTRY}, cheap gas is similar cost to standalone solar"

# ---------------------------
# Default fossil assumptions
# ---------------------------
DEFAULT_FOSSIL_LF = [0.7]  # availability used as load factor

# ---------------------------
# Tech-years (user-facing)
# ---------------------------
TECH_YEARS = [
    {"tech": "Solar+BESS", "year": 2015},
    {"tech": "Solar+BESS", "year": 2025},
    {"tech": "Gas",        "year": 2025},              # uses default LF
    # {"tech": "Gas",      "year": 2025, "lf": [0.5]}, # override example
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

# ===============================================================
# FONTS
# ===============================================================
font_dir = r"C:\Users\barna\AppData\Local\Microsoft\Windows\Fonts"

paths = {
    "regular": fr"{font_dir}\Montserrat-Regular.ttf",
    "medium": fr"{font_dir}\Montserrat-Medium.ttf",
    "semi": fr"{font_dir}\Montserrat-SemiBold.ttf",
    "bold": fr"{font_dir}\Montserrat-Bold.ttf",
}

for p in paths.values():
    fm.fontManager.addfont(p)

FONT_REGULAR   = fm.FontProperties(fname=paths["regular"])
FONT_MEDIUM    = fm.FontProperties(fname=paths["medium"])
FONT_SEMI_BOLD = fm.FontProperties(fname=paths["semi"])
FONT_BOLD      = fm.FontProperties(fname=paths["bold"])

small_text  = 15
medium_text = 17
title_size  = 22

# ===============================================================
# LOAD DATA
# ===============================================================
df = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_results.csv"
)
df = df[df["Country"] == COUNTRY]

# ===============================================================
# NORMALISE TECH-YEARS (internal only)
# ===============================================================
NORMALISED_TECH_YEARS = []

for t in TECH_YEARS:
    tech = t["tech"]
    year = t["year"]

    if tech in ["Gas", "Coal"]:
        lfs = t.get("lf", DEFAULT_FOSSIL_LF)
        for lf in lfs:
            NORMALISED_TECH_YEARS.append(
                {"tech": tech, "year": year, "lf": lf}
            )
    else:
        NORMALISED_TECH_YEARS.append(
            {"tech": tech, "year": year, "lf": None}
        )

# ===============================================================
# HELPERS
# ===============================================================
def fossil_lcoe_at_lf(df, tech, year, lf):
    """Uses Availability as load factor proxy."""
    subset = df[(df["Tech"] == tech) & (df["Year"] == year)]
    idx = (subset["Availability"] - lf).abs().idxmin()
    return subset.loc[idx, "LCOE"]


def curve_label_properties_display(ax, x, y, x_center=0.6, dx=0.05, offset_px=20):
    x = np.asarray(x)
    y = np.asarray(y)

    x1, x2 = x_center - dx, x_center + dx
    y1 = np.interp(x1, x, y)
    y2 = np.interp(x2, x, y)
    yc = np.interp(x_center, x, y)

    p1 = ax.transData.transform((x1, y1))
    p2 = ax.transData.transform((x2, y2))

    v = p2 - p1
    angle = np.degrees(np.arctan2(v[1], v[0]))

    n = np.array([-v[1], v[0]])
    n /= np.linalg.norm(n)

    pc = ax.transData.transform((x_center, yc))
    pl = pc + n * offset_px

    return *ax.transData.inverted().transform(pl), angle

# ===============================================================
# PRECOMPUTE FOSSIL LCOE
# ===============================================================
FOSSIL_LCOE = {}

for s in NORMALISED_TECH_YEARS:
    if s["tech"] in ["Gas", "Coal"]:
        FOSSIL_LCOE[(s["tech"], s["year"], s["lf"])] = fossil_lcoe_at_lf(
            df, s["tech"], s["year"], s["lf"]
        )

# ===============================================================
# STYLING
# ===============================================================
COLOR_MAP = {
    ("Solar+BESS", 2015): "#93C993",
    ("Solar+BESS", 2025): "#2F7A2F",
    ("Gas", 2025): "#7A7A7A",
}

BLACK = "#000000"
DARK_GREY = "#373737"
CLOUD = "#C5C6D0"

# ===============================================================
# FIGURE
# ===============================================================
DPI = 100
fig, ax = plt.subplots(figsize=(1920 / DPI, 1080 / DPI), dpi=DPI)

fig.subplots_adjust(left=0.08, right=0.85, top=0.84, bottom=0.14)

fig.text(
    0.05, 0.91,
    TITLE,
    fontproperties=FONT_SEMI_BOLD,
    fontsize=title_size,
    color=BLACK,
    ha="left"
)

fig.text(
    0.05, 0.875,
    "Levelised cost of electricity ($/MWh)",
    fontproperties=FONT_REGULAR,
    fontsize=medium_text,
    color=DARK_GREY,
    ha="left"
)

fig.patch.set_facecolor("#FBFBFB")
ax.set_facecolor("#FBFBFB")

ax.set_xlim(0.05, 1.0)
ax.margins(x=0)
ax.set_ylim(0, 160)

ax.hlines(np.arange(0, 160, 20), *ax.get_xlim(), color=CLOUD, lw=0.6)

# ===============================================================
# PLOT
# ===============================================================
LW_MAIN = 2.6
HLINE_LABEL_X = 1.01

for s in NORMALISED_TECH_YEARS:
    tech, year, lf = s["tech"], s["year"], s["lf"]
    color = COLOR_MAP[(tech, year)]

    if TECH_RENDER[tech] == "curve":
        data = df[(df["Tech"] == tech) & (df["Year"] == year)]
        data = data.sort_values("Availability")

        x_vals = data["Availability"].values
        y_vals = data["LCOE"].values

        ax.plot(x_vals, y_vals, lw=LW_MAIN, color=color, zorder=3)
        x, y, angle = curve_label_properties_display(ax, x_vals, y_vals)

        label = f"{tech} {year}"

    else:
        y = FOSSIL_LCOE[(tech, year, lf)]
        ax.hlines(y, *ax.get_xlim(), lw=LW_MAIN, color=color, zorder=2)
        x, angle = HLINE_LABEL_X, 0

        label = f"{tech} {year} – {int(lf * 100)}% LF"

    ax.text(
        x,
        y,
        label,
        fontproperties=FONT_SEMI_BOLD,
        fontsize=medium_text,
        color=color,
        rotation=angle,
        rotation_mode="anchor",
        va="center",
        ha="left"
    )

# ===============================================================
# AXES
# ===============================================================
ax.set_xlabel("Load factor", fontproperties=FONT_REGULAR, fontsize=small_text, color=DARK_GREY)

x_ticks = np.arange(0.1, 1.01, 0.1)
ax.set_xticks(x_ticks)
ax.set_xticklabels(
    [f"{int(x * 100)}%" for x in x_ticks],
    fontproperties=FONT_REGULAR,
    fontsize=small_text,
    color=DARK_GREY
)

ax.spines["bottom"].set_color(DARK_GREY)
ax.spines["bottom"].set_linewidth(1.2)
ax.tick_params(axis="x", length=10, width=1.2, color=DARK_GREY)

ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

for label in ax.get_yticklabels():
    label.set_fontproperties(FONT_REGULAR)
    label.set_fontsize(small_text)
    label.set_color(DARK_GREY)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.show()
