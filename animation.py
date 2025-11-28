import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
from tqdm import tqdm
from plotting import plot_stack, plot_line


# ---------------------------------------------------------
# INTERPOLATION BETWEEN STACKS
# ---------------------------------------------------------
def interpolate_stacks(stack_a, stack_b, n_steps):
    if not stack_a.columns.equals(stack_b.columns):
        stack_b = stack_b[stack_a.columns]

    a = stack_a.to_numpy()
    b = stack_b.to_numpy()

    frames = []
    for i in range(1, n_steps + 1):
        alpha = i / (n_steps + 1)
        values = (1 - alpha) * a + alpha * b
        frames.append(
            stack_a.__class__(values, index=stack_a.index, columns=stack_a.columns)
        )

    return frames


# ---------------------------------------------------------
# ANIMATION: YEARLY STACK TRANSITION
# ---------------------------------------------------------
def animate_smooth_yearly_transition(periods, fps, transition_seconds, pause_seconds):

    fig, ax = plt.subplots(figsize=(8, 8))

    all_frames = []
    all_titles = []

    transition_frames = int(fps * transition_seconds)

    for i, (stack, order, year) in enumerate(periods):

        # pause on the year
        pframes = int(fps * pause_seconds.get(year, 1))
        for _ in range(pframes):
            all_frames.append(stack)
            all_titles.append(f"{year}")

        # transition to next year
        if i < len(periods) - 1:
            next_stack, _, next_year = periods[i + 1]
            inter = interpolate_stacks(stack, next_stack, transition_frames)
            for f in inter:
                all_frames.append(f)
                all_titles.append(f"{year} → {next_year}")

    # Main animation update
    def update(i):
        # NOTE: colours and fonts handled INSIDE plot_stack()
        plot_stack(ax, all_frames[i], periods[0][1], all_titles[i])

    anim = FuncAnimation(
        fig,
        update,
        frames=len(all_frames),
        interval=1000 / fps,
        repeat=True
    )

    plt.show()
    return anim


# ---------------------------------------------------------
# ANIMATION: TRAILING 365-DAY ROLLING AVERAGE
# ---------------------------------------------------------
from data_prep import make_trailing_year_stack
from plotting import plot_stack

def animate_trailing_yearly_stack(df, fps=30, window_days=365):

    # one frame per day in the dataset
    all_days = pd.date_range(df.index.min() + pd.Timedelta(days=window_days),
                             df.index.max(), freq="W")

    frames = []
    titles = []

    for day in tqdm(all_days, desc="Building trailing-year frames"):
        stack, order = make_trailing_year_stack(df, day, window_days)
        frames.append(stack)
        titles.append(f"Trailing {window_days}-Day Average up to {day.date()}")

    fig, ax = plt.subplots(figsize=(8, 8))

    def update(i):
        plot_stack(ax, frames[i], order, titles[i], ylim=(0,30))

    anim = FuncAnimation(
        fig,
        update,
        frames=len(frames),
        interval=1000 / fps,
        repeat=False
    )

    plt.show()
    return anim
