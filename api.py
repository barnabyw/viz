import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# -------------------------------------------------------------
# 1. PREP — Compute 3-month average stacked dataframe
# -------------------------------------------------------------
def make_three_month_avg_stack(df, start_month):
    """
    Given a start month (e.g., "2021-04"), compute the 3-month average
    profile (Apr, May, Jun), averaged by time-of-day.
    Returns: (stack_df, ordered_columns)
    """
    start = pd.Timestamp(start_month)
    end = start + pd.DateOffset(months=3)

    period = df.loc[start:end].copy()

    # split battery charge/discharge
    period["Battery Discharge"] = period["Batteries"].clip(lower=0)
    period["Battery Charge"] = (-period["Batteries"].clip(upper=0))

    stack = pd.DataFrame({
        "Nuclear": period["Nuclear"],
        "Hydro": period["Small Hydro"] + period["Large Hydro"],
        "Wind": period["Wind"],
        "Solar": period["Solar"],
        "Battery Discharge": period["Battery Discharge"],
        "Battery Charge": period["Battery Charge"],
        "Gas": period["Natural Gas"],
        "Imports": period["Imports"],
    })

    # Resample to consistent 5-minute spacing
    stack = stack.resample("5min").mean().ffill()

    # Average across all days by time-of-day
    stack = stack.groupby(stack.index.time).mean()

    # Recreate a datetime index (just for plotting)
    stack.index = pd.date_range(start, periods=len(stack), freq="5min")

    order = [
        "Nuclear", "Hydro", "Wind", "Solar",
        "Battery Discharge", "Battery Charge",
        "Gas", "Imports"
    ]
    return stack[order], order


# -------------------------------------------------------------
# 2. STATIC PLOT of a single frame in the animation
# -------------------------------------------------------------
def plot_stack(ax, stack, order, colors, title):
    ax.clear()

    ax.stackplot(
        stack.index,
        [stack[col] for col in order],
        colors=[colors[c] for c in order],
        alpha=0.95,
    )

    ax.set_title(title, fontsize=18, weight="bold")
    ax.set_ylabel("MW")
    ax.set_xlabel("")

    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.grid(alpha=0.2)


# -------------------------------------------------------------
# 3. ANIMATION — show Apr-May-Jun average per frame
# -------------------------------------------------------------
def animate_seasonal_averages(df, start_months, colors, frames_per_period=60):
    """
    For each starting month in 'start_months':
      - compute 3-month average stack (Apr-May-Jun)
      - display it for `frames_per_period` frames
    """
    fig, ax = plt.subplots(figsize=(14, 6))

    # Precompute all periods
    periods = []
    for month in start_months:
        stack, order = make_three_month_avg_stack(df, month)
        year = pd.Timestamp(month).year
        periods.append((stack, order, year))

    total_frames = len(periods) * frames_per_period

    def update(frame_idx):
        period_idx = frame_idx // frames_per_period  # which period to show

        stack, order, year = periods[period_idx]

        plot_stack(
            ax,
            stack,
            order,
            colors,
            title=f"Apr-May-Jun {year} Average",
        )

    anim = FuncAnimation(
        fig,
        update,
        frames=total_frames,
        interval=20,  # 4x faster (was 80)
        repeat=True
    )

    plt.show()
    return anim


# -------------------------------------------------------------
# 4. MAIN SCRIPT — load data + call animation
# -------------------------------------------------------------
if __name__ == "__main__":
    path = r"C:\Users\barna\OneDrive\Documents\data\caiso\caiso_fuel_mix_may_range.csv"
    df = pd.read_csv(path)

    df["Time"] = pd.to_datetime(df["Time"])
    df = df.set_index("Time")
    df.index = df.index.tz_convert("America/Los_Angeles").tz_localize(None)

    colors = {
        "Solar": "#FFE082",
        "Battery Discharge": "#FB8C00",
        "Battery Charge": "#FFB74D",
        "Wind": "#90CAF9",
        "Hydro": "#64B5F6",
        "Gas": "#B0BEC5",
        "Imports": "#CFD8DC",
        "Nuclear": "#B3E5FC",
    }

    # Start of Apr-May-Jun period for each year
    start_months = [
        "2021-04-01",
        "2022-04-01",
        "2023-04-01",
        "2024-04-01",
        "2025-04-01",
    ]

    animate_seasonal_averages(df, start_months, colors, frames_per_period=20)