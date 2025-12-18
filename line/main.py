import pandas as pd
import matplotlib.pyplot as plt

from config import (
    COUNTRY, TITLE, TECH_YEARS, DEFAULT_FOSSIL_LF,
    TECH_RENDER, TECH_LABEL_MODE
)
from lcoe_chart import plot_lcoe_chart

# Load data
df = pd.read_csv(
    r"C:\Users\barna\PycharmProjects\solar_bess\outputs\lcoe_results.csv"
)
df = df[df["Country"] == COUNTRY]

# Plot
fig, ax = plot_lcoe_chart(
    df=df,
    tech_years=TECH_YEARS,
    title=TITLE,
    default_fossil_lf=DEFAULT_FOSSIL_LF,
    tech_render=TECH_RENDER,
    tech_label_mode=TECH_LABEL_MODE,
    ylims=(0,200),
    y_tick_step=50
)

plt.show()
