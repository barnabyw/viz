import pandas as pd
import os
import time
import matplotlib.pyplot as plt

from utils import build_chart_name, mpl_text
from config import TECH_RENDER, TECH_LABEL_MODE
from lcoe_chart import draw_lcoe_chart
from styling import (
    BACKGROUND, FONT_SEMI_BOLD, FONT_REGULAR,
    DARK_GREY, large_font, medium_font, small_font
)

COUNTRY = "Spain"
TITLE_RAW = f"{COUNTRY} in 2025: solar and BESS costs have declined fast"

DEFAULT_FOSSIL_LF = [0.7]

TECH_YEARS = [
    {"tech": "Solar+BESS", "year": 2015},
    {"tech": "Solar+BESS", "year": 2025},
    {"tech": "Gas",        "year": 2015},
]

ylims = (0, 150)

# -------------------------------------------------
# Load data
# -------------------------------------------------
df = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_results.csv"
)
df = df[df["Country"] == COUNTRY]

TITLE = mpl_text(TITLE_RAW)

# -------------------------------------------------
# Figure + layout
# -------------------------------------------------
DPI = 100
fig = plt.figure(figsize=(1920 / DPI, 1080 / DPI), dpi=DPI)
fig.patch.set_facecolor(BACKGROUND)

gs = fig.add_gridspec(
    nrows=2,
    ncols=1,
    height_ratios=[1, 1],
    left=0.08,
    right=0.8,
    top=0.80,
    bottom=0.14,
    hspace=0.20, # space between
)

ax_top = fig.add_subplot(gs[0, 0])
ax_bottom = fig.add_subplot(gs[1, 0])

ax_top.set_facecolor(BACKGROUND)
ax_bottom.set_facecolor(BACKGROUND)

# -------------------------------------------------
# Draw charts
# -------------------------------------------------
draw_lcoe_chart(
    ax=ax_top,
    df=df,
    tech_years=TECH_YEARS,
    default_fossil_lf=DEFAULT_FOSSIL_LF,
    tech_render=TECH_RENDER,
    tech_label_mode=TECH_LABEL_MODE,
    ylims=ylims,
    y_tick_step=50,
)

draw_lcoe_chart(
    ax=ax_bottom,
    df=df,
    tech_years=TECH_YEARS,
    default_fossil_lf=DEFAULT_FOSSIL_LF,
    tech_render=TECH_RENDER,
    tech_label_mode=TECH_LABEL_MODE,
    ylims=ylims,
    y_tick_step=50,
)

# -------------------------------------------------
# Titles & labels
# -------------------------------------------------
fig.text(
    0.05, 0.91,
    TITLE,
    fontproperties=FONT_SEMI_BOLD,
    fontsize=large_font,
    ha="left"
)

fig.text(
    0.05, 0.87,
    "Levelised cost of electricity ($/MWh)",
    fontproperties=FONT_REGULAR,
    fontsize=medium_font,
    color=DARK_GREY
)

ax_bottom.set_xlabel(
    "Load factor",
    fontproperties=FONT_REGULAR,
    fontsize=small_font,
    color=DARK_GREY,
    labelpad=14,
)

ax_top.set_xticklabels([])
ax_top.tick_params(axis="x", length=0)

# -------------------------------------------------
# Save
# -------------------------------------------------
name = build_chart_name(COUNTRY, TECH_YEARS)
output_path = fr"C:\Users\barna\OneDrive\Documents\Solar_BESS\Good charts\video\{name}_double.png"

fig.savefig(
    output_path,
    dpi=300,
    facecolor=fig.get_facecolor(),
)

time.sleep(0.3)
os.startfile(output_path)
