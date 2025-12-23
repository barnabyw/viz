import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from line.style.styling import (
    FONT_REGULAR, FONT_MEDIUM, FONT_SEMI_BOLD,
    DARK_GREY, CLOUD, BACKGROUND, build_color_lookup, small_font, medium_font, large_font, STACK_COLOURS
)

# ===============================================================
# Helpers
# ===============================================================
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
    offset_px=18,
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
        lw=0.6,
        zorder=0,
    )

    # Tick labels
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(
        [f"{y:g}" for y in y_ticks],
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY,
    )

    # Spine + ticks
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.tick_params(axis="y", length=0, pad=6)


# ===============================================================
# Main chart function
# ===============================================================
def draw_lcoe_chart(
    ax,
    df,
    tech_years,
    default_fossil_lf,
    tech_render,
    tech_label_mode,
    ylims=(0, 160),
    y_tick_step=20,
    component_df=None,
    component_order=None,
    component_colors=None,
    area_alpha=0.6,
):
    """
    Draw LCOE vs load factor chart.

    Supports:
    - Curves (renewables)
    - Horizontal lines (fossil at fixed LF)
    - Optional stacked areas for LCOE component breakdown

    component_df must be long-form:
        Country | Year | Tech | Availability | Component | Value
    """

    # -------------------------------------------------
    # Normalise tech-years (PRESERVE all controls)
    # -------------------------------------------------
    normalised = []
    for s in tech_years:
        tech, year = s["tech"], s["year"]

        if tech in ["Gas", "Coal"]:
            lfs = s.get("lf", default_fossil_lf)
            for lf in lfs:
                entry = s.copy()
                entry["lf"] = lf
                normalised.append(entry)
        else:
            entry = s.copy()
            entry["lf"] = None
            normalised.append(entry)

    color_lookup = build_color_lookup(tech_years)

    # -------------------------------------------------
    # Axis setup
    # -------------------------------------------------
    ax.set_facecolor(BACKGROUND)
    ax.set_xlim(0.05, 1.0)
    ax.margins(x=0)

    style_y_axis(ax, ylims, y_tick_step)

    LW_MAIN = 2.6

    # Precompute proportional offset
    y_min, y_max = ylims
    y_range = y_max - y_min
    OFFSET_FRAC = 0.017
    y_offset = OFFSET_FRAC * y_range

    # -------------------------------------------------
    # Plot each tech/year
    # -------------------------------------------------
    for s in normalised:
        tech, year, lf = s["tech"], s["year"], s["lf"]
        color = color_lookup[(tech, year)]

        label_pos = s.get("label_pos", "above")     # above | below
        label_anchor = s.get("label_anchor", "end") # start | end (flat only)

        sign = 1 if label_pos == "above" else -1
        va = "bottom" if label_pos == "above" else "top"

        # =================================================
        # CURVE TECHS
        # =================================================
        if tech_render[tech] == "curve":
            data = (
                df[(df["Tech"] == tech) & (df["Year"] == year)]
                .sort_values("Availability")
            )

            x_vals = data["Availability"].values
            y_vals = data["LCOE"].values

            # Optional stacked areas
            if component_df is not None:
                comp = component_df[
                    (component_df["Tech"] == tech) &
                    (component_df["Year"] == year) &
                    (component_df["Component"] != "Total")
                ]

                if not comp.empty:
                    pivot = (
                        comp
                        .pivot(
                            index="Availability",
                            columns="Component",
                            values="Value"
                        )
                        .sort_index()
                    )

                    if component_order is None:
                        component_order = pivot.columns.tolist()

                    if component_colors is None:
                        raise ValueError(
                            "component_colors must be provided when component_df is used"
                        )

                    ax.stackplot(
                        pivot.index,
                        [pivot[c] for c in component_order],
                        colors=[component_colors[c] for c in component_order],
                        alpha=area_alpha,
                        zorder=1,
                    )

            # LCOE curve
            ax.plot(
                x_vals,
                y_vals,
                lw=LW_MAIN,
                color=color,
                zorder=3,
            )

            x, y, angle = curve_label_properties_display(
                ax,
                x_vals,
                y_vals,
                label_pos=label_pos,
            )
            label = f"{tech} {year}"

            curve_below_offset_frac = 0.017
            curve_below_offset = curve_below_offset_frac * (ylims[1] - ylims[0])

            if label_pos == "below":
                y = y - curve_below_offset

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
            )

        # =================================================
        # FOSSIL TECHS (horizontal)
        # =================================================
        else:
            y = fossil_lcoe_at_lf(df, tech, year, lf)

            ax.hlines(
                y,
                *ax.get_xlim(),
                lw=LW_MAIN,
                color=color,
                linestyles=(0, (1.2, 1.5)),
                zorder=2,
            )

            if label_anchor == "start":
                x = ax.get_xlim()[0]
                ha = "left"
            else:
                x = ax.get_xlim()[1]
                ha = "right"

            label = f"{tech} {year} – {int(lf * 100)}% LF"

            ax.text(
                x,
                y + sign * y_offset,
                label,
                fontproperties=FONT_SEMI_BOLD,
                fontsize=medium_font,
                color=color,
                rotation=0,
                va=va,
                ha=ha,
                zorder=4,
            )

    # -------------------------------------------------
    # X-axis styling
    # -------------------------------------------------
    ax.set_xticks(np.arange(0.1, 1.01, 0.1))
    ax.set_xticklabels(
        [f"{int(t * 100)}%" for t in ax.get_xticks()],
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY,
    )

