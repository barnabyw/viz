import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.font_manager as fm
from matplotlib.animation import FFMpegWriter


# -------------------------------------------------------------
# FONT SETUP (Montserrat)

font_dir = r"C:\Users\barna\AppData\Local\Microsoft\Windows\Fonts"

regular_path = fr"{font_dir}\Montserrat-Regular.ttf"
medium_path  = fr"{font_dir}\Montserrat-Medium.ttf"
bold_path    = fr"{font_dir}\Montserrat-Bold.ttf"
italic_path  = fr"{font_dir}\Montserrat-Italic.ttf"

fm.fontManager.addfont(regular_path)
fm.fontManager.addfont(medium_path)
fm.fontManager.addfont(bold_path)
fm.fontManager.addfont(italic_path)

mont_regular = fm.FontProperties(fname=regular_path)
mont_medium  = fm.FontProperties(fname=medium_path)
mont_bold    = fm.FontProperties(fname=bold_path)
mont_italic  = fm.FontProperties(fname=italic_path)

plt.rcParams['font.family'] = mont_regular.get_name()
plt.rcParams['font.weight'] = 'regular'

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


def build_sequence_of_frames(periods, fps, transition_seconds, pause_seconds):
    all_frames = []
    titles = []

    transition_frames = int(transition_seconds * fps)

    for i, (stack, order, year) in enumerate(periods):

        # YEAR-SPECIFIC PAUSE
        pause_frames = int(pause_seconds.get(year, 2) * fps)

        for _ in range(pause_frames):
            all_frames.append(stack)
            titles.append(f"{year}")

        # Transition to next year
        if i < len(periods) - 1:
            next_stack, _, next_year = periods[i + 1]
            intermediates = interpolate_stacks(stack, next_stack, transition_frames)

            for frame in intermediates:
                all_frames.append(frame)
                titles.append(f"{year} → {next_year}")

    return all_frames, titles, order



# =============================================================
# 2. CHART DESIGN
# =============================================================
def plot_stack(ax, stack, order, colors, title):

    ax.clear()

    axis_line_col = "#CCCCCC"  # lighter grey (spines + tick marks)
    text_col = "#555555"  # darker grey (numbers + labels + title)

    # Convert MW → GW
    stack_gw = stack / 1000.0

    # Stackplot
    ax.stackplot(
        stack_gw.index,
        [stack_gw[col] for col in order],
        colors=[colors[c] for c in order],
        alpha=0.95,
    )

    # TITLE — use Montserrat Bold
    ax.set_title(
        title,
        fontproperties=mont_bold,
        fontsize=20,
        color=text_col
    )

    # ---- Y-AXIS ----
    total = stack_gw.sum(axis=1)
    ymax = total.max()
    ax.set_ylim(0, ymax * 1.05)

    ticks = ax.get_yticks()
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:g} GW" for t in ticks])

    # ---- X-AXIS ----
    desired = ["06:00", "12:00", "18:00"]
    tick_positions = [t for t in stack_gw.index if t.strftime("%H:%M") in desired]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(["6 AM", "12 PM", "6 PM"])

    # ---- AXIS + TICK COLOURS ----
    ax.tick_params(axis="both", colors=axis_line_col)

    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(axis_line_col)
        ax.spines[spine].set_linewidth(1)

    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    # ---- FORCE MONTSERRAT MEDIUM ON TICK LABELS ----
    for label in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        label.set_fontproperties(mont_medium)
        label.set_fontsize(13)
        label.set_color(text_col)

    # GRID + BG
    ax.grid(color="#E5E5E5", linewidth=0.8, alpha=0.25)
    ax.set_facecolor("#FAFAFA")
    ax.margins(x=0)

    # Square aspect
    ax.set_box_aspect(1)

# =============================================================
# 3. ANIMATION
# =============================================================
def animate_smooth_yearly_transition(df, start_months, colors,
                                     fps=30,
                                     transition_seconds=1.5,
                                     pause_seconds=None):

    if pause_seconds is None:
        pause_seconds = {}

    fig, ax = plt.subplots(figsize=(8, 8))

    # Build stacks for each start month
    periods = []
    for month in start_months:
        stack, order = make_three_month_avg_stack(df, month)
        yr = pd.Timestamp(month).year
        periods.append((stack, order, yr))

    # Build the master frame list
    frames, titles, order = build_sequence_of_frames(
        periods, fps, transition_seconds, pause_seconds
    )

    def update(i):
        plot_stack(ax, frames[i], order, colors, titles[i])

    anim = FuncAnimation(
        fig,
        update,
        frames=len(frames),
        interval=1000 / fps,   # << 30 FPS exact timing
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

    # ——— New timing parameters ———
    fps = 50
    transition_seconds = 0.25
    pause_seconds = {
        2021: 0.75,
        2022: 0.5,
        2023: 0.5,
        2024: 1.5,
        2025: 3,
    }

    animate_smooth_yearly_transition(
        df,
        start_months,
        colors,
        fps=fps,
        transition_seconds=transition_seconds,
        pause_seconds=pause_seconds,
    )

