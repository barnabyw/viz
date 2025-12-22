import pandas as pd
import os
import time
import matplotlib.pyplot as plt

from utils import build_chart_name, mpl_text
from config import TECH_RENDER, TECH_LABEL_MODE
from lcoe_chart import draw_lcoe_chart, draw_generation_stack_chart
from line.lcoe_chart import draw_capacity_cluster_chart
from styling import (
    BACKGROUND,
    FONT_SEMI_BOLD,
    FONT_REGULAR,
    DARK_GREY,
    large_font,
    medium_font,
    small_font,
)
from prep_stack import load_typical_week_by_availability
from variable_map import VARIABLE_MAP

# ===============================================================
# Configuration
# ===============================================================
COUNTRY = "Spain"
TITLE_RAW = f"{COUNTRY} in 2025: solar and BESS costs have declined fast"

DEFAULT_FOSSIL_LF = [0.7]

TECH_YEARS = [
    {"tech": "Solar+BESS", "year": 2015},
    {"tech": "Solar+BESS", "year": 2025},
    {"tech": "Gas",        "year": 2015},
]

LCOE_YLIMS = (0, 150)

# ===============================================================
# Load LCOE data
# ===============================================================
df_lcoe = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_results.csv"
)
df_lcoe = df_lcoe[df_lcoe["Country"] == COUNTRY]

# ===============================================================
# Load & prepare stack data (precomputed views)
# ===============================================================
typical_week_by_avail = load_typical_week_by_availability(
    country=COUNTRY,
    path=r"C:\Users\barna\PycharmProjects\solar_bess\outputs\long_timeseries_Spain.csv",
    variable_map=VARIABLE_MAP,
    anchor_year=2023,
)

avail = 0.75
week_df = typical_week_by_avail[avail]

# ===============================================================
# Figure + layout
# ===============================================================
DPI = 100
fig = plt.figure(figsize=(1920 / DPI, 1620 / DPI), dpi=DPI)
fig.patch.set_facecolor(BACKGROUND)

gs = fig.add_gridspec(
    nrows=3,
    ncols=1,
    height_ratios=[1.2, 1.0, 1.0],
    left=0.08,
    right=0.80,
    top=0.90,
    bottom=0.08,
    hspace=0.30,
)

ax_top = fig.add_subplot(gs[0, 0])
ax_mid = fig.add_subplot(gs[1, 0])
ax_bot = fig.add_subplot(gs[2, 0])

for ax in (ax_top, ax_mid, ax_bot):
    ax.set_facecolor(BACKGROUND)

# ===============================================================
# Draw charts
# ===============================================================

# --- Top: Generation stack ---
draw_generation_stack_chart(
    ax=ax_top,
    stack_df=week_df,
    order=["Solar", "Battery Discharge", "Unmet Demand"],
    unit="MW",
)

ax_top.set_title(
    f"Typical weekly dispatch (availability {avail:.0%})",
    fontproperties=FONT_SEMI_BOLD,
    fontsize=medium_font,
    color=DARK_GREY,
    loc="left",
    pad=10,
)

ax_top.set_xlabel(
    "Time (typical week)",
    fontproperties=FONT_REGULAR,
    fontsize=small_font,
    color=DARK_GREY,
    labelpad=10,
)

# --- Middle: Capacity cluster ---
draw_capacity_cluster_chart(
    ax=ax_mid,
    df=df_lcoe,
    tech_years=TECH_YEARS,
    ylims_power=(0, 20),
    y_tick_step_power=10,
    ylims_duration=(0, 90),
    y_tick_step_duration=30,
    bar_width=0.012,
)

ax_mid.set_title(
    "Installed solar and storage capacity",
    fontproperties=FONT_SEMI_BOLD,
    fontsize=medium_font,
    color=DARK_GREY,
    loc="left",
    pad=10,
)

ax_mid.set_xlabel(
    "Load factor",
    fontproperties=FONT_REGULAR,
    fontsize=small_font,
    color=DARK_GREY,
    labelpad=10,
)

# --- Bottom: LCOE ---
draw_lcoe_chart(
    ax=ax_bot,
    df=df_lcoe,
    tech_years=TECH_YEARS,
    default_fossil_lf=DEFAULT_FOSSIL_LF,
    tech_render=TECH_RENDER,
    tech_label_mode=TECH_LABEL_MODE,
    ylims=LCOE_YLIMS,
    y_tick_step=50,
)

ax_bot.set_title(
    "Levelised cost of electricity",
    fontproperties=FONT_SEMI_BOLD,
    fontsize=medium_font,
    color=DARK_GREY,
    loc="left",
    pad=10,
)

ax_bot.set_xlabel(
    "Load factor",
    fontproperties=FONT_REGULAR,
    fontsize=small_font,
    color=DARK_GREY,
    labelpad=12,
)

# ===============================================================
# Figure title
# ===============================================================
TITLE = mpl_text(TITLE_RAW)

fig.text(
    0.05,
    0.95,
    TITLE,
    fontproperties=FONT_SEMI_BOLD,
    fontsize=large_font,
    ha="left",
)

# ===============================================================
# Save
# ===============================================================
name = build_chart_name(COUNTRY, TECH_YEARS)
output_path = fr"C:\Users\barna\OneDrive\Documents\Solar_BESS\Good charts\video\{name}_triple.png"

fig.savefig(
    output_path,
    dpi=300,
    facecolor=fig.get_facecolor(),
)

time.sleep(0.3)
os.startfile(output_path)
