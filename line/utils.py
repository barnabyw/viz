from collections import defaultdict

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