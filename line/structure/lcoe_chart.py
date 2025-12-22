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
    """Uses Availability as load-factor proxy."""
    subset = df[(df["Tech"] == tech) & (df["Year"] == year)]
    idx = (subset["Availability"] - lf).abs().idxmin()
    return subset.loc[idx, "LCOE"]

def curve_label_properties_display(
    ax,
    x,
    y,
    x_anchor=0.62,
    dx=0.05,
    offset_px=18,
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

    p_label = p_curve + np.array([0, offset_px])

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
    # Normalise tech-years
    # -------------------------------------------------
    normalised = []
    for s in tech_years:
        tech, year = s["tech"], s["year"]
        if tech in ["Gas", "Coal"]:
            lfs = s.get("lf", default_fossil_lf)
            for lf in lfs:
                normalised.append({"tech": tech, "year": year, "lf": lf})
        else:
            normalised.append({"tech": tech, "year": year, "lf": None})

    color_lookup = build_color_lookup(tech_years)

    # -------------------------------------------------
    # Axis setup
    # -------------------------------------------------
    ax.set_facecolor(BACKGROUND)
    ax.set_xlim(0.05, 1.0)
    ax.margins(x=0)

    style_y_axis(ax, ylims, y_tick_step)

    LW_MAIN = 2.6
    HLINE_LABEL_X = 1.01

    # -------------------------------------------------
    # Plot each tech/year
    # -------------------------------------------------
    for s in normalised:
        tech, year, lf = s["tech"], s["year"], s["lf"]
        color = color_lookup[(tech, year)]

        # =================================================
        # CURVE TECHS (e.g. Solar+BESS)
        # =================================================
        if tech_render[tech] == "curve":
            data = (
                df[(df["Tech"] == tech) & (df["Year"] == year)]
                .sort_values("Availability")
            )

            x_vals = data["Availability"].values
            y_vals = data["LCOE"].values

            # ---------------------------
            # Optional stacked areas
            # ---------------------------
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

            # ---------------------------
            # LCOE curve
            # ---------------------------
            ax.plot(
                x_vals,
                y_vals,
                lw=LW_MAIN,
                color=color,
                zorder=3,
            )

            x, y, angle = curve_label_properties_display(ax, x_vals, y_vals)
            label = f"{tech} {year}"
            ha = "center"

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

            x, angle = HLINE_LABEL_X, 0
            label = f"{tech} {year} – {int(lf * 100)}% LF"
            ha = "left"

        # ---------------------------
        # Label
        # ---------------------------
        ax.text(
            x,
            y,
            label,
            fontproperties=FONT_SEMI_BOLD,
            fontsize=medium_font,
            color=color,
            rotation=angle,
            va="center",
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
    ylims_power,
    y_tick_step_power,
    ylims_duration,
    y_tick_step_duration,
    bar_width=0.025,
    highlight_avail=None,
):
    """
    Clustered capacity chart vs availability.

    For each availability:
    - Left axis (MW): stacked Solar + BESS power capacity
    - Right axis (h): storage duration (energy / power)

    Optional:
    - highlight_avail: float (e.g. 0.75) to emphasise one load factor
    """

    ax.cla()

    # -------------------------------------------------
    # Base styling
    # -------------------------------------------------
    ax.set_facecolor(BACKGROUND)
    ax.margins(x=0)
    ax.spines["top"].set_visible(False)

    ax_power = ax
    ax_duration = ax.twinx()

    ax_duration.spines["top"].set_visible(False)
    ax_duration.spines["right"].set_visible(False)

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

    # -------------------------------------------------
    # Plot bars
    # -------------------------------------------------
    for s in normalised:
        tech, year = s["tech"], s["year"]

        data = (
            df[(df["Tech"] == tech) & (df["Year"] == year)]
            .sort_values("Availability")
        )

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

            # --- Duration ---
            ax_duration.bar(
                xi + offset,
                dh,
                width=bar_width,
                color=COLOR_DURATION,
                alpha=alpha,
                zorder=3,
            )

    # -------------------------------------------------
    # Left y-axis (MW)
    # -------------------------------------------------
    style_y_axis(
        ax=ax_power,
        ylims=ylims_power,
        y_tick_step=y_tick_step_power,
    )

    ax_power.grid(False)
    ax_duration.spines["left"].set_visible(False)

    ax_power.set_ylabel(
        "Installed power (MW)",
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY,
        labelpad=10,
    )

    # -------------------------------------------------
    # Right y-axis (hours)
    # -------------------------------------------------
    y_min, y_max = ylims_duration
    y_ticks = np.arange(y_min, y_max + 1e-9, y_tick_step_duration)
    y_ticks = y_ticks[y_ticks <= y_max]

    ax_duration.set_ylim(y_min, y_max)
    ax_duration.set_yticks(y_ticks)
    ax_duration.set_yticklabels(
        [f"{y:g} h" for y in y_ticks],
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY,
    )

    ax_duration.tick_params(axis="y", length=0, pad=6)

    # -------------------------------------------------
    # X-axis
    # -------------------------------------------------
    ax_power.set_xticks(np.arange(0.1, 1.01, 0.1))
    ax_power.set_xticklabels(
        [f"{int(t * 100)}%" for t in ax_power.get_xticks()],
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY,
    )

    # -------------------------------------------------
    # Highlight annotation (optional)
    # -------------------------------------------------
    if highlight_x is not None:
        ax_power.axvline(
            highlight_x,
            color=DARK_GREY,
            linestyle=(0, (1.5, 2.5)),
            linewidth=1.2,
            zorder=4,
        )

        ax_power.text(
            highlight_x,
            ylims_power[1],
            f"Load factor: {int(highlight_x * 100)}%",
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
    ylims=None,
    unit="GW",
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
    ax.stackplot(
        stack_scaled.index,
        [stack_scaled[col] for col in order],
        colors=[STACK_COLOURS[col] for col in order],
        alpha=0.95,
        zorder=2,
    )

    # ---------------------------
    # Y-axis
    # ---------------------------
    if ylims is not None:
        ax.set_ylim(*ylims)
    else:
        ymax = stack_scaled.sum(axis=1).max()
        ax.set_ylim(0, ymax * 1.1)

    yticks = ax.get_yticks()
    ax.set_yticks(yticks)
    ax.set_yticklabels(
        [f"{t:g} {unit_label}" for t in yticks],
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
