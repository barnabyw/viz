from collections import defaultdict

from line.style.styling import DARK_GREY


def build_chart_name(country, tech_years):
    parts = [country.lower().replace(" ", "_")]

    tech_to_years = defaultdict(list)
    for s in tech_years:
        tech_to_years[s["tech"]].append(s["year"])

    for tech, years in tech_to_years.items():
        years = sorted(set(years))

        tech_slug = tech.lower().replace("+", "_").replace(" ", "_")

        if len(years) == 1:
            year_part = str(years[0])
        else:
            year_part = f"{years[0]}-{years[-1]}"

        parts.append(f"{tech_slug}_{year_part}")

    return "_".join(parts)

def mpl_text(s: str) -> str:
    """
    Escape characters that trigger Matplotlib mathtext.
    Currently only handles '$'.
    """
    return s.replace("$", r"\$")

def draw_dashboard_callout(
    fig,
    x,
    y_center,
    rows,
    label_font,
    value_font,
    label_size,
    value_size,
    color,
    row_gap=0.1,
    value_offset=0.015,
):
    """
    Draw a vertical dashboard-style callout.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
    x : float
        X position in figure coordinates (0–1)
    y_center : float
        Vertical center in figure coordinates
    rows : list of dicts
        Each dict: {"label": str, "value": str}
        Optional: {"color": str}
    """

    n = len(rows)
    offsets = [(i - (n - 1) / 2) for i in range(n)]

    for offset, row in zip(offsets, rows):
        y = y_center - offset * row_gap

        # Resolve colour (fallback to existing behaviour)
        row_color = row.get("color", color)

        # Label (small) — UNCHANGED
        fig.text(
            x,
            y,
            row["label"],
            ha="center",
            va="bottom",
            fontproperties=label_font,
            fontsize=label_size,
            color=DARK_GREY,
        )

        # Value (large) — UNCHANGED
        fig.text(
            x,
            y - value_offset,
            row["value"],
            ha="center",
            va="top",
            fontproperties=value_font,
            fontsize=value_size,
            color=row_color,
        )

