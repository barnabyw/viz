import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm

COUNTRY = "China"
title = f"In the {COUNTRY}, cheap gas is similar cost to standalone solar"

# ---------------------------
# Fonts
# ---------------------------
font_dir = r"C:\Users\barna\AppData\Local\Microsoft\Windows\Fonts"

regular_path = fr"{font_dir}\Montserrat-Regular.ttf"
medium_path  = fr"{font_dir}\Montserrat-Medium.ttf"
semi_bold_path = fr"{font_dir}\Montserrat-SemiBold.ttf"
bold_path    = fr"{font_dir}\Montserrat-Bold.ttf"

fm.fontManager.addfont(regular_path)
fm.fontManager.addfont(medium_path)
fm.fontManager.addfont(bold_path)
fm.fontManager.addfont(semi_bold_path)

FONT_REGULAR = fm.FontProperties(fname=regular_path)
FONT_MEDIUM  = fm.FontProperties(fname=medium_path)
FONT_BOLD    = fm.FontProperties(fname=bold_path)
FONT_SEMI_BOLD = fm.FontProperties(fname=semi_bold_path)

small_text = 15
medium_text = 17
title_size = 22

# ---------------------------
# Load and filter data
# ---------------------------
df_raw = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_results.csv"
)
df = df_raw.copy()
df = df[df["Country"] == COUNTRY]

TECH_YEARS = [
    ("Solar+BESS", 2015),
    ("Solar+BESS", 2025),
    ("Gas", 2025),
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

REFERENCE_LCOE = (
    df[df["Tech"].isin(["Gas", "Coal"])]
    .groupby(["Tech", "Year"])["LCOE"]
    .mean()
    .to_dict()
)

df["scenario"] = list(zip(df["Tech"], df["Year"]))
df = df[df["scenario"].isin(TECH_YEARS)]
groups = df.groupby(["Tech", "Year"])

# ---------------------------
# Styling
# ---------------------------
COLOR_MAP = {
    ("Solar+BESS", 2015): "#3969AC",
    ("Solar+BESS", 2025): "#11A579",
    ("Gas", 2025): "#E73F74",
}

BLACK = "#000000"
DARK_GREY = "#373737"
CLOUD = "#C5C6D0"

# ---------------------------
# Label helper
# ---------------------------
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

# ---------------------------
# Figure (1920x1080)
# ---------------------------
DPI = 100
fig, ax = plt.subplots(figsize=(1920 / DPI, 1080 / DPI), dpi=DPI)

fig.subplots_adjust(
    left=0.08,
    right=0.85,
    top=0.84,     # ⬅ compressed downward
    bottom=0.14
)

# ---------------------------
# Title & subtitle (lowered)
# ---------------------------
fig.text(
    0.05, 0.91,
    title,
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

# ---------------------------
# Gridlines (horizontal only)
# ---------------------------
ax.hlines(np.arange(0, 160, 20), *ax.get_xlim(), color=CLOUD, lw=0.6, zorder=0)

# ---------------------------
# Plot lines + labels
# ---------------------------
LW_MAIN = 2.6
LABEL_X_PAD = 0.015
HLINE_LABEL_X = 1.01  # ⬅ moved left

for (tech, year), data in groups:
    color = COLOR_MAP[(tech, year)]
    mode = TECH_RENDER[tech]
    label_mode = TECH_LABEL_MODE[tech]

    if mode == "curve":
        data = data.sort_values("Availability")
        x_vals = data["Availability"].values
        y_vals = data["LCOE"].values

        ax.plot(x_vals, y_vals, lw=LW_MAIN, color=color, zorder=3)
        x, y, angle = curve_label_properties_display(ax, x_vals, y_vals)

    else:
        y = REFERENCE_LCOE[(tech, year)]
        ax.hlines(y, *ax.get_xlim(), lw=LW_MAIN, color=color, zorder=2)
        x, angle = HLINE_LABEL_X, 0

    ax.text(
        x,
        y,
        f"{tech} {year}",
        fontproperties=FONT_SEMI_BOLD,
        fontsize=medium_text,
        color=color,
        rotation=angle,
        rotation_mode="anchor",
        va="center",
        ha="left"
    )

# ---------------------------
# X-axis styling
# ---------------------------
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

# Y-axis: labels only, no ticks or spine
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

for label in ax.get_yticklabels():
    label.set_fontproperties(FONT_REGULAR)
    label.set_fontsize(small_text)
    label.set_color(DARK_GREY)


ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.show()
