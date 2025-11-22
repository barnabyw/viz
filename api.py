import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# =============================================================
# 1. DATA PREPARATION
# =============================================================

def make_three_month_avg_stack(df, start_month):
    """
    Compute 3-month average dispatch profile averaged by time-of-day.
    Returns (stack_df, ordered_cols).
    """
    start = pd.Timestamp(start_month)
    end = start + pd.DateOffset(months=3)

    period = df.loc[start:end].copy()

    # Split battery charge/discharge
    period["Battery Discharge"] = period["Batteries"].clip(lower=0)
    period["Battery Charge"] = 0 #(-period["Batteries"].clip(upper=0))

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

    # Ensure 5-minute spacing
    stack = stack.resample("5min").mean().ffill()

    # Average each time-of-day over all days
    stack = stack.groupby(stack.index.time).mean()

    # Recreate datetime index for plotting
    stack.index = pd.date_range(start, periods=len(stack), freq="5min")

    order = [
        "Nuclear", "Wind", "Solar",
        "Battery Discharge", "Battery Charge",  "Imports", "Hydro", "Gas"
    ]

    return stack[order], order


def interpolate_stacks(stack_a, stack_b, n_steps):
    """
    Generate n_steps interpolated stacks between stack_a → stack_b,
    ignoring index alignment issues by working on the underlying arrays.
    """
    # Make sure columns are in the same order
    if not stack_a.columns.equals(stack_b.columns):
        stack_b = stack_b[stack_a.columns]

    # They *should* have the same shape because of your pipeline,
    # but it's good to be defensive:
    assert stack_a.shape == stack_b.shape, "Stacks must have same shape for interpolation"

    values_a = stack_a.to_numpy()
    values_b = stack_b.to_numpy()

    frames = []
    for i in range(1, n_steps + 1):
        alpha = i / (n_steps + 1)   # 0 < alpha < 1 for pure intermediates
        interp_vals = (1 - alpha) * values_a + alpha * values_b

        interp_df = pd.DataFrame(
            interp_vals,
            index=stack_a.index,      # reuse one consistent index
            columns=stack_a.columns,
        )
        frames.append(interp_df)

    return frames



def build_sequence_of_frames(periods, transition_frames):
    """
    Given [(stack_year1, order, year), (stack_year2,...), ...]
    Create the full ordered list of frames including:
    - each yearly stack
    - smooth transitions to the next year
    """
    all_frames = []
    titles = []

    for i, (stack, order, year) in enumerate(periods):
        # Always include the start-of-year frame
        all_frames.append(stack)
        titles.append(f"{year}")

        # If not the last period, interpolate to next
        if i < len(periods) - 1:
            next_stack, _, next_year = periods[i+1]

            intermediates = interpolate_stacks(
                stack, next_stack, n_steps=transition_frames
            )

            for frame in intermediates:
                # Title shows fractional movement toward next year
                titles.append(f"{year}")
                all_frames.append(frame)

    return all_frames, titles, order


# =============================================================
# 2. PLOTTING — Chart design in ONE place
# =============================================================

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

    # Clean look
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.grid(alpha=0.2)


# =============================================================
# 3. ANIMATION LOGIC — clean, readable
# =============================================================

def animate_smooth_yearly_transition(df, start_months, colors,
                                     transition_frames=20):
    """
    Build and animate smooth transitions between year-to-year
    dispatch averages.
    """
    fig, ax = plt.subplots(figsize=(14, 6))

    # Step 1 — compute AVERAGES
    periods = []
    for month in start_months:
        stack, order = make_three_month_avg_stack(df, month)
        yr = pd.Timestamp(month).year
        periods.append((stack, order, yr))

    # Step 2 — build all transitional frames
    frames, titles, order = build_sequence_of_frames(periods, transition_frames)

    # Step 3 — animation
    def update(i):
        plot_stack(ax, frames[i], order, colors, titles[i])

    anim = FuncAnimation(
        fig,
        update,
        frames=len(frames),
        interval=40,
        repeat=True,
    )

    plt.show()
    return anim


# =============================================================
# 4. MAIN
# =============================================================
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

    start_months = [
        "2021-04-01",
        "2022-04-01",
        "2023-04-01",
        "2024-04-01",
        "2025-04-01",
    ]

    animate_smooth_yearly_transition(
        df,
        start_months,
        colors,
        transition_frames=20   # 20 smooth steps between seasons
    )