def draw_capacity_stack_chart(
    ax,
    df,
    tech_years,
    ylims,
    y_tick_step,
):
    """
    Stacked capacity bars vs availability.
    """

    # ---------------------------
    # Normalise tech-years
    # ---------------------------
    normalised = []
    for s in tech_years:
        normalised.append({
            "tech": s["tech"],
            "year": s["year"],
        })

    ax.set_facecolor(BACKGROUND)
    ax.set_xlim(0.05, 1.0)
    ax.margins(x=0)

    # Apply shared y-axis styling
    style_y_axis(ax, ylims, y_tick_step)

    # ---------------------------
    # Bar settings
    # ---------------------------
    BAR_WIDTH = 0.035

    COLOR_SOLAR = "#FDB813"
    COLOR_BESS_E = "#4C72B0"
    COLOR_BESS_P = "#55A868"

    # ---------------------------
    # Plot bars
    # ---------------------------
    for s in normalised:
        tech, year = s["tech"], s["year"]

        data = (
            df[(df["Tech"] == tech) & (df["Year"] == year)]
            .sort_values("Availability")
        )

        x = data["Availability"].values

        solar = data["Solar_Capacity_MW"].values
        bess_e = data["BESS_Energy_MWh"].values
        bess_p = data["BESS_Power_MW"].values

        ax.bar(
            x,
            solar,
            width=BAR_WIDTH,
            color=COLOR_SOLAR,
            edgecolor="none",
            zorder=3,
        )

        ax.bar(
            x,
            bess_e,
            bottom=solar,
            width=BAR_WIDTH,
            color=COLOR_BESS_E,
            edgecolor="none",
            zorder=3,
        )

        ax.bar(
            x,
            bess_p,
            bottom=solar + bess_e,
            width=BAR_WIDTH,
            color=COLOR_BESS_P,
            edgecolor="none",
            zorder=3,
        )

    # X-axis styling (same contract)
    ax.set_xticks(np.arange(0.1, 1.01, 0.1))
    ax.set_xticklabels(
        [f"{int(t * 100)}%" for t in ax.get_xticks()],
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY,
    )

