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
# 1. DATA HANDLING FOR RECORD-DAY DATA
# =============================================================
def prepare_stack(sub):
    """
    Build the canonical stack columns from whatever raw columns exist.
    Handles both your CAISO raw columns and pre-aggregated ones.
    """

    idx = sub.index

    # Nuclear
    nuclear = sub["Nuclear"] if "Nuclear" in sub.columns else pd.Series(0.0, index=idx)

    # Hydro: either "Hydro" or ("Small Hydro" + "Large Hydro")
    if "Hydro" in sub.columns:
        hydro = sub["Hydro"]
    elif "Small Hydro" in sub.columns and "Large Hydro" in sub.columns:
        hydro = sub["Small Hydro"] + sub["Large Hydro"]
    else:
        hydro = pd.Series(0.0, index=idx)

    # Wind
    wind = sub["Wind"] if "Wind" in sub.columns else pd.Series(0.0, index=idx)

    # Solar
    solar = sub["Solar"] if "Solar" in sub.columns else pd.Series(0.0, index=idx)

    # Batteries → Battery Discharge / Charge
    if "Battery Discharge" in sub.columns:
        batt_discharge = sub["Battery Discharge"]
    elif "Batteries" in sub.columns:
        batt_discharge = sub["Batteries"].clip(lower=0)
    else:
        batt_discharge = pd.Series(0.0, index=idx)

    if "Battery Charge" in sub.columns:
        batt_charge = sub["Battery Charge"]
    else:
        batt_charge = pd.Series(0.0, index=idx)

    # Imports
    imports = sub["Imports"] if "Imports" in sub.columns else pd.Series(0.0, index=idx)

    # Gas: either "Gas" or "Natural Gas"
    if "Gas" in sub.columns:
        gas = sub["Gas"]
    elif "Natural Gas" in sub.columns:
        gas = sub["Natural Gas"]
    else:
        gas = pd.Series(0.0, index=idx)

    stack = pd.DataFrame({
        "Nuclear": nuclear,
        "Hydro": hydro,
        "Wind": wind,
        "Solar": solar,
        "Battery Discharge": batt_discharge,
        "Battery Charge": batt_charge,
        "Imports": imports,
        "Gas": gas,
    }, index=idx)

    order = [
        "Nuclear",
        "Wind",
        "Solar",
        "Battery Discharge",
        "Battery Charge",
        "Imports",
        "Hydro",
        "Gas",
    ]

    return stack[order], order


def build_year_stacks(df):
    """
    Expects df with:
      - datetime index (Time)
      - CAISO-style raw columns (Nuclear, Small/Large Hydro, Wind, Solar, Batteries, Imports, Natural Gas, etc.)
    Automatically infers years from the index.

    Returns list of (stack_df, order, year)
    """

    # Ensure datetime index
    dt_index = pd.to_datetime(df.index)
    df = df.copy()
    df.index = dt_index

    years = sorted(dt_index.year.unique())

    periods = []
    for yr in years:
        mask = dt_index.year == yr
        sub = df.loc[mask].copy()
        if sub.empty:
            continue

        stack, order = prepare_stack(sub)
        periods.append((stack, order, yr))

    return periods


# =============================================================
# 2. INTERPOLATION BETWEEN YEARS
# =============================================================
def interpolate_stacks(stack_a, stack_b, n_steps):
    # Align columns just in case
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


# =============================================================
# 3. BUILD SEQUENCE USING SECONDS + FPS
# =============================================================
def build_sequence_of_frames(periods, fps, transition_seconds, pause_seconds):
    all_frames = []
    titles = []

    transition_frames = int(transition_seconds * fps)

    for i, (stack, order, year) in enumerate(periods):

        # Year-specific static hold (default 2 seconds if not specified)
        pause_frames = int(pause_seconds.get(year, 2.0) * fps)

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
# 4. PLOTTING
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

    # --- FIXED: SQUARE SHAPE ---
    ax.set_box_aspect(1)


# =============================================================
# 5. ANIMATION
# =============================================================
def animate_smooth_yearly_transition(df, colors,
                                     fps=30,
                                     transition_seconds=1.5,
                                     pause_seconds=None):

    if pause_seconds is None:
        pause_seconds = {}

    fig, ax = plt.subplots(figsize=(8, 8))

    # Build one stack per year automatically from the Time index
    periods = build_year_stacks(df)

    frames, titles, order = build_sequence_of_frames(
        periods, fps, transition_seconds, pause_seconds
    )

    def update(i):
        plot_stack(ax, frames[i], order, colors, titles[i])

    anim = FuncAnimation(
        fig,
        update,
        frames=len(frames),
        interval=1000 / fps,   # 30 FPS
        repeat=True,
        blit=False,
    )

    plt.show()
    return anim


# =============================================================
# 6. MAIN
# =============================================================
if __name__ == "__main__":

    # df should have:
    #   - a "Time" column with datetimes (one record day per year)
    #   - CAISO-style columns (Nuclear, Small/Large Hydro, Wind, Solar, Batteries, Imports, Natural Gas, etc.)
    path = r"C:\Users\barna\OneDrive\Documents\data\caiso\record_days\caiso_record_days_all_years.csv"
    df = pd.read_csv(path)

    df["Time"] = pd.to_datetime(df["Time"])
    df = df.set_index("Time")

    # If your Time index is tz-aware, you can strip the tz like this:
    if df.index.tz is not None:
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

    animate_smooth_yearly_transition(
        df,
        colors,
        fps=50,
        transition_seconds=0.25,
        pause_seconds={
            2018: 0.4,
            2019: 0.4,
            2020: 0.4,
            2021: 0.4,
            2022: 0.4,
            2023: 0.8,
            2024: 0.8,
            2025: 3
        },
    )