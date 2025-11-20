import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# -------------------------------------------------------------
# 1. PREP — Compute week-average stacked dataframe for a day
# -------------------------------------------------------------
def make_week_avg_stack(df, day):
    """
    Given a start day (string), compute the 7-day average profile,
    averaged by time-of-day across the week.
    Returns: (stack_df, ordered_columns)
    """
    start = pd.Timestamp(day)
    end = start + pd.Timedelta(days=31)

    week = df.loc[start:end].copy()

    # split battery charge/discharge
    week["Battery Discharge"] = week["Batteries"].clip(lower=0)
    week["Battery Charge"] = (-week["Batteries"].clip(upper=0))

    stack = pd.DataFrame({
        "Nuclear": week["Nuclear"],
        "Hydro": week["Small Hydro"] + week["Large Hydro"],
        "Wind": week["Wind"],
        "Solar": week["Solar"],
        "Battery Discharge": week["Battery Discharge"],
        "Battery Charge": week["Battery Charge"],
        "Gas": week["Natural Gas"],
        "Imports": week["Imports"],
    })

    # Resample to consistent 5-minute spacing
    stack = stack.resample("5min").mean().ffill()

    # Average across the 7 days by time-of-day
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
# 3. ANIMATION — show one week average per frame
# -------------------------------------------------------------
def animate_week_averages(df, days, colors, frames_per_week=30):
    """
    For each date in 'days':
      - compute 7-day average stack
      - display it for `frames_per_week` frames
    """
    fig, ax = plt.subplots(figsize=(14, 6))

    # Precompute all weeks
    weeks = []
    for d in days:
        stack, order = make_week_avg_stack(df, d)
        weeks.append((stack, order, d))

    total_frames = len(weeks) * frames_per_week

    def update(frame_idx):
        week_idx = frame_idx // frames_per_week  # which week to show

        stack, order, d = weeks[week_idx]

        plot_stack(
            ax,
            stack,
            order,
            colors,
            title=f"7-Day Average Starting {d}",
        )

    anim = FuncAnimation(
        fig,
        update,
        frames=total_frames,
        interval=20,
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

    # Start date for each year
    days = [
        "2019-05-01",
        "2020-05-01",
        "2021-05-01",
        "2022-05-01",
        "2023-05-01",
        "2024-05-01",
        "2025-05-01",
    ]

    animate_week_averages(df, days, colors, frames_per_week=60)