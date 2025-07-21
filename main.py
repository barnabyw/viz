import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplotlib.animation import FuncAnimation
from config import GRAPHICS_CONFIG

plt.style.use('dark_background')  # Set dark background globally

class Series:
    def __init__(self, df, y_col, x_col="year"):
        self.name = y_col
        self.data = df[[x_col, y_col]].dropna().to_numpy()
        self.x_col = x_col
        self.y_col = y_col
        self.params = None
        self.exp_func = None

    def fit_exponential(self, start_year, end_year):
        mask = (self.data[:, 0] >= start_year) & (self.data[:, 0] <= end_year)
        x_data = self.data[mask][:, 0]
        y_data = self.data[mask][:, 1]
        x0 = x_data[0]

        def exp_func(x, a, b):
            return a * np.exp(b * (x - x0))

        self.params, _ = curve_fit(exp_func, x_data, y_data, maxfev=10000)
        self.exp_func = exp_func

class Plotter:
    def __init__(self, title="", subtitle="", ylabel="", start_year=None, end_year=None):
        self.title = title
        self.subtitle = subtitle
        self.ylabel = ylabel
        self.series_list = []
        self.global_start_year = start_year
        self.global_end_year = end_year

    # Removed axis parameter here
    def add_series(self, series, start_year=None, end_year=None, color=None):
        self.series_list.append({
            'series': series,
            'start_year': start_year,
            'end_year': end_year,
            'color': color
        })

    def plot(self, font = 'Bahnschrift'):
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(20, 7.5))

        default_color = '#66c2ff'

        for entry in self.series_list:
            series = entry['series']
            start_year = entry['start_year'] or self.global_start_year
            end_year = entry['end_year'] or self.global_end_year
            color = entry['color'] or default_color

            x_real = series.data[:, 0]
            y_real = series.data[:, 1]

            ax.plot(x_real, y_real, 'o-', label=f'{series.name}', color=color, markerfacecolor=color)

            if series.exp_func and series.params is not None:
                x_proj = np.linspace(start_year, end_year, 100)
                y_proj = series.exp_func(x_proj, *series.params)
                ax.plot(x_proj, y_proj, '--', color=color)

            # Annotate last point
            ax.annotate(
                text=series.name,
                xy=(x_real[-1], y_real[-1]),
                textcoords='offset points',
                xytext=(5, -4),
                fontsize=13,
                color=color
            )

        # Remove y-axis label and spines for clean look
        ax.set_ylabel(self.ylabel)
        for spine in ['right', 'top']:
            ax.spines[spine].set_visible(False)

        # Only horizontal grid lines
        ax.grid(axis='y', alpha=0.3)
        ax.grid(axis='x', visible=False)

        # Axis labels
        ax.set_xlabel("Year")

        # Title and subtitle
        plt.text(0.125, 0.90, self.title, fontname=font, fontsize=20, ha='left', transform=fig.transFigure)
        plt.text(0.125, 0.86, self.subtitle, fontname=font, fontsize=16, ha='left', transform=fig.transFigure)

        fig.add_artist(plt.Line2D(
            [0.1, 0.9], [0.87, 0.87],
            transform=fig.transFigure,
            clip_on=False,
            color='white',
            linewidth=1.5
        ))

        # Footnote
        plt.text(0.1, 0.05, "Source: Example Data", fontname=font, fontstyle='italic',
                 fontsize=12, ha='left', transform=fig.transFigure)

        plt.subplots_adjust(top=0.8, wspace=0.3)
        plt.show()

def animate_to_log(plotter, series_obj):
    config = GRAPHICS_CONFIG
    fig, ax = plt.subplots(figsize=config["figsize"])
    ax.set_facecolor(config["colors"]["background"])
    # Extract and trim data
    x = series_obj.data[:, 0]
    y = series_obj.data[:, 1]
    # Use start/end year from plotter or series entry
    start_year = plotter.global_start_year or x.min()
    end_year = plotter.global_end_year or x.max()
    mask = (x >= start_year) & (x <= end_year)
    x, y = x[mask], y[mask]
    # Plot line
    (line,) = ax.plot(x, y, 'o-', color=config["colors"]['left'], lw=config["line_width"],
                      markerfacecolor=config["colors"]['left'])
    # Log ticks
    log_ticks = np.array(config["log_ticks"])
    log_tick_labels = [str(t) for t in log_ticks]
    ax.set_yticks(log_ticks)
    ax.set_yticklabels(log_tick_labels)
    ax.grid(True, axis='y', which='major', linestyle='--', alpha=0.4)
    ax.set_xlabel(series_obj.x_col, fontsize=14)
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(y.min(), y.max())
    # Precomputed eased time steps
    frames = config["animation"]["frames"]
    duration_ms = config["animation"]["duration_ms"]
    ease = config["animation"]["easing"]
    t_values = [ease(i / (frames - 1)) for i in range(frames)]
    t_values = (np.array(t_values) - min(t_values)) / (max(t_values) - min(t_values))

    def log_interp(y_vals, t):
        return (1 - t) * y_vals + t * np.log10(y_vals)

    def animate(i):
        t = t_values[i]
        y_interp = log_interp(y, t)
        line.set_ydata(y_interp)
        tick_interp = log_interp(log_ticks, t)
        ax.set_yticks(tick_interp)
        ax.set_yticklabels(log_tick_labels)
        ax.set_ylim(y_interp.min(), y_interp.max())
        return line,

    def finalize_log_scale():
        ax.set_yscale('log')
        line.set_ydata(y)
        ax.set_yticks(log_ticks)
        ax.set_yticklabels(log_tick_labels)
        ax.set_ylim(y.min(), y.max())
        fig.canvas.draw_idle()

    anim = FuncAnimation(fig, animate, frames=frames,
                         interval=duration_ms / frames, blit=False, repeat=False)

    def on_animation_end(*args):
        finalize_log_scale()

    anim._stop = lambda: (FuncAnimation._stop(anim), on_animation_end())[0]

    plt.tight_layout()
    plt.show()

# === MAIN SCRIPT ===

# 1. Load the data
data_path = r"C:\Users\barna\downloads\\"
file_name = "solars mad one.csv"
df = pd.read_csv(data_path + file_name)

# Create Series objects
solar = Series(df, "generation_twh")
demand = Series(df, "global demand")

# Fit exponential curves
solar.fit_exponential(2015, 2030)
demand.fit_exponential(2005, 2015)

plotter = Plotter(
    title="Solar Generation vs Global Demand",
    ylabel="Generation (TWh)",
    start_year=2010,
    end_year=2030
)

plotter.add_series(solar, start_year=2010, end_year=2030)

# Plot everything
# plotter.plot()

# Animate
animate_to_log(plotter, solar)
