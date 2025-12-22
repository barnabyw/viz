# data/stack_views.py

import pandas as pd

def _clean_long_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["Hour"] = df["Hour"].astype(int)
    df["Availability"] = df["Availability"].astype(float)
    df["Country"] = df["Country"].astype(str)
    df["Variable"] = df["Variable"].astype(str)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0.0)

    return df


def _build_stack_lookup(df, country, variable_map, anchor_year):
    lookup = {}

    sub = df[df["Country"] == country]

    for avail, g in sub.groupby("Availability"):
        idx = pd.Timestamp(f"{anchor_year}-01-01") + pd.to_timedelta(
            g["Hour"], unit="h"
        )

        wide = (
            g.assign(time=idx)
             .pivot(index="time", columns="Variable", values="Value")
             .fillna(0.0)
             .sort_index()
             .rename(columns=variable_map)
        )

        lookup[avail] = wide

    return lookup


def _select_typical_week(stack_df, anchor_date):
    week = (
        stack_df
        .assign(dow=stack_df.index.dayofweek, hour=stack_df.index.hour)
        .groupby(["dow", "hour"])
        .mean()
        .reset_index()
        .sort_values(["dow", "hour"])
    )

    idx = (
        pd.to_datetime(anchor_date)
        + pd.to_timedelta(week["dow"] * 24 + week["hour"], unit="h")
    )

    week.index = idx
    return week.drop(columns=["dow", "hour"])


def load_typical_week_by_availability(
    country: str,
    path: str,
    variable_map: dict,
    anchor_year: int = 2023,
) -> dict:
    """
    Returns:
        { availability: DataFrame(168h × techs) }
    """

    df = pd.read_csv(path)
    df = _clean_long_df(df)

    lookup = _build_stack_lookup(
        df=df,
        country=country,
        variable_map=variable_map,
        anchor_year=anchor_year,
    )

    typical_week_by_avail = {
        avail: _select_typical_week(df_year, f"{anchor_year}-01-01")
        for avail, df_year in lookup.items()
    }

    return typical_week_by_avail