def draw_capacity_cluster_chart(
    ax,
    df,
    tech_years,
    max_avail=None,
    duration_power_ratio=4.0,   # hours per MW (axis scaling only)
    bar_width=0.025,
    highlight_avail=None,
):
    """
    Clustered capacity chart vs availability.

    Behaviour:
    - Plots availabilities <= max_avail (if provided)
    - Left axis: stacked Solar + BESS power (MW) [axis hidden]
    - Right axis: duration proxy (h) via fixed ratio [axis hidden]
    - X-axis unchanged
    """

    ax.cla()

    # -------------------------------------------------
    # Base styling
    # -------------------------------------------------
    ax.set_facecolor(BACKGROUND)
    ax.margins(x=0)

    ax_power = ax
    ax_duration = ax.twinx()

    # Hide vertical + top spines, keep bottom (x-axis line)
    for spine in ["top", "right", "left"]:
        ax_power.spines[spine].set_visible(False)
        ax_duration.spines[spine].set_visible(False)

    # Explicitly keep bottom spine visible
    ax_power.spines["bottom"].set_visible(True)
    ax_power.spines["bottom"].set_color(DARK_GREY)
    ax_power.spines["bottom"].set_linewidth(0.8)

    # Kill y ticks explicitly (belt + braces)
    ax_power.set_yticks([])
    ax_duration.set_yticks([])
    # -------------------------------------------------
    # Colours
    # -------------------------------------------------
    COLOR_SOLAR = "#FDB813"
    COLOR_BESS_P = "#55A868"
    COLOR_DURATION = "#4C72B0"

    FADE_ALPHA = 0.25
    FULL_ALPHA = 1.0

    # -------------------------------------------------
    # Normalise tech-years
    # -------------------------------------------------
    normalised = [{"tech": s["tech"], "year": s["year"]} for s in tech_years]

    highlight_x = None
    max_power_seen = 0.0

    # -------------------------------------------------
    # Plot bars
    # -------------------------------------------------
    for s in normalised:
        tech, year = s["tech"], s["year"]

        data = df[(df["Tech"] == tech) & (df["Year"] == year)].copy()

        if max_avail is not None:
            data = data[data["Availability"] <= max_avail]

        data = data.sort_values("Availability")

        x = data["Availability"].values
        offset = bar_width / 2

        solar_mw = data["Solar_Capacity_MW"].values
        bess_power_mw = data["BESS_Power_MW"].values
        duration_h = data["BESS_Energy_MWh"].values

        for xi, smw, bpmw, dh in zip(x, solar_mw, bess_power_mw, duration_h):

            is_highlight = highlight_avail is not None and np.isclose(xi, highlight_avail)
            alpha = FULL_ALPHA if is_highlight or highlight_avail is None else FADE_ALPHA

            if is_highlight:
                highlight_x = xi

            total_power = smw + bpmw
            max_power_seen = max(max_power_seen, total_power)

            # --- Power (stacked) ---
            ax_power.bar(
                xi - offset,
                smw,
                width=bar_width,
                color=COLOR_SOLAR,
                alpha=alpha,
                zorder=3,
            )

            ax_power.bar(
                xi - offset,
                bpmw,
                bottom=smw,
                width=bar_width,
                color=COLOR_BESS_P,
                alpha=alpha,
                zorder=3,
            )

            # --- Duration (scaled via ratio) ---
            ax_duration.bar(
                xi + offset,
                dh,
                width=bar_width,
                color=COLOR_DURATION,
                alpha=alpha,
                zorder=3,
            )

    # -------------------------------------------------
    # Axis scaling (invisible)
    # -------------------------------------------------
    ax_power.set_ylim(0, max_power_seen * 1.75)
    ax_duration.set_ylim(0, max_power_seen * 1.75 * duration_power_ratio)

    # -------------------------------------------------
    # X-axis (unchanged)
    # -------------------------------------------------
    ax_power.set_xticks(np.arange(0.1, 1.01, 0.1))
    ax_power.set_xticklabels(
        [f"{int(t * 100)}%" for t in ax_power.get_xticks()],
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY,
    )

    label_pad = 0.9

    # -------------------------------------------------
    # Highlight annotation (optional)
    # -------------------------------------------------
    if highlight_x is not None:
        ax_power.axvline(
            highlight_x,
            ymin=0.0,
            ymax=label_pad,
            color=DARK_GREY,
            linestyle=(0, (1.5, 2.5)),
            linewidth=1.2,
            zorder=4,
        )

        ax_power.text(
            highlight_x,
            ax_power.get_ylim()[1]*label_pad-0.05,
            f"Load factor: {int(highlight_x * 100)}% ",
            ha="center",
            va="bottom",
            fontproperties=FONT_SEMI_BOLD,
            fontsize=small_font,
            color=DARK_GREY,
            zorder=5,
        )

