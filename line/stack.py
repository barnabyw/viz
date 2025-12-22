import pandas as pd
import os
import time
import matplotlib.pyplot as plt

from utils import mpl_text
from line.style.styling import (
    BACKGROUND,
    FONT_SEMI_BOLD,
    FONT_REGULAR,
    DARK_GREY,
    large_font,
    medium_font,
    small_font,
)

from line.structure.lcoe_chart import draw_capacity_stack_chart  # wherever you put it


# ======================================================
# Settings
# ======================================================
COUNTRY = "United States"
TITLE_RAW = f"{COUNTRY} – Solar + BESS capacity build-out vs load factor"

TECH_YEARS = [
    {"tech": "Solar+BESS", "year": 2015},
]

ylims = (0,100)  # or e.g. (0, 25)


# ======================================================
# Load data
# ======================================================
df = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_results.csv"
)
df = df[df["Country"] == COUNTRY]

TITLE = mpl_text(TITLE_RAW)


# ======================================================
# Figure
# ======================================================
DPI = 100
fig = plt.figure(figsize=(1920 / DPI, 1080 / DPI), dpi=DPI)
fig.patch.set_facecolor(BACKGROUND)

ax = fig.add_subplot(1, 1, 1)
ax.set_facecolor(BACKGROUND)

fig.subplots_adjust(
    left=0.08,
    right=0.92,
    top=0.82,
    bottom=0.16,
)


# ======================================================
# Draw chart
# ======================================================
draw_capacity_stack_chart(
    ax=ax,
    df=df,
    tech_years=TECH_YEARS,
    ylims=ylims,
    y_tick_step=10
)


# ======================================================
# Titles & labels
# ======================================================
fig.text(
    0.05, 0.92,
    TITLE,
    fontproperties=FONT_SEMI_BOLD,
    fontsize=large_font,
    ha="left",
)

fig.text(
    0.05, 0.88,
    "Stacked installed capacities (Solar + BESS)",
    fontproperties=FONT_REGULAR,
    fontsize=medium_font,
    color=DARK_GREY,
)

ax.set_xlabel(
    "Load factor",
    fontproperties=FONT_REGULAR,
    fontsize=small_font,
    color=DARK_GREY,
    labelpad=14,
)


# ======================================================
# Save & show
# ======================================================
output_path = (
    r"C:\Users\barna\OneDrive\Documents\Solar_BESS\Good charts"
    r"\capacity_stack_debug.png"
)

fig.savefig(
    output_path,
    dpi=300,
    facecolor=fig.get_facecolor(),
)

time.sleep(0.3)
os.startfile(output_path)
