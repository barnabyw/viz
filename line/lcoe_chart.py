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

# ===============================================================
# Main chart function
# ===============================================================
def plot_lcoe_chart(
    df,
    tech_years,
    title,
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

    # ---------------------------
    # Colours
    # ---------------------------
    color_lookup = build_color_lookup(tech_years)

    # ---------------------------
    # Figure
    # ---------------------------
    DPI = 100
    fig, ax = plt.subplots(figsize=(1920 / DPI, 1080 / DPI), dpi=DPI)
    fig.subplots_adjust(left=0.08, right=0.8, top=0.80, bottom=0.14)

    fig.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)

    fig.text(
        0.05, 0.91, title,
        fontproperties=FONT_SEMI_BOLD,
        fontsize=large_font,
        ha="left"
    )

    fig.text(
        0.05, 0.87,
        "Levelised cost of electricity ($/MWh)",
        fontproperties=FONT_REGULAR,
        fontsize=medium_font,
        color=DARK_GREY
    )

    ax.set_xlim(0.05, 1.0)
    ax.set_ylim(*ylims)
    ax.margins(x=0)

    y_min, y_max = ylims
    y_ticks = np.arange(y_min, y_max + y_tick_step, y_tick_step)

    # ---------------------------
    # Gridlines
    # ---------------------------
    ax.hlines(y_ticks, xmin=ax.get_xlim()[0], xmax=ax.get_xlim()[1], color=CLOUD, lw=0.6, zorder=0
    )

    # ---------------------------
    # Plot
    # ---------------------------
    LW_MAIN = 2.6
    HLINE_LABEL_X = 1.01

    for s in normalised:
        tech, year, lf = s["tech"], s["year"], s["lf"]
        color = color_lookup[(tech, year)]

        if tech_render[tech] == "curve":
            data = df[(df["Tech"] == tech) & (df["Year"] == year)]
            data = data.sort_values("Availability")

            x_vals = data["Availability"].values
            y_vals = data["LCOE"].values

            ax.plot(x_vals, y_vals, lw=LW_MAIN, color=color)
            x, y, angle = curve_label_properties_display(ax, x_vals, y_vals)
            label = f"{tech} {year}"

            horz_anchor = "center"

        else:
            y = fossil_lcoe_at_lf(df, tech, year, lf)
            ax.hlines(y, *ax.get_xlim(), lw=LW_MAIN, color=color, linestyles=(0, (1.2, 1.5))) # dot length, gap length
            x, angle = HLINE_LABEL_X, 0
            label = f"{tech} {year} – {int(lf * 100)}% LF"
            horz_anchor = "left"

        ax.text(
            x, y, label,
            fontproperties=FONT_SEMI_BOLD,
            fontsize=medium_font,
            color=color,
            rotation=angle,
            va="center",
            ha=horz_anchor
        )

    # ---------------------------
    # Axes styling
    # ---------------------------
    ax.set_xlabel(
        "Load factor",
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY,
        labelpad=14,  # ⬅ pushes title down
    )

    # X-axis
    x_ticks = np.arange(0.1, 1.01, 0.1)
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(
        [f"{int(t * 100)}%" for t in x_ticks],
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY
    )

    ax.spines["bottom"].set_color(DARK_GREY)
    ax.spines["bottom"].set_linewidth(1.2)
    ax.tick_params(axis="x", length=10, width=1.2, color=DARK_GREY)

    # ---------------------------
    # Y-axis (labels only)
    # ---------------------------
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(
        [f"{y}" for y in y_ticks],
        fontproperties=FONT_REGULAR,
        fontsize=small_font,
        color=DARK_GREY
    )

    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=6)

    # Remove unused spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    return fig, ax
