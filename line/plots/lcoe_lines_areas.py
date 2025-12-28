# -------------------------------------------------
# Configuration
# -------------------------------------------------
COUNTRY = "India"

TITLE_RAW = f"Solar and BESS costs have declined 80% in 10 years"

tag = "3.a"

line_tech_years = [
    #{"tech": "Solar+BESS", "year": 2025, "highlight": True},
    #{"tech": "Solar+BESS", "year": 2020},
    {"tech": "Solar+BESS", "year": 2015, "highlight": True},
    {"tech": "Solar+BESS", "year": 2020, "highlight": True},
    #{"tech": "Gas", "year": 2025},
    #{"tech": "Gas", "year": 2015, "highlight": True} #, "label_pos": "above", "label_anchor": "end"}
]

component_tech_years = [{"tech": "Solar+BESS", "year": 2015}] # None

LCOE_YLIMS = (0, 150)

# -------------------------------------------------
# Component styling
# -------------------------------------------------
component_order = [
    "Solar CAPEX",
    "BESS Energy CAPEX",
    "BESS Power CAPEX",
    "Augmentation",
    "Opex",
]

import pandas as pd
import os
import time
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# -------------------------------------------------
# Path setup
# -------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# -------------------------------------------------
# Imports
# -------------------------------------------------
from line.utils import build_chart_name, mpl_text
from line.style.config import TECH_RENDER, TECH_LABEL_MODE
from line.structure.lcoe_chart import draw_lcoe_chart
from line.style.chart_spec import setup_lcoe_figure
from line.style.styling import (
    BACKGROUND,
    FONT_SEMI_BOLD,
    FONT_REGULAR,
    DARK_GREY,
    large_font,
    medium_font,
    small_font,
    component_colors
)

TITLE = mpl_text(TITLE_RAW)

# -------------------------------------------------
# Load LCOE data
# -------------------------------------------------
df_lcoe = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_results_complete.csv"
)

df_lcoe = df_lcoe[
    df_lcoe["Country"] == COUNTRY
]

# -------------------------------------------------
# Load component breakdown data
# -------------------------------------------------
df_components = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_breakdowns2.csv"
)

df_components = df_components[(df_components["Country"] == COUNTRY)] #&(df_components["Year"] == YEAR)]

# -------------------------------------------------
# Draw chart (components enabled)
# -------------------------------------------------
def render_lcoe(
    *,
    df_lcoe,
    df_components,
    country,
    line_tech_years,
    component_tech_years,
    component_order,
    ylims,
    y_tick_step=50,
    default_fossil_lf=(0.7,),
):
    """
    Render a single LCOE chart (static frame).
    Safe for PNG export or animation driver.
    """

    title_raw = TITLE_RAW
    title = mpl_text(title_raw)
    subtitle = COUNTRY

    fig, ax = setup_lcoe_figure(title, subtitle)

    draw_lcoe_chart(
        ax=ax,
        df=df_lcoe,
        line_tech_years=line_tech_years,
        component_tech_years=component_tech_years,
        component_df=df_components,
        component_order=component_order,
        component_colors=component_colors,
        default_fossil_lf=default_fossil_lf,
        tech_render=TECH_RENDER,
        tech_label_mode=TECH_LABEL_MODE,
        ylims=ylims,
        y_tick_step=y_tick_step,
    )

    return fig, ax

if __name__ == "__main__":

    print(component_tech_years)

    fig, ax = render_lcoe(
        df_lcoe=df_lcoe,
        df_components=df_components,
        country=COUNTRY,
        line_tech_years=line_tech_years,
        component_tech_years=component_tech_years,
        component_order=component_order,
        ylims=LCOE_YLIMS,
    )

    # -------------------------------------------------
    # Save
    # -------------------------------------------------

    name = build_chart_name(COUNTRY, line_tech_years)

    output_path = (
        fr"C:\Users\barna\OneDrive\Documents\Solar_BESS\video charts\{tag}_{name}.png"
    )

    fig.savefig(
        output_path,
        dpi=300,
        facecolor=fig.get_facecolor(),
    )

    time.sleep(0.3)
    os.startfile(output_path)