def draw_generation_stack_chart(
    ax,
    stack_df,
    order,
    ylims=(0,1.2),
    unit="GW",
    positive=None,
    negative=None
):


    """
    Stacked generation chart.

    - Data expected in MW
    - unit="GW" or "MW" controls display scaling
    - X-axis always shows 12 AM and 12 PM anchors
    """

    ax.cla()

    # ---------------------------
    # Base axis styling
    # ---------------------------
    ax.set_facecolor(BACKGROUND)
    ax.margins(x=0)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    # ---------------------------
    # Ensure all ordered techs exist
    # ---------------------------
    stack_df = stack_df.copy()
    for tech in order:
        if tech not in stack_df.columns:
            stack_df[tech] = 0.0

    # ---------------------------
    # Data prep
    # ---------------------------
    if unit == "GW":
        scale = 1_000.0
        unit_label = "GW"
    elif unit == "MW":
        scale = 1.0
        unit_label = "MW"
    else:
        raise ValueError("unit must be 'GW' or 'MW'")

    stack_scaled = stack_df[order] / scale

    # ---------------------------
    # Stackplot
    # ---------------------------
    # ---------------------------
    # Positive stack (above zero)
    # ---------------------------
    ax.stackplot(
        stack_scaled.index,
        [stack_scaled[c] for c in positive if c in stack_scaled.columns],
        colors=[STACK_COLOURS[c] for c in positive if c in stack_scaled.columns],
        alpha=0.95,
        zorder=2,
    )

    # ---------------------------
    # Negative stack (below zero)
    # ---------------------------
    if negative:
        ax.stackplot(
            stack_scaled.index,
            [stack_scaled[c] for c in negative if c in stack_scaled.columns],
            colors=[STACK_COLOURS[c] for c in negative if c in stack_scaled.columns],
            alpha=0.95,
            zorder=2,
        )

    # Ensure x-axis elements render above stacks
    ax.spines["bottom"].set_zorder(5)
    ax.xaxis.set_zorder(5)

    # ---------------------------
    # Y-axis (only 0 and 1)
    # ---------------------------
    ax.set_ylim(*ylims)

    y_min, y_max = ax.get_ylim()  # or ylims

    ax.set_yticks([y_min, 0, y_max])
    ax.set_yticklabels(
        [f"{y_min:g} {unit_label}", "0", f"{y_max:g} {unit_label}"],
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY,
    )

    # ---------------------------
    # X-axis: 12 AM / 12 PM only
    # ---------------------------
    hours = stack_scaled.index.hour
    tick_mask = hours.isin([12])
    xticks = stack_scaled.index[tick_mask]


    labels = []
    for t in xticks:
        labels.append("12 PM")

    # ---------------------------
    # Move x-axis to y = 0
    # ---------------------------
    ax.spines["bottom"].set_position(("data", 0))
    ax.spines["bottom"].set_color(DARK_GREY)
    ax.spines["bottom"].set_linewidth(0.8)

    ax.xaxis.set_ticks_position("bottom")
    ax.xaxis.set_label_position("bottom")

    ax.set_xticks(xticks)
    ax.set_xticklabels(
        labels,
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY,
    )

    # ---------------------------
    # Grid (y only)
    # ---------------------------
    ax.grid(
        axis="y",
        color=CLOUD,
        linewidth=0.8,
        alpha=0.35,
        zorder=1,
    )
