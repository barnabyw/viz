from data_prep import load_caiso, make_three_month_avg_stack
from animation import animate_smooth_yearly_transition
from plotting import COLOURS

import pandas as pd

if __name__ == "__main__":

    df = load_caiso(
        r"C:\Users\barna\OneDrive\Documents\data\caiso\caiso_fuel_mix_may_range.csv"
    )

    start_months = [
        "2019-04-01", "2020-04-01", "2021-04-01",
        "2022-04-01", "2023-04-01", "2024-04-01", "2025-04-01"
    ]

    periods = []
    for month in start_months:
        stack, order = make_three_month_avg_stack(df, month)
        year = pd.Timestamp(month).year
        periods.append((stack, order, year))

    fps = 50
    pause_seconds = {
        2019: 0.4,
        2020: 0.4,
        2021: 0.4,
        2022: 0.4,
        2023: 0.6,
        2024: 1.0,
        2025: 2
    }

    animate_smooth_yearly_transition(
        periods=periods,
        fps=fps,
        transition_seconds=0.2,
        pause_seconds=pause_seconds,
    )
