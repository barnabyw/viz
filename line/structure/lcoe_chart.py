import sys
from pathlib import Path

from line.style.config import OTHER_LINE_ALPHA, LINE_WEIGHT

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from line.structure.helpers import *

# ===============================================================
# Main chart function
# ===============================================================
def draw_lcoe_chart(
    ax,
    df,
    line_tech_years,
    default_fossil_lf,
    tech_render,
    tech_label_mode,
    ylims=(0, 160),
    y_tick_step=20,
    component_df=None,
    component_tech_years=None,
    component_order=None,
    component_colors=None,
    area_alpha=0.6,
    right_axis=False,
):
    """
    Draw LCOE vs load factor chart.

    Lines and component areas are driven independently:
    - line_tech_years: which tech-years get curves / lines + labels
    - component_tech_years: which tech-years get stacked component areas
    """

    # -------------------------------------------------
    # Axis setup
    # -------------------------------------------------
    ax.set_facecolor(BACKGROUND)
    ax.set_xlim(0.05, 1.0)
    ax.margins(x=0)

    style_y_axis(ax, ylims, y_tick_step, "right" if right_axis else "left")

    # -------------------------------------------------
    # Draw COMPONENT AREAS (independent of lines)
    # -------------------------------------------------
    if component_df is not None and component_tech_years:
        for s in component_tech_years:
            tech, year = s["tech"], s["year"]

            comp = component_df[
                (component_df["Tech"] == tech) &
                (component_df["Year"] == year) &
                (component_df["Component"] != "Total")
            ]

            if comp.empty:
                continue

            pivot = (
                comp
                .pivot(
                    index="Availability",
                    columns="Component",
                    values="Value"
                )
                .sort_index()
            )

            order = component_order or pivot.columns.tolist()

            if component_colors is None:
                raise ValueError(
                    "component_colors must be provided when component_df is used"
                )

            ax.stackplot(
                pivot.index,
                [pivot[c] for c in order],
                colors=[component_colors[c] for c in order],
                alpha=area_alpha,
                zorder=1,
            )

    # -------------------------------------------------
    # Normalise LINE tech-years
    # -------------------------------------------------
    normalised = []
    for s in line_tech_years:
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

    color_lookup = build_color_lookup(line_tech_years)

    # -------------------------------------------------
    # Draw LINES + LABELS
    # -------------------------------------------------
    highlight_mode = any(s.get("highlight", False) for s in line_tech_years)
    for s in normalised:
        label_pos = s.get("label_pos", "above")
        label_anchor = s.get("label_anchor", "start")

        tech, year, lf = s["tech"], s["year"], s["lf"]
        color = color_lookup[(tech, year)]

        is_highlight = s.get("highlight", False)
        alpha = 1.0 if (not highlight_mode or is_highlight) else OTHER_LINE_ALPHA

        # -------- curve techs --------
        if tech_render.get(tech) == "curve":
            data = (
                df[(df["Tech"] == tech) & (df["Year"] == year)]
                .sort_values("Availability")
            )

            if data.empty:
                continue

            ax.plot(
                data["Availability"].values,
                data["LCOE"].values,
                lw=LINE_WEIGHT,
                color=color,
                zorder=3,
                alpha=alpha,
            )

        # -------- fossil techs --------
        else:
            y = fossil_lcoe_at_lf(df, tech, year, lf)

            ax.hlines(
                y,
                *ax.get_xlim(),
                lw=LINE_WEIGHT,
                color=color,
                linestyles=(0, (1.2, 1.5)),
                zorder=2,
                alpha=alpha-0.1,
            )

        draw_lcoe_label(
            ax=ax,
            tech=tech,
            year=year,
            lf=lf,
            df=df,
            color=color,
            ylims=ylims,
            tech_render=tech_render,
            label_pos=label_pos,
            label_anchor=label_anchor,
            alpha=alpha - 0.1,
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

    ax.spines["left"].set_visible(False)

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
    duration_power_ratio=4.0,
    bar_width=0.025,
    highlight_avail=None,
    colors=None,   # NEW
    ref_xline_label = False
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

    # Remove any existing twin axes
    for other_ax in ax.figure.axes:
        if other_ax is not ax and other_ax.get_shared_x_axes().joined(ax, other_ax):
            other_ax.remove()

    # -------------------------------------------------
    # Base styling
    # -------------------------------------------------
    ax.set_facecolor(BACKGROUND)
    ax.margins(x=0)

    ax_power = ax
    ax_duration = ax.twinx()
    ax_duration.patch.set_alpha(0)

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

    DEFAULT_COLORS = {
        "Solar": "#FDB813",
        "BESS Power": "#55A868",
        "BESS Energy": "#4C72B0",
    }

    if colors is None:
        colors = DEFAULT_COLORS

    COLOR_SOLAR = colors["Solar"]
    COLOR_BESS_P = colors["BESS Power"]
    COLOR_DURATION = colors["BESS Energy"]

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
            is_dimmed = highlight_avail is not None and not is_highlight

            power_alpha = FULL_ALPHA if not is_dimmed else FADE_ALPHA
            duration_alpha = FULL_ALPHA if not is_dimmed else FADE_ALPHA * 0.6

            if is_highlight:
                highlight_x = xi

            total_power = smw + bpmw
            max_power_seen = max(max_power_seen, total_power)

            # --- Power (stacked) ---
            # --- Power (stacked) ---
            ax_power.bar(
                xi - offset,
                smw,
                width=bar_width,
                color=COLOR_SOLAR,
                alpha=power_alpha,
                zorder=3,
            )

            ax_power.bar(
                xi - offset,
                bpmw,
                bottom=smw,
                width=bar_width,
                color=COLOR_BESS_P,
                alpha=power_alpha,
                zorder=3,
            )

            # --- Duration ---
            ax_duration.bar(
                xi + offset,
                dh,
                width=bar_width,
                color=COLOR_DURATION,
                alpha=duration_alpha,
                zorder=3,
            )

            # --- Duration ---
            ax_duration.bar(
                xi + offset,
                dh,
                width=bar_width,
                color=COLOR_DURATION,
                alpha=duration_alpha,
                zorder=3,
            )

    # -------------------------------------------------
    # Axis scaling (invisible)
    # -------------------------------------------------
    ax_power.set_ylim(0, max_power_seen * 1.75)
    ax_duration.set_ylim(0, max_power_seen * 1.75 * duration_power_ratio)

    REF_POWER_MW = 1.0

    # --- Reference system lines ---
    ax_power.axhline(
        REF_POWER_MW,
        color=DARK_GREY,
        lw=1.2,
        linestyle=(0, (2, 2)),
        alpha=0.8,
        zorder=2,
    )

    x_left = ax_power.get_xlim()[0]

    if ref_xline_label:
        ax_power.text(
            x_left,
            REF_POWER_MW,
            f"{REF_POWER_MW} MW/{REF_POWER_MW*duration_power_ratio} MWh",
            ha="left",
            va="bottom",
            fontproperties=FONT_SEMI_BOLD,
            fontsize=small_font,
            color=DARK_GREY,
            zorder=5,
            clip_on=False,
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor=BACKGROUND,
                edgecolor="none",
                alpha=0.6,
            ),
        )

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
            f"{int(highlight_x * 100)}%",
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
    negative=None,
    right_axis=False
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
    ax.spines["left"].set_visible(False)

    if right_axis:
        ax.spines["right"].set_visible(True)

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

    if right_axis:
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
        ax.spines["right"].set_color(DARK_GREY)
        ax.spines["right"].set_linewidth(0.8)

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
