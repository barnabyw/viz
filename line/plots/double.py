import pandas as pd
import os
import time
import matplotlib.pyplot as plt
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from line.utils import build_chart_name, draw_dashboard_callout
from line.style.config import TECH_RENDER, TECH_LABEL_MODE, POSITIVE, NEGATIVE
from line.style.styling import (
    BACKGROUND,
    FONT_SEMI_BOLD,
    FONT_REGULAR,
    DARK_GREY,
    medium_font,
    small_font,
    STACK_COLOURS,
    component_colors,
    capacity_colors,
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
AVAIL = 1
YEAR = 2015

TECH_YEARS = [{"tech": "Solar+BESS", "year": YEAR}]
LCOE_YLIMS = (0, 500)

# ===============================================================
# Load data
# ===============================================================
df_lcoe = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_results_complete.csv"
)
df_lcoe = df_lcoe[df_lcoe["Country"] == COUNTRY]

df_components = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_breakdowns_complete.csv"
)
df_components = df_components[
    (df_components["Country"] == COUNTRY) &
    (df_components["Year"] == YEAR)
]

component_order = [
    "Solar CAPEX",
    "BESS Energy CAPEX",
    "BESS Power CAPEX",
    "Augmentation",
    "Opex",
]

typical_week_by_avail = load_typical_week_by_availability(
    country=COUNTRY,
    path=r"C:\Users\barna\PycharmProjects\solar_bess\outputs\long_timeseries_Spain.csv",
    variable_map=VARIABLE_MAP,
    anchor_year=2023,
)

# ===============================================================
# Figure + layout
# ===============================================================
DPI = 100
fig = plt.figure(figsize=(1920 / DPI, 1620 / DPI), dpi=DPI)
fig.patch.set_facecolor(BACKGROUND)

gs = fig.add_gridspec(
    nrows=3,
    ncols=1,
    height_ratios=[1, 1, 1],
    left=0.08,
    right=0.80,
    top=0.94,
    bottom=0.08,
    hspace=0.30,
)

ax_top = fig.add_subplot(gs[0])
ax_mid = fig.add_subplot(gs[1])
ax_bot = fig.add_subplot(gs[2])

for ax in (ax_top, ax_mid, ax_bot):
    ax.set_facecolor(BACKGROUND)

# ===============================================================
# Capture base positions ONCE
# ===============================================================
BASE_POS = {
    "top": ax_top.get_position().frozen(),
    "mid": ax_mid.get_position().frozen(),
    "bot": ax_bot.get_position().frozen(),
}

# ===============================================================
# Deterministic vertical squeeze
# ===============================================================
def apply_vertical_squeeze(ax_top, ax_mid, ax_bot, base_pos):
    ax_top.set_position(base_pos["top"])

    p = base_pos["mid"]
    ax_mid.set_position([
        p.x0,
        p.y0 + 0.04,
        p.width,
        p.height - 0.05,
    ])

    p = base_pos["bot"]
    ax_bot.set_position([
        p.x0,
        p.y0 + 0.03,
        p.width,
        p.height - 0.05,
    ])

def axis_center_y(ax):
    p = ax.get_position()
    return 0.5 * (p.y0 + p.y1)

# ===============================================================
# Static draw
# ===============================================================
week_df = typical_week_by_avail[AVAIL]

draw_generation_stack_chart(
    ax=ax_top,
    stack_df=week_df,
    order=["Solar", "Battery Discharge", "Unmet Demand", "Battery Charge", "Curtailment"],
    unit="MW",
    ylims=(-0.6, 1),
    positive=POSITIVE,
    negative=NEGATIVE,
    right_axis=True
)

draw_capacity_cluster_chart(
    ax=ax_mid,
    df=df_lcoe,
    tech_years=TECH_YEARS,
    max_avail=AVAIL,
    highlight_avail=AVAIL,
    duration_power_ratio=4.0,
    bar_width=0.02,
    colors=capacity_colors,
)

ax_mid.set_xlabel(
    "Demand met",
    fontproperties=FONT_REGULAR,
    fontsize=small_font,
    color=DARK_GREY,
    labelpad=10,
)

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
    right_axis=True
)

ax_bot.set_xlabel(
    "Demand met",
    fontproperties=FONT_REGULAR,
    fontsize=small_font,
    color=DARK_GREY,
    labelpad=12,
)

# --- apply squeeze BEFORE titles + dashboards ---
apply_vertical_squeeze(ax_top, ax_mid, ax_bot, BASE_POS)

