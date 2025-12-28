# chart_spec.py
import matplotlib.pyplot as plt
from line.style.styling import (
    BACKGROUND,
    FONT_SEMI_BOLD,
    FONT_REGULAR,
    DARK_GREY,
    large_font,
    medium_font,
    small_font,
)

def setup_lcoe_figure(title):
    DPI = 100
    fig = plt.figure(figsize=(1920 / DPI, 1080 / DPI), dpi=DPI)
    fig.patch.set_facecolor(BACKGROUND)

    ax = fig.add_subplot(1, 1, 1)
    ax.set_facecolor(BACKGROUND)

    fig.subplots_adjust(
        left=0.087,
        right=0.80,
        top=0.80,
        bottom=0.14,
    )

    # ---- titles (draw ONCE) ----
    fig.text(
        0.05,
        0.91,
        title,
        fontproperties=FONT_SEMI_BOLD,
        fontsize=large_font,
        ha="left",
    )

    fig.text(
        0.05,
        0.87,
        "Levelised cost of electricity ($/MWh)",
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

    return fig, ax
