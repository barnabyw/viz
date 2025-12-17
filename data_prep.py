import pandas as pd
from pathlib import Path

# =========================
# Configuration
# =========================

OTHER_RENEWABLE_COLS = ["Biomass", "Biogas", "Geothermal"]

# =========================
# Loaders
# =========================

def load_caiso(path):
    df = pd.read_csv(path)
    df["Time"] = pd.to_datetime(df["Time"])
    df = df.set_index("Time")
    df.index = df.index.tz_convert("America/Los_Angeles").tz_localize(None)
    return df


def load_caiso_folder(path):
    """
    Loads all CSV files in a folder containing yearly CAISO fuel mix data.
    """
    folder = Path(path)
    csvs = sorted(folder.glob("*.csv"))

    if not csvs:
        raise FileNotFoundError(f"No CSV files found in: {path}")

    df_list = []

    for file in csvs:
        df = pd.read_csv(file)
        df["Time"] = pd.to_datetime(df["Time"])
        df = df.set_index("Time")
        df_list.append(df)

    df = pd.concat(df_list).sort_index()
    return df


# =========================
# Helpers
# =========================

def add_other_renewables(df):
    """
    Explicitly aggregates Biomass, Biogas, Geothermal
    into a single 'Other' column.
    """
    df = df.copy()
    existing = [c for c in OTHER_RENEWABLE_COLS if c in df.columns]
    df["Other"] = df[existing].sum(axis=1)
    return df


# =========================
# Stack builders
# =========================

def make_three_month_avg_stack(df, start_month):
    start = pd.Timestamp(start_month)
    end = start + pd.DateOffset(months=3)

    period = add_other_renewables(df.loc[start:end])

    period["Battery Discharge"] = period["Batteries"].clip(lower=0)
    period["Battery Charge"] = 0

    stack = pd.DataFrame({
        "Nuclear": period["Nuclear"],
        "Hydro": period["Small Hydro"] + period["Large Hydro"],
        "Wind": period["Wind"],
        "Solar": period["Solar"],
        "Other": period["Other"],
        "Battery Discharge": period["Battery Discharge"],
        "Battery Charge": period["Battery Charge"],
        "Imports": period["Imports"],
        "Gas": period["Natural Gas"],
    })

    # Build average daily profile
    stack = stack.resample("5min").mean().ffill()
    stack = stack.groupby(stack.index.time).mean()
    stack.index = pd.date_range(start, periods=len(stack), freq="5min")

    order = [
        "Nuclear", "Wind", "Solar",
        "Battery Discharge", "Other", "Battery Charge",
        "Imports", "Hydro", "Gas"
    ]

    return stack[order], order


def make_trailing_year_stack(df, end_date, window_days=365):
    end_date = pd.Timestamp(end_date)
    start_date = end_date - pd.Timedelta(days=window_days)

    period = add_other_renewables(df.loc[start_date:end_date])

    period["Battery Discharge"] = period["Batteries"].clip(lower=0)
    period["Battery Charge"] = 0

    stack = pd.DataFrame({
        "Nuclear": period["Nuclear"],
        "Hydro": period["Small Hydro"] + period["Large Hydro"],
        "Wind": period["Wind"],
        "Solar": period["Solar"],
        "Other": period["Other"],
        "Battery Discharge": period["Battery Discharge"],
        "Battery Charge": period["Battery Charge"],
        "Imports": period["Imports"],
        "Gas": period["Natural Gas"],
    })

    stack = stack.resample("5min").mean().ffill()
    stack = stack.groupby(stack.index.time).mean()
    stack.index = pd.date_range(end_date.normalize(), periods=len(stack), freq="5min")

    order = [
        "Nuclear", "Wind", "Solar",
        "Battery Discharge",  "Other", "Battery Charge",
        "Imports", "Hydro", "Gas"
    ]

    return stack[order], order


# =========================
# Solar + BESS share
# =========================

def trailing_solar_bess_share(df, end_date, window_days=365):
    """
    Computes trailing-window % of load served by:
    - Solar
    - Battery discharge
    """
    end_date = pd.Timestamp(end_date)
    start_date = end_date - pd.Timedelta(days=window_days)

    period = add_other_renewables(df.loc[start_date:end_date])

    period["Load_total"] = (
        period["Nuclear"] +
        period["Small Hydro"] + period["Large Hydro"] +
        period["Wind"] +
        period["Solar"] +
        period["Other"] +
        period["Batteries"].clip(lower=0) +
        period["Imports"] +
        period["Natural Gas"]
    )

    period["Solar_gen"] = period["Solar"]
    period["BESS_gen"] = period["Batteries"].clip(lower=0)

    dt_hours = 5 / 60
    solar_mwh = period["Solar_gen"].sum() * dt_hours
    bess_mwh = period["BESS_gen"].sum() * dt_hours
    load_mwh = period["Load_total"].sum() * dt_hours

    return {
        "solar": 100 * solar_mwh / load_mwh,
        "bess": 100 * bess_mwh / load_mwh,
        "total": 100 * (solar_mwh + bess_mwh) / load_mwh,
    }


# =========================
# Main
# =========================

if __name__ == "__main__":

    years = range(2019, 2026)
    share_by_year = {}

    data_path = r"C:\Users\barna\OneDrive\Documents\data\caiso\raw_years"
    df = load_caiso_folder(data_path)

    for y in years:
        end_date = f"{y}-11-15"
        share_by_year[y] = trailing_solar_bess_share(df, end_date)

    results_df = pd.DataFrame.from_dict(share_by_year, orient="index")
    results_df.index.name = "year"
    results_df.reset_index(inplace=True)

    print(results_df)

    results_df.to_csv(
        r"C:\Users\barna\OneDrive\Documents\Solar_BESS\output\cali_solar_bess_share.csv",
        index=False
    )
