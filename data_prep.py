import pandas as pd
from pathlib import Path

"""
OTHER NEEDS FIXING
"""

def load_caiso(path):
    df = pd.read_csv(path)
    df["Time"] = pd.to_datetime(df["Time"])
    df = df.set_index("Time")
    df.index = df.index.tz_convert("America/Los_Angeles").tz_localize(None)
    return df

def load_caiso_folder(path):
    """
    Loads all CSV files in a folder containing yearly CAISO fuel mix data.
    Assumes each CSV contains columns like:
    Time, Solar, Wind, Nuclear, Natural Gas, ...
    """

    folder = Path(path)
    csvs = sorted(folder.glob("*.csv"))

    if not csvs:
        raise FileNotFoundError(f"No CSV files found in: {path}")

    df_list = []
    for file in csvs:
        df = pd.read_csv(file)

        # Fix the Time column
        df["Time"] = pd.to_datetime(df["Time"])
        df = df.set_index("Time")
        #df.index = df.index.tz_convert("America/Los_Angeles").tz_localize(None)

        df_list.append(df)

    df = pd.concat(df_list).sort_index()
    return df

def make_three_month_avg_stack(df, start_month):
    start = pd.Timestamp(start_month)
    end = start + pd.DateOffset(months=3)

    period = df.loc[start:end].copy()

    period["Battery Discharge"] = period["Batteries"].clip(lower=0)
    period["Battery Charge"] = 0

    stack = pd.DataFrame({
        "Nuclear": period["Nuclear"],
        "Hydro": period["Small Hydro"] + period["Large Hydro"],
        "Wind": period["Wind"],
        "Solar": period["Solar"],
        "Battery Discharge": period["Battery Discharge"],
        "Battery Charge": period["Battery Charge"],
        "Imports": period["Imports"],
        "Gas": period["Natural Gas"],
    })

    # Resample and make a daily "average profile"
    stack = stack.resample("5min").mean().ffill()
    stack = stack.groupby(stack.index.time).mean()
    stack.index = pd.date_range(start, periods=len(stack), freq="5min")

    order = ["Nuclear", "Wind", "Solar",
             "Battery Discharge", "Battery Charge",
             "Imports", "Hydro", "Gas"]

    return stack[order], order


def make_trailing_year_stack(df, end_date, window_days=365):
    """
    Builds a daily average stack profile for the trailing N days.
    end_date: a Timestamp (the last day included in the window)
    """

    end_date = pd.Timestamp(end_date)
    start_date = end_date - pd.Timedelta(days=window_days)

    period = df.loc[start_date:end_date].copy()

    # Same transformations as your 3-month version
    period["Battery Discharge"] = period["Batteries"].clip(lower=0)
    period["Battery Charge"] = 0

    stack = pd.DataFrame({
        "Nuclear": period["Nuclear"],
        "Hydro": period["Small Hydro"] + period["Large Hydro"],
        "Wind": period["Wind"],
        "Solar": period["Solar"],
        "Battery Discharge": period["Battery Discharge"],
        "Battery Charge": period["Battery Charge"],
        "Imports": period["Imports"],
        "Gas": period["Natural Gas"],
    })

    # Same daily profile averaging
    stack = stack.resample("5min").mean().ffill()
    stack = stack.groupby(stack.index.time).mean()

    # Rebuild a fake daily index (exactly as your monthly code does)
    stack.index = pd.date_range(end_date.normalize(), periods=len(stack), freq="5min")

    order = [
        "Nuclear", "Wind", "Solar",
        "Battery Discharge", "Battery Charge",
        "Imports", "Hydro", "Gas"
    ]

    return stack[order], order

def trailing_solar_bess_share(df, end_date, window_days=365):
    """
    Computes the trailing-12-month % of load served by Solar + Battery Discharge.
    LOAD = sum of all positive generation sources (supply-side load).
    """

    end_date = pd.Timestamp(end_date)
    start_date = end_date - pd.Timedelta(days=window_days)

    # Slice the period
    period = df.loc[start_date:end_date].copy()

    # Compute load (total supply)
    period["Load_total"] = (
        period["Nuclear"] +
        period["Small Hydro"] + period["Large Hydro"] +
        period["Wind"] +
        period["Solar"] +
        period["Batteries"].clip(lower=0) +    # discharge only
        period["Imports"] +
        period["Natural Gas"]
    )

    # Components of interest
    period["Solar_gen"] = period["Solar"]
    period["BESS_gen"] = period["Batteries"].clip(lower=0)

    # Integrate energy over time (5-min data)
    # Multiply MW by 5/60 hours to get MWh
    dt_hours = 5/60

    solar_mwh = (period["Solar_gen"].sum() * dt_hours)
    bess_mwh  = (period["BESS_gen"].sum() * dt_hours)
    load_mwh  = (period["Load_total"].sum() * dt_hours)

    pct = 100 * (solar_mwh + bess_mwh) / load_mwh

    return pct

if __name__ == "__main__":
    years = range(2019, 2026)
    share_by_year = {}

    data_path = r"C:\Users\barna\OneDrive\Documents\data\caiso\raw_years"
    df = load_caiso_folder(data_path)

    for y in years:
        end_date = f"{y}-11-15"
        share_by_year[y] = trailing_solar_bess_share(df, end_date)

    print(share_by_year)