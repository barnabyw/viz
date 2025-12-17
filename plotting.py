import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np

# ---------------------------------------------------------------
# FONT + COLOUR PRESETS (LOADED ON IMPORT)
# ---------------------------------------------------------------

font_dir = r"C:\Users\barna\AppData\Local\Microsoft\Windows\Fonts"

regular_path = fr"{font_dir}\Montserrat-Regular.ttf"
medium_path  = fr"{font_dir}\Montserrat-Medium.ttf"
bold_path    = fr"{font_dir}\Montserrat-Bold.ttf"

fm.fontManager.addfont(regular_path)
fm.fontManager.addfont(medium_path)
fm.fontManager.addfont(bold_path)

FONT_REGULAR = fm.FontProperties(fname=regular_path)
FONT_MEDIUM  = fm.FontProperties(fname=medium_path)
FONT_BOLD    = fm.FontProperties(fname=bold_path)

COLOURS = {
    # Keep original hero colours
    "Solar": '#FFBB00', # "#FFE082",
    "Battery Discharge": "#0F9ED5", #'#375E97',  # 1995AD', #"#FB8C00",
    # All others as light greys (ordered light → dark)
    "Nuclear": "#F2F2F2",
    "Wind": "#E0E0E0",
    "Battery Charge": "#CDCDCD",
    "Other": "#D6D6D6",
    "Imports": "#BBBBBB",
    "Hydro": "#A7A7A7",
    "Gas": "#919191",
}

# ---------------------------------------------------------------
# STACKED AREA CHART PLOT
# ---------------------------------------------------------------
def plot_stack(ax, stack, order, title, ylim=None):
    #ax.clear()

    axis_line_col = "#CCCCCC"
    text_col = "#555555"

    stack_gw = stack / 1000.0

    ax.stackplot(
        stack_gw.index,
        [stack_gw[col] for col in order],
        colors=[COLOURS[c] for c in order],
        alpha=0.95,
    )

    ax.text(-0.12, 1.06,
            title, transform=ax.transAxes, ha="left", va="bottom",
            fontproperties=FONT_MEDIUM, fontsize=18, color=text_col)

    # y-axis formatting
    if ylim is not None:
        ax.set_ylim(ylim)
    else:
        total = stack_gw.sum(axis=1)
        ymax = total.max()
        ax.set_ylim(0, ymax * 1.05)

    ticks = ax.get_yticks()
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:g} GW" for t in ticks])

    # x-axis: 6 AM, 12 PM, 6 PM
    desired = ["06:00", "12:00", "18:00"]
    xticks = [t for t in stack_gw.index if t.strftime("%H:%M") in desired]
    ax.set_xticks(xticks)
    ax.set_xticklabels(["6 AM", "12 PM", "6 PM"])

    ax.tick_params(axis="both", colors=axis_line_col)

    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(axis_line_col)

    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    # Tick font
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(FONT_MEDIUM)
        label.set_fontsize(13)
        label.set_color(text_col)

    ax.grid(color="#E5E5E5", linewidth=0.8, alpha=0.25)
    ax.set_facecolor("#FAFAFA")
    ax.margins(x=0)
    ax.set_box_aspect(1)

# ---------------------------------------------------------------
# SIMPLE LINE PLOT
# ---------------------------------------------------------------
def plot_line(ax, series, title):
    ax.clear()
    ax.plot(series.index, series.values, linewidth=2)
    ax.set_title(title, fontproperties=FONT_BOLD)
    ax.set_xlabel("Date", fontproperties=FONT_MEDIUM)
    ax.set_ylabel(series.name, fontproperties=FONT_MEDIUM)
    ax.grid(alpha=0.3)

if __name__ == "__main__":
    # Fake 5-min index
    idx = pd.date_range("2024-01-01", periods=288, freq="5min")

    # Fake data with realistic magnitudes (MW)
    stack_test = pd.DataFrame({
        "Nuclear": 2200 + 0*idx.hour,
        "Wind": 800 + 200*np.sin(np.linspace(0, 2*np.pi, len(idx))),
        "Solar": np.clip(3000*np.sin(np.linspace(-np.pi/2, 3*np.pi/2, len(idx))), 0, None),
        "Other": 400,
        "Battery Discharge": 300*np.exp(-((idx.hour-19)/3)**2),
        "Battery Charge": 0,
        "Imports": 600,
        "Hydro": 900,
        "Gas": 1800,
    }, index=idx)

    order = [
        "Nuclear", "Wind", "Solar",
        "Battery Discharge", "Other",
        "Imports", "Hydro", "Gas"
    ]

    fig, ax = plt.subplots(figsize=(8, 8))
    plot_stack(ax, stack_test, order, "Test Stack – Colour Check", ylim=(0, 30))
    plt.show()
