import numpy as np
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
from line.style.content import *


import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter

def animate_lcoe_yzoom(
    *,
    df_lcoe,
    df_components,
    country,
    year,
    line_tech_years,
    component_tech_years,
    component_order,
    y_start,
    y_end,
    frames=40,
    fps=30,
    hold_seconds=1.0,     # ← NEW
    default_fossil_lf=(0.7,),
    save_path=None,
):

    title = mpl_text(f"{country} in {year}: solar and BESS cost breakdown")

    # ---- create layout ONCE ----
    fig, ax = setup_lcoe_figure(title)

    hold_frames = int(hold_seconds * fps)
    total_frames = frames + hold_frames

    def ease_out_cubic(t):
        return 1 - (1 - t) ** 3

    def update(frame):
        if frame < frames:
            t = frame / (frames - 1)
            t = ease_out_cubic(t)
        else:
            t = 1.0  # hold final state

        ylims = (
            y_start[0] + t * (y_end[0] - y_start[0]),
            y_start[1] + t * (y_end[1] - y_start[1]),
        )

        ax.clear()
        ax.set_facecolor(BACKGROUND)

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
            y_tick_step=50,
        )

        return []

    anim = FuncAnimation(
        fig,
        update,
        frames=total_frames,
        interval=1000 / fps,
        blit=False,
    )

    # ---- Save OR preview ----
    if save_path is not None:
        writer = FFMpegWriter(
            fps=fps,
            metadata={"artist": "Barnaby Winser"},
            bitrate=10000,
        )

        anim.save(save_path, writer=writer)
        plt.close(fig)

    else:
        plt.show()

    return anim


if __name__ == "__main__":
    name = build_chart_name(COUNTRY, line_tech_years)

    output_path = (
        fr"C:\Users\barna\OneDrive\Documents\Solar_BESS\video charts\{tag}_{name}_ANIM.mp4"
    )

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

    df_components = df_components[
        (df_components["Country"] == COUNTRY) &
        (df_components["Year"] == YEAR)
        ]

    animate_lcoe_yzoom(
        df_lcoe=df_lcoe,
        df_components=df_components,
        country=COUNTRY,
        year=YEAR,
        line_tech_years=line_tech_years,
        component_tech_years=component_tech_years,
        component_order=component_order,
        y_start=(0, 400),
        y_end=(0, 200),
        frames=45,
        fps=60,
        save_path=output_path
    )

