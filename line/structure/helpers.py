import numpy as np
import pandas as pd

from line.style.styling import (
    FONT_REGULAR, FONT_MEDIUM, FONT_SEMI_BOLD,
    DARK_GREY, CLOUD, BACKGROUND, build_color_lookup, small_font, medium_font, large_font, STACK_COLOURS
)
from line.style.config import TECH_RENDER, LABEL_OFFSET_PX, LABEL_HORZ_OFF_PX

def fossil_lcoe_at_lf(
    df,
    tech,
    year,
    lf,
    scenario=None,
):
    mask = (
        (df["Tech"] == tech) &
        (df["Year"] == year) &
        (df["Availability"] == lf)
    )

    if scenario is not None:
        mask &= df["Scenario"] == scenario

    subset = df[mask]

    if subset.empty:
        raise ValueError(
            f"No LCOE found for Tech={tech}, Year={year}, "
            f"Availability={lf}"
            + (f", Scenario={scenario}" if scenario is not None else "")
        )

    if len(subset) > 1:
        raise ValueError(
            f"Multiple LCOE rows found for Tech={tech}, Year={year}, "
            f"Availability={lf}"
            + (f", Scenario={scenario}" if scenario is not None else "")
        )

    return subset.iloc[0]["LCOE"]

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

def draw_lcoe_label(
    ax,
    tech,
    year,
    lf,
    df,
    color,
    ylims,
    tech_render,
    label_pos=None,        # allow None
    label_anchor=None,     # allow None
    alpha=1,
    scenario=None,
):
    # -------------------------
    # CURVE TECHS
    # -------------------------
    if tech_render[tech] == "curve":

        mask = (df["Tech"] == tech) & (df["Year"] == year)

        if scenario is not None:
            # Explicit scenario requested
            mask &= df["Scenario"] == scenario
        else:
            # No scenario → baseline only
            mask &= (
                    df["Scenario"].isna() |
                    (df["Scenario"] == "") |
                    (df["Scenario"] == "Base")
            )

        data = df[mask].sort_values("Availability")

        if data.empty:
            return

        x_vals = data["Availability"].values
        y_vals = data["LCOE"].values

        x, y, angle = curve_label_properties_display(
            ax,
            x_vals,
            y_vals,
            label_pos=label_pos or "above",
        )

        label = f"{tech} {year}"
        if scenario is not None:
            label += f" ({scenario})"

        ax.text(
            x,
            y,
            label,
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
    # FLAT / FOSSIL TECHS
    # -------------------------
    else:
        y = fossil_lcoe_at_lf(
            df,
            tech,
            year,
            lf,
            scenario=scenario,
        )

        # ---- defaults for flat lines ----
        label_anchor = label_anchor or "end"
        label_pos = label_pos or "center"

        # Base x position (data space)
        if label_anchor == "start":
            x = ax.get_xlim()[0]
            ha = "right"
            dx = -LABEL_HORZ_OFF_PX
        else:  # "end"
            x = ax.get_xlim()[1]
            ha = "left"
            dx = LABEL_HORZ_OFF_PX

        # Vertical alignment
        if label_pos == "above":
            dy = LABEL_OFFSET_PX
            va = "bottom"
        elif label_pos == "below":
            dy = -LABEL_OFFSET_PX
            va = "top"
        else:  # "center"
            dy = 0
            va = "center"

        # Transform using display space
        p_line = ax.transData.transform((x, y))
        p_label = p_line + np.array([dx, dy])
        x_lab, y_lab = ax.transData.inverted().transform(p_label)

        label = f"{tech} {year} – {int(lf * 100)}% LF"
        if scenario is not None:
            label += f" ({scenario})"

        ax.text(
            x_lab,
            y_lab,
            label,
            fontproperties=FONT_SEMI_BOLD,
            fontsize=medium_font,
            color=color,
            rotation=0,
            va=va,
            ha=ha,
            zorder=4,
            alpha=alpha,
        )