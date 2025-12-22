import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from styling import (
    FONT_REGULAR, FONT_MEDIUM, FONT_SEMI_BOLD,
    DARK_GREY, CLOUD, BACKGROUND, build_color_lookup, small_font, medium_font, large_font
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
):
    # ---------------------------
    # Normalise tech-years
    # ---------------------------
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

    ax.set_facecolor(BACKGROUND)
    ax.set_xlim(0.05, 1.0)
    ax.margins(x=0)

    # Apply shared y-axis styling
    style_y_axis(ax, ylims, y_tick_step)

    LW_MAIN = 2.6
    HLINE_LABEL_X = 1.01

    for s in normalised:
        tech, year, lf = s["tech"], s["year"], s["lf"]
        color = color_lookup[(tech, year)]

        if tech_render[tech] == "curve":
            data = df[(df["Tech"] == tech) & (df["Year"] == year)].sort_values("Availability")
            x_vals = data["Availability"].values
            y_vals = data["LCOE"].values

            ax.plot(x_vals, y_vals, lw=LW_MAIN, color=color)

            x, y, angle = curve_label_properties_display(ax, x_vals, y_vals)
            label = f"{tech} {year}"
            ha = "center"

        else:
            y = fossil_lcoe_at_lf(df, tech, year, lf)
            ax.hlines(
                y, *ax.get_xlim(),
                lw=LW_MAIN,
                color=color,
                linestyles=(0, (1.2, 1.5))
            )
            x, angle = HLINE_LABEL_X, 0
            label = f"{tech} {year} – {int(lf * 100)}% LF"
            ha = "left"

        ax.text(
            x, y, label,
            fontproperties=FONT_SEMI_BOLD,
            fontsize=medium_font,
            color=color,
            rotation=angle,
            va="center",
            ha=ha
        )

    # X-axis styling (unchanged)
    ax.set_xticks(np.arange(0.1, 1.01, 0.1))
    ax.set_xticklabels(
        [f"{int(t * 100)}%" for t in ax.get_xticks()],
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY
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

