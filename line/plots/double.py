import pandas as pd
import os
import time
import matplotlib.pyplot as plt
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from line.utils import build_chart_name, mpl_text, draw_dashboard_callout
from line.style.config import TECH_RENDER, TECH_LABEL_MODE, POSITIVE, NEGATIVE
from line.style.styling import (
    BACKGROUND,
    FONT_SEMI_BOLD,
    FONT_REGULAR,
    DARK_GREY,
    large_font,
    medium_font,
    small_font,
    STACK_COLOURS,
    component_colors,
    capacity_colors
)
from line.structure.lcoe_chart import (
    draw_lcoe_chart,
    draw_generation_stack_chart,
    draw_capacity_cluster_chart,
)

from line.structure.prep_stack import load_typical_week_by_availability
from line.variable_map import VARIABLE_MAP

# ===============================================================
# Configuration
# ===============================================================
COUNTRY = "Spain"
TITLE_RAW = f"Optimising costs to meet given load factors with solar and BESS"

AVAIL = 1

year = 2015

TECH_YEARS = [
    {"tech": "Solar+BESS", "year": year},
]

LCOE_YLIMS = (0, 500)

# ===============================================================
# Load LCOE data
# ===============================================================
df_lcoe = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_results_complete.csv"
)
df_lcoe = df_lcoe[df_lcoe["Country"] == COUNTRY]

# ===============================================================
# Extract callout values for selected availability
# ===============================================================
row = (
    df_lcoe[
        (df_lcoe["Tech"] == "Solar+BESS") &
        (df_lcoe["Year"] == year) &
        (df_lcoe["Availability"] == AVAIL)
    ]
    .iloc[0]
)

solar_capacity = row["Solar_Capacity_MW"]
bess_power = row["BESS_Power_MW"]
duration_h = row["BESS_Energy_MWh"]

# ===============================================================
# Load LCOE component breakdown data (for bottom chart only)
# ===============================================================
df_components = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_breakdowns_complete.csv"
)

df_components = df_components[
    (df_components["Country"] == COUNTRY) &
    (df_components["Year"] == year)
]

component_order = [
    "Solar CAPEX",
    "BESS Energy CAPEX",
    "BESS Power CAPEX",
    "Augmentation",
    "Opex",
]

# ===============================================================
# Load & prepare stack data (precomputed views)
# ===============================================================
typical_week_by_avail = load_typical_week_by_availability(
    country=COUNTRY,
    path=r"C:\Users\barna\PycharmProjects\solar_bess\outputs\long_timeseries_Spain.csv",
    variable_map=VARIABLE_MAP,
    anchor_year=2023
)

week_df = typical_week_by_avail[AVAIL]
print(week_df.columns)
# ===============================================================
# Figure + layout
# ===============================================================
DPI = 100
fig = plt.figure(figsize=(1920 / DPI, 1620 / DPI), dpi=DPI)
fig.patch.set_facecolor(BACKGROUND)

gs = fig.add_gridspec(
    nrows=3,
    ncols=1,
    height_ratios=[1, 1.0, 1.0],
    left=0.08,
    right=0.80,
    top=0.94,
    bottom=0.08,
    hspace=0.30,
)

ax_top = fig.add_subplot(gs[0, 0])
ax_mid = fig.add_subplot(gs[1, 0])
ax_bot = fig.add_subplot(gs[2, 0])

for ax in (ax_top, ax_mid, ax_bot):
    ax.set_facecolor(BACKGROUND)

def shift_and_narrow_axis(ax, shift=0.02, shrink=0.04):
    pos = ax.get_position()
    ax.set_position([
        pos.x0 + shift,
        pos.y0,
        pos.width - shrink,
        pos.height,
    ])

shift_and_narrow_axis(ax_top, shift=0.04, shrink=0.04)

# ===============================================================
# Draw charts
# ===============================================================

# --- Top: Generation stack ---
draw_generation_stack_chart(
    ax=ax_top,
    stack_df=week_df,
    order=["Solar", "Battery Discharge", "Unmet Demand", "Battery Charge", "Curtailment"],
    unit="MW",
    ylims=(-0.6,1),
    positive=POSITIVE,
    negative=NEGATIVE
)

