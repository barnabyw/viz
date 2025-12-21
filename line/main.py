import pandas as pd
import os
import time

from utils import build_chart_name, mpl_text
from config import TECH_RENDER, TECH_LABEL_MODE
from lcoe_chart import plot_lcoe_chart

COUNTRY = "Spain"
TITLE_RAW = f"{COUNTRY} in 2025: solar and BESS costs have declined fast"

DEFAULT_FOSSIL_LF = [0.7]

TECH_YEARS = [
    {"tech": "Solar+BESS", "year": 2015},
    {"tech": "Solar+BESS", "year": 2025},
    {"tech": "Gas",        "year": 2015},
    #{"tech": "Gas", "year": 2025},
]

ylims = (0,150)

# Load data
df = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_results.csv"
)
df = df[df["Country"] == COUNTRY]

TITLE = mpl_text(TITLE_RAW)

# Plot
fig, ax = plot_lcoe_chart(
    df=df,
    tech_years=TECH_YEARS,
    title=TITLE,
    default_fossil_lf=DEFAULT_FOSSIL_LF,
    tech_render=TECH_RENDER,
    tech_label_mode=TECH_LABEL_MODE,
    ylims=ylims,
    y_tick_step=50
)

name = build_chart_name(COUNTRY, TECH_YEARS)

output_path = fr"C:\Users\barna\OneDrive\Documents\Solar_BESS\Good charts\video\{name}.png"

fig.savefig(output_path,
    dpi=300,
    facecolor=fig.get_facecolor(),
)

time.sleep(0.3)
os.startfile(output_path)