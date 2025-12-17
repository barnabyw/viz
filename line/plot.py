import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm

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

# ---------------------------
# Load and filter data
# ---------------------------
df_raw = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_results.csv"
)

df = df_raw.copy()

COUNTRY = "United States"
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
    n = n / np.linalg.norm(n)

    pc = ax.transData.transform((x_center, yc))
    pl = pc + n * offset_px

    x_lab, y_lab = ax.transData.inverted().transform(pl)

    return x_lab, y_lab, angle

# ---------------------------
# Figure (1920x1080)
# ---------------------------
DPI = 100
fig, ax = plt.subplots(figsize=(1920 / DPI, 1080 / DPI), dpi=DPI)

fig.subplots_adjust(left=0.08, right=0.85, top=0.88, bottom=0.12)

# ---------------------------
# Title & subtitle
# ---------------------------
fig.text(
    0.04, 0.94,
    COUNTRY,
    fontproperties=FONT_SEMI_BOLD,
    fontsize=22,
    color=BLACK,
    ha="left",
    va="bottom"
)

fig.text(
    0.04, 0.905,
    "Levelised cost of electricity ($/MWh)",
    fontproperties=FONT_REGULAR,
    fontsize=14,
    color=DARK_GREY,
    ha="left",
    va="bottom"
)

fig.patch.set_facecolor("#FBFBFB")
ax.set_facecolor("#FBFBFB")

ax.set_xlim(0.05, 1.0)
ax.margins(x=0)
ax.set_ylim(0, 160)

# ---------------------------
# Gridlines
# ---------------------------
ax.hlines(np.arange(0, 160, 20), 0, 1.05, color=CLOUD, lw=0.6, zorder=0)
#ax.vlines(np.arange(0, 1.05, 0.1), 0, 160, color=CLOUD, lw=0.6, zorder=0)

# ---------------------------
# Plot lines + labels
# ---------------------------
LW_MAIN = 2.6
LABEL_X_PAD = 0.02

for (tech, year), data in groups:
    color = COLOR_MAP[(tech, year)]
    mode = TECH_RENDER[tech]
    label_mode = TECH_LABEL_MODE[tech]

    if mode == "curve":
        data = data.sort_values("Availability")
        x_vals = data["Availability"].values
        y_vals = data["LCOE"].values

        ax.plot(x_vals, y_vals, lw=LW_MAIN, color=color, zorder=3)

        x, y, angle = curve_label_properties_display(
            ax, x_vals, y_vals, offset_px=20
        )

    else:
        y = REFERENCE_LCOE[(tech, year)]
        ax.hlines(y, 0, 1.05, lw=LW_MAIN, color=color, zorder=2)
        x, angle = 1.05, 0

    ax.text(
        x + (LABEL_X_PAD if label_mode == "end" else 0),
        y,
        f"{tech} {year}",
        fontproperties=FONT_BOLD,
        fontsize=13,
        color=color,
        rotation=angle,
        rotation_mode="anchor",
        va="center",
        ha="left" if label_mode == "end" else "center"
    )

# ---------------------------
# Axes styling (fonts!)
# ---------------------------
ax.set_xlabel("Availability", fontproperties=FONT_MEDIUM, fontsize=13, color=DARK_GREY)
x_ticks = np.arange(0, 1.01, 0.1)

ax.set_xticks(x_ticks)
ax.set_xticklabels(
    [f"{int(x * 100)}%" for x in x_ticks],
    fontproperties=FONT_MEDIUM,
    fontsize=13,
    color=DARK_GREY
)

# Stronger x-axis line
ax.spines["bottom"].set_color(DARK_GREY)
ax.spines["bottom"].set_linewidth(1.2)

# Stronger x ticks
ax.tick_params(
    axis="x",
    length=10,
    width=1.2,
    color=DARK_GREY
)

for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontproperties(FONT_MEDIUM)
    label.set_fontsize(12)
    label.set_color(DARK_GREY)

ax.tick_params(axis="x", length=8, color=DARK_GREY)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_color(DARK_GREY)

plt.show()