# --- Middle: Capacity cluster ---

draw_capacity_cluster_chart(
    ax=ax_mid,
    df=df_lcoe,
    tech_years=TECH_YEARS,
    max_avail=AVAIL,
    highlight_avail=AVAIL,
    duration_power_ratio=4.0,
    bar_width=0.02,
    colors=capacity_colors
)

ax_mid.set_xlabel(
    "Load factor",
    fontproperties=FONT_REGULAR,
    fontsize=small_font,
    color=DARK_GREY,
    labelpad=10,
)

# --- Bottom: LCOE (Solar+BESS 2025 with components) ---
draw_lcoe_chart(
    ax=ax_bot,
    df=df_lcoe,
    tech_years=TECH_YEARS,
    default_fossil_lf=None,  # not used (no fossil)
    tech_render=TECH_RENDER,
    tech_label_mode=TECH_LABEL_MODE,
    ylims=LCOE_YLIMS,
    y_tick_step=50,
    component_df=df_components,
    component_order=component_order,
    component_colors=component_colors,
    area_alpha=0.65,
)

ax_bot.set_xlabel(
    "Load factor",
    fontproperties=FONT_REGULAR,
    fontsize=small_font,
    color=DARK_GREY,
    labelpad=12,
)

pos = ax_bot.get_position()

ax_bot.set_position([
    pos.x0,
    pos.y0 + 0.02,     # shift up
    pos.width,
    pos.height - 0.04,  # shrink height
])

# ===============================================================
# Titles (figure-level, driven by dict)
# ===============================================================

pad_y = 0.02

axis_titles = {
    ax_top: f"Mean weekly dispatch (availability {AVAIL:.0%})",
    ax_mid: "Installed solar and storage capacity",
    ax_bot: f"Levelised cost of electricity – component breakdown ({year})",
}

for ax, title in axis_titles.items():
    pos = ax.get_position()
    fig.text(
        0.05,
        pos.y1 + pad_y,
        title,
        ha="left",
        va="bottom",
        fontproperties=FONT_REGULAR,
        fontsize=medium_font,
        color=DARK_GREY,
    )

# ===============================================================
# Fine-tune middle axis vertically
# ===============================================================

pos = ax_mid.get_position()

ax_mid.set_position([
    pos.x0,
    pos.y0 + 0.03,     # shift up
    pos.width,
    pos.height - 0.04,  # shrink height
])

def axis_center_y(ax):
    bbox = ax.get_position()
    return 0.5 * (bbox.y0 + bbox.y1)

y_top_center = axis_center_y(ax_top)
x_centre = 0.9

draw_dashboard_callout(
    fig=fig,
    x= x_centre + 0.03,
    y_center=y_top_center+0.05,
    rows=[
        {"label": "Load factor", "value": f"{int(AVAIL * 100)}%"},
    ],
    label_font=FONT_REGULAR,
    value_font=FONT_SEMI_BOLD,
    label_size=small_font,
    value_size=medium_font + 6,
    color=DARK_GREY,
    row_gap=0.05,
    value_offset=0.02,
)

y_mid_center = 0.53

draw_dashboard_callout(
    fig=fig,
    x=0.9 + 0.03,
    y_center=0.55,
    rows=[
        {
            "label": "Solar capacity",
            "value": f"{solar_capacity:.1f} MW",
            "color": STACK_COLOURS["Solar"],
        },
        {
            "label": "BESS power",
            "value": f"{bess_power:.1f} MW",
            "color": capacity_colors["BESS Power"],
        },
        {
            "label": "BESS energy",
            "value": f"{duration_h:.1f} MWh",
            "color": STACK_COLOURS["Battery Discharge"],
        },
    ],
    label_font=FONT_REGULAR,
    value_font=FONT_SEMI_BOLD,
    label_size=small_font,
    value_size=medium_font + 7,
    color=DARK_GREY,
    row_gap=0.075,
    value_offset=0.02,
)

