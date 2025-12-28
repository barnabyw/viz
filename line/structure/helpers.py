import numpy as np
import pandas as pd

from line.style.styling import (
    FONT_REGULAR, FONT_MEDIUM, FONT_SEMI_BOLD,
    DARK_GREY, CLOUD, BACKGROUND, build_color_lookup, small_font, medium_font, large_font, STACK_COLOURS
)
from line.style.config import TECH_RENDER, LABEL_OFFSET_PX


def fossil_lcoe_at_lf(df, tech, year, lf):
    subset = df[
        (df["Tech"] == tech) &
        (df["Year"] == year) &
        (df["Availability"] == lf)
    ]
    if subset.empty:
        raise ValueError(
            f"No LCOE found for Tech={tech}, Year={year}, Availability={lf}"
        )
    if len(subset) > 1:
        raise ValueError(
            f"Multiple LCOE rows found for Tech={tech}, Year={year}, Availability={lf}"
        )
    return subset.iloc[0]["LCOE"]

def curve_label_properties_display(
    ax,
    x,
    y,
    x_anchor=0.62,
    dx=0.05,
    offset_px=LABEL_OFFSET_PX,
    label_pos="above"
):

    x = np.asarray(x)
    y = np.asarray(y)

    x1, x2 = x_anchor - dx, x_anchor + dx
    y1 = np.interp(x1, x, y)
    y2 = np.interp(x2, x, y)

    p1 = ax.transData.transform((x1, y1))
    p2 = ax.transData.transform((x2, y2))

    angle = np.degrees(np.arctan2(p2[1] - p1[1], p2[0] - p1[0]))

    y_curve = np.interp(x_anchor, x, y)
    p_curve = ax.transData.transform((x_anchor, y_curve))

    sign = 1 if label_pos == "above" else -1
    p_label = p_curve + np.array([0, sign * offset_px])

    return *ax.transData.inverted().transform(p_label), angle

def style_y_axis(
    ax,
    ylims,
    y_tick_step,
    side="left"
):
    """
    Apply standard y-axis styling used across charts.
    """

    y_min, y_max = ylims
    ax.set_ylim(y_min, y_max)

    # Generate ticks, then clip strictly to limits
    y_ticks = np.arange(y_min, y_max + 1e-9, y_tick_step)
    y_ticks = y_ticks[y_ticks <= y_max]

    # Gridlines
    ax.hlines(
        y_ticks,
        xmin=ax.get_xlim()[0],
        xmax=ax.get_xlim()[1],
        color=CLOUD,
        lw=1,
        zorder=0,
        alpha=0.65
    )

    # Tick labels
    # Optional: remove zero tick on right axis
    if side == "right":
        y_ticks = y_ticks[y_ticks != 0]

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(
        [f"{y:g}" for y in y_ticks],
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY,
    )

    # Spine + ticks
    ax.spines["top"].set_visible(False)

    if side == "right":
        ax.spines["left"].set_visible(False)
        ax.spines["right"].set_visible(True)

        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")

        ax.spines["right"].set_color(DARK_GREY)
        ax.spines["right"].set_linewidth(0.8)

    else:  # left (default)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(True)

        ax.yaxis.tick_left()
        ax.yaxis.set_label_position("left")

        ax.spines["left"].set_color(DARK_GREY)
        ax.spines["left"].set_linewidth(0.8)

    ax.tick_params(axis="y", length=0, pad=6)

def draw_lcoe_label(
    ax,
    tech,
    year,
    lf,
    df,
    color,
    ylims,
    tech_render,
    label_pos="above",
    label_anchor="start",
    alpha=1
):
    sign = 1 if label_pos == "above" else -1

    # -------------------------
    # CURVE TECHS
    # -------------------------
    if tech_render[tech] == "curve":
        data = (
            df[(df["Tech"] == tech) & (df["Year"] == year)]
            .sort_values("Availability")
        )

        x_vals = data["Availability"].values
        y_vals = data["LCOE"].values

        x, y, angle = curve_label_properties_display(
            ax,
            x_vals,
            y_vals,
            label_pos=label_pos,
        )

        ax.text(
            x,
            y,
            f"{tech} {year}",
            fontproperties=FONT_SEMI_BOLD,
            fontsize=medium_font,
            color=color,
            rotation=angle,
            va="center",
            ha="center",
            zorder=4,
            alpha=alpha,
        )

    # -------------------------
    # FOSSIL TECHS
    # -------------------------
    else:
        y = fossil_lcoe_at_lf(df, tech, year, lf)

        if label_anchor == "start":
            x = ax.get_xlim()[0]
            ha = "left"
        else:
            x = ax.get_xlim()[1]
            ha = "right"

        p_line = ax.transData.transform((x, y))
        p_label = p_line + np.array([0, sign * LABEL_OFFSET_PX])
        x_lab, y_lab = ax.transData.inverted().transform(p_label)

        ax.text(
            x_lab,
            y_lab,
            f"{tech} {year} – {int(lf * 100)}% LF",
            fontproperties=FONT_SEMI_BOLD,
            fontsize=medium_font,
            color=color,
            rotation=0,
            va="center", #va
            ha=ha,
            zorder=4,
            alpha=alpha,
        )