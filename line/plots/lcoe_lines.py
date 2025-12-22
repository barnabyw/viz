import pandas as pd
import os
import time
import matplotlib.pyplot as plt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from line.utils import build_chart_name, mpl_text
from line.style.config import TECH_RENDER, TECH_LABEL_MODE
from line.structure.lcoe_chart import draw_lcoe_chart
from line.style.styling import (
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
# Figure
# -------------------------------------------------
DPI = 100
fig = plt.figure(figsize=(1920 / DPI, 1080 / DPI), dpi=DPI)
fig.patch.set_facecolor(BACKGROUND)

ax = fig.add_subplot(1, 1, 1)
ax.set_facecolor(BACKGROUND)

fig.subplots_adjust(
    left=0.08,
    right=0.8,
    top=0.80,
    bottom=0.14,
)

# -------------------------------------------------
# Draw chart
# -------------------------------------------------
draw_lcoe_chart(
    ax=ax,
    df=df,
    tech_years=TECH_YEARS,
    default_fossil_lf=DEFAULT_FOSSIL_LF,
    tech_render=TECH_RENDER,
    tech_label_mode=TECH_LABEL_MODE,
    ylims=ylims,
    y_tick_step=50,
)

# -------------------------------------------------
# Titles
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

ax.set_xlabel(
    "Load factor",
    fontproperties=FONT_REGULAR,
    fontsize=small_font,
    color=DARK_GREY,
    labelpad=14,
)

# -------------------------------------------------
# Save
# -------------------------------------------------
name = build_chart_name(COUNTRY, TECH_YEARS)
output_path = fr"C:\Users\barna\OneDrive\Documents\Solar_BESS\Good charts\video\{name}.png"

fig.savefig(
    output_path,
    dpi=300,
    facecolor=fig.get_facecolor(),
)

time.sleep(0.3)
os.startfile(output_path)