# ===============================================================
# Titles
# ===============================================================
pad_y = 0.02
for ax, title in {
    ax_top: f"Mean weekly dispatch (availability {AVAIL:.0%})",
    ax_mid: "Installed solar and storage capacity",
    ax_bot: f"Levelised cost of electricity – component breakdown ({YEAR})",
}.items():
    pos = ax.get_position()
    fig.text(
        0.08,
        pos.y1 + pad_y,
        title,
        ha="left",
        va="bottom",
        fontproperties=FONT_REGULAR,
        fontsize=medium_font,
        color=DARK_GREY,
    )

# ===============================================================
# Dashboards (static)
# ===============================================================
row = df_lcoe[
    (df_lcoe["Tech"] == "Solar+BESS") &
    (df_lcoe["Year"] == YEAR) &
    (df_lcoe["Availability"] == AVAIL)
].iloc[0]

solar_capacity = row["Solar_Capacity_MW"]
bess_power = row["BESS_Power_MW"]
duration_h = row["BESS_Energy_MWh"]

draw_dashboard_callout(
    fig=fig,
    x=0.93,
    y_center=axis_center_y(ax_top) + 0.05,
    rows=[{"label": "Demand met", "value": f"{int(AVAIL * 100)}%"}],
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

# ===============================================================
# Animation scaffold
# ===============================================================
def build_dashboard(fig, axes):
    ax_top, ax_mid, ax_bot = axes
    availabilities = sorted(df_lcoe["Availability"].unique())
    final_avail = availabilities[-1]

    def update(avail):
        ax_top.cla()
        ax_mid.cla()
        ax_bot.cla()

        for ax in (ax_top, ax_mid, ax_bot):
            ax.set_facecolor(BACKGROUND)

        week_df = typical_week_by_avail[avail]

        draw_generation_stack_chart(
            ax=ax_top,
            stack_df=week_df,
            order=["Solar", "Battery Discharge", "Unmet Demand", "Battery Charge", "Curtailment"],
            unit="MW",
            ylims=(-0.6, 1),
            positive=POSITIVE,
            negative=NEGATIVE,
            right_axis=True
        )

        draw_capacity_cluster_chart(
            ax=ax_mid,
            df=df_lcoe,
            tech_years=TECH_YEARS,
            max_avail=avail,
            highlight_avail=avail,
            duration_power_ratio=4.0,
            bar_width=0.02,
            colors=capacity_colors,
            ref_xline_label=True if avail > 0.15 else False
        )

        ax_mid.set_xlabel(
            "Demand met",
            fontproperties=FONT_REGULAR,
            fontsize=small_font,
            color=DARK_GREY,
            labelpad=10,
        )

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
            right_axis=True
        )

        ax_bot.set_xlabel(
            "Demand met",
            fontproperties=FONT_REGULAR,
            fontsize=small_font,
            color=DARK_GREY,
            labelpad=12,
        )

        apply_vertical_squeeze(ax_top, ax_mid, ax_bot, BASE_POS)

        # --- clear and redraw titles + dashboards ---
        fig.texts.clear()

        for ax, title in {
            ax_top: f"Average dispatch pattern", # {avail:.0%}
            ax_mid: "Solar and storage capacities to meet % of annual energy",
            ax_bot: f"Levelised cost of electricity – component breakdown ({COUNTRY}, {YEAR})",
        }.items():
            pos = ax.get_position()
            fig.text(
                0.08,
                pos.y1 + pad_y,
                title,
                ha="left",
                va="bottom",
                fontproperties=FONT_REGULAR,
                fontsize=medium_font,
                color=DARK_GREY,
            )

        row = df_lcoe[
            (df_lcoe["Tech"] == "Solar+BESS") &
            (df_lcoe["Year"] == YEAR) &
            (df_lcoe["Availability"] == avail)
        ].iloc[0]

        draw_dashboard_callout(
            fig=fig,
            x=0.93,
            y_center=axis_center_y(ax_top) + 0.05,
            rows=[{"label": "Demand met", "value": f"{int(avail * 100)}%"}],
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
                {"label": "Solar capacity", "value": f"{row['Solar_Capacity_MW']:.1f} MW", "color": STACK_COLOURS["Solar"]},
                {"label": "BESS power", "value": f"{row['BESS_Power_MW']:.1f} MW", "color": capacity_colors["BESS Power"]},
                {"label": "BESS energy", "value": f"{row['BESS_Energy_MWh']:.1f} MWh", "color": STACK_COLOURS["Battery Discharge"]},
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

# ===============================================================
# Save
# ===============================================================
if __name__ == "__main__":
    name = build_chart_name(COUNTRY, TECH_YEARS)
    output_path = rf"C:\Users\barna\OneDrive\Documents\Solar_BESS\Good charts\video\{name}_triple.png"

    fig.savefig(
        output_path,
        dpi=300,
        facecolor=fig.get_facecolor(),
    )

    time.sleep(0.3)
    os.startfile(output_path)