def build_dashboard(fig, axes):
    """
    Returns an update(avail) function for animation.
    """
    ax_top, ax_mid, ax_bot = axes

    availabilities = sorted(df_lcoe["Availability"].unique())
    final_avail = availabilities[-1]

    def update(avail):
        # --- clear axes ---
        ax_top.cla()
        ax_mid.cla()
        ax_bot.cla()

        for ax in (ax_top, ax_mid, ax_bot):
            ax.set_facecolor(BACKGROUND)

        # --- row for availability ---
        row = df_lcoe[
            (df_lcoe["Tech"] == "Solar+BESS") &
            (df_lcoe["Year"] == year) &
            (df_lcoe["Availability"] == avail)
        ].iloc[0]

        solar_capacity = row["Solar_Capacity_MW"]
        bess_power = row["BESS_Power_MW"]
        duration_h = row["BESS_Energy_MWh"]

        week_df = typical_week_by_avail[avail]

        # --- top ---
        draw_generation_stack_chart(
            ax=ax_top,
            stack_df=week_df,
            order=["Solar", "Battery Discharge", "Unmet Demand", "Battery Charge", "Curtailment"],
            unit="MW",
            ylims=(-0.6, 1),
            positive=POSITIVE,
            negative=NEGATIVE,
        )

        # --- middle ---
        highlight = None if avail == final_avail else avail

        draw_capacity_cluster_chart(
            ax=ax_mid,
            df=df_lcoe,
            tech_years=TECH_YEARS,
            max_avail=avail,
            highlight_avail=highlight,
            duration_power_ratio=4.0,
            bar_width=0.02,
            colors=capacity_colors,
        )

        ax_mid.set_xlabel(
            "Load factor",
            fontproperties=FONT_REGULAR,
            fontsize=small_font,
            color=DARK_GREY,
            labelpad=10,
        )

        # --- bottom ---
        draw_lcoe_chart(
            ax=ax_bot,
            df=df_lcoe,
            tech_years=TECH_YEARS,
            default_fossil_lf=None,
            tech_render=TECH_RENDER,
            tech_label_mode=TECH_LABEL_MODE,
            ylims=LCOE_YLIMS,
            y_tick_step=50,
            component_df=df_components,
            component_order=component_order,
            component_colors=component_colors,
            area_alpha=0.65,
        )

        ax_bot.set_xlabel(
            "Load factor",
            fontproperties=FONT_REGULAR,
            fontsize=small_font,
            color=DARK_GREY,
            labelpad=12,
        )

        # --- titles + callouts ---
        fig.texts.clear()

        pad_y = 0.02
        for ax, title in {
            ax_top: f"Mean weekly dispatch (availability {avail:.0%})",
            ax_mid: "Installed solar and storage capacity",
            ax_bot: f"Levelised cost of electricity – component breakdown ({year})",
        }.items():
            pos = ax.get_position()
            fig.text(
                0.05,
                pos.y1 + pad_y,
                title,
                ha="left",
                va="bottom",
                fontproperties=FONT_REGULAR,
                fontsize=medium_font,
                color=DARK_GREY,
            )

        def axis_center_y(ax):
            p = ax.get_position()
            return 0.5 * (p.y0 + p.y1)

        draw_dashboard_callout(
            fig=fig,
            x=0.93,
            y_center=axis_center_y(ax_top) + 0.05,
            rows=[{"label": "Load factor", "value": f"{int(avail * 100)}%"}],
            label_font=FONT_REGULAR,
            value_font=FONT_SEMI_BOLD,
            label_size=small_font,
            value_size=medium_font + 6,
            color=DARK_GREY,
            row_gap=0.05,
            value_offset=0.02,
        )

        draw_dashboard_callout(
            fig=fig,
            x=0.93,
            y_center=0.55,
            rows=[
                {"label": "Solar capacity", "value": f"{solar_capacity:.1f} MW", "color": STACK_COLOURS["Solar"]},
                {"label": "BESS power", "value": f"{bess_power:.1f} MW", "color": capacity_colors["BESS Power"]},
                {"label": "BESS energy", "value": f"{duration_h:.1f} MWh", "color": STACK_COLOURS["Battery Discharge"]},
            ],
            label_font=FONT_REGULAR,
            value_font=FONT_SEMI_BOLD,
            label_size=small_font,
            value_size=medium_font + 7,
            color=DARK_GREY,
            row_gap=0.075,
            value_offset=0.02,
        )

    return update, availabilities

if __name__ == "__main__":
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
