import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import font_manager

# -------------------------------------------------------------
# FONT SETUP (Montserrat)
# -------------------------------------------------------------
font_path = r"C:\Users\barna\AppData\Local\Microsoft\Windows\Fonts\Montserrat-VariableFont_wght.ttf"
font_manager.fontManager.addfont(font_path)

plt.rcParams['font.family'] = 'Montserrat'

# =============================================================
# 1. DATA PREPARATION
# =============================================================
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

    stack = stack.resample("5min").mean().ffill()
    stack = stack.groupby(stack.index.time).mean()
    stack.index = pd.date_range(start, periods=len(stack), freq="5min")

    order = ["Nuclear", "Wind", "Solar",
             "Battery Discharge", "Battery Charge",
             "Imports", "Hydro", "Gas"]

    return stack[order], order


def interpolate_stacks(stack_a, stack_b, n_steps):
    if not stack_a.columns.equals(stack_b.columns):
        stack_b = stack_b[stack_a.columns]

    values_a = stack_a.to_numpy()
    values_b = stack_b.to_numpy()

    frames = []
    for i in range(1, n_steps + 1):
        alpha = i / (n_steps + 1)
        interp_vals = (1 - alpha) * values_a + alpha * values_b
        frames.append(pd.DataFrame(interp_vals, index=stack_a.index, columns=stack_a.columns))

    return frames


def build_sequence_of_frames(periods, transition_frames, pause_frames):
    all_frames = []
    titles = []

    for i, (stack, order, year) in enumerate(periods):

        for _ in range(pause_frames):
            all_frames.append(stack)
            titles.append(f"{year}")

        if i < len(periods) - 1:
            next_stack, _, _ = periods[i + 1]
            intermediates = interpolate_stacks(stack, next_stack, n_steps=transition_frames)

            for frame in intermediates:
                all_frames.append(frame)
                titles.append(f"{year}")

    return all_frames, titles, order


# =============================================================
# 2. CHART DESIGN
# =============================================================
def plot_stack(ax, stack, order, colors, title):

    ax.clear()

    # Convert MW → GW
    stack_gw = stack / 1000.0

    # Stackplot
    ax.stackplot(
        stack_gw.index,
        [stack_gw[col] for col in order],
        colors=[colors[c] for c in order],
        alpha=0.95,
    )

    # TITLE
    ax.set_title(title, fontsize=20, weight="bold", color="#333333")

    # ---- Y-AXIS ----
    total = stack_gw.sum(axis=1)
    ymax = total.max()
    ax.set_ylim(0, ymax * 1.05)

    ticks = ax.get_yticks()
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:g} GW" for t in ticks], color="#777777")

    # ---- X-AXIS ----
    desired = ["06:00", "12:00", "18:00"]
    tick_positions = [t for t in stack_gw.index if t.strftime("%H:%M") in desired]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(["6 AM", "12 PM", "6 PM"], color="#777777")

    # SOFT STYLING
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("#AAAAAA")
        ax.spines[spine].set_linewidth(1)

    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    ax.grid(color="#E5E5E5", linewidth=0.8, alpha=0.25)
    ax.set_facecolor("#FAFAFA")
    ax.margins(x=0)

    # --- FIXED: SQUARE SHAPE (placed last so autoscaling works) ---
    ax.set_box_aspect(1)      # <--- THIS MUST BE LAST


# =============================================================
# 3. ANIMATION
# =============================================================
def animate_smooth_yearly_transition(df, start_months, colors,
                                     transition_frames=20,
                                     pause_frames=25):

    fig, ax = plt.subplots(figsize=(8, 8))

    periods = []
    for month in start_months:
        stack, order = make_three_month_avg_stack(df, month)
        yr = pd.Timestamp(month).year
        periods.append((stack, order, yr))

    frames, titles, order = build_sequence_of_frames(periods, transition_frames, pause_frames)

    def update(i):
        plot_stack(ax, frames[i], order, colors, titles[i])

    anim = FuncAnimation(
        fig, update,
        frames=len(frames),
        interval=40,
        repeat=True,
        blit=False,
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

    start_months = ["2021-04-01","2022-04-01","2023-04-01","2024-04-01","2025-04-01"]

    animate_smooth_yearly_transition(
        df,
        start_months,
        colors,
        transition_frames=20,
        pause_frames=30,
    )
