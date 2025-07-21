import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplotlib.animation import FuncAnimation
from config import GRAPHICS_CONFIG

plt.style.use('dark_background')


class Series:
    def __init__(self, df, y_col, x_col="year"):
        self.name = y_col
        self.data = df[[x_col, y_col]].dropna().to_numpy()
        self.exp_func = None
        self.params = None

    def fit_exponential(self, start_year, end_year):
        mask = (self.data[:, 0] >= start_year) & (self.data[:, 0] <= end_year)
        x_data, y_data = self.data[mask][:, 0], self.data[mask][:, 1]
        x0 = x_data[0]

        def exp_func(x, a, b): return a * np.exp(b * (x - x0))
        self.params, _ = curve_fit(exp_func, x_data, y_data, maxfev=10000)
        self.exp_func = exp_func


class Plotter:
    def __init__(self, title="", subtitle="", ylabel="", start_year=None, end_year=None):
        self.title = title
        self.subtitle = subtitle
        self.ylabel = ylabel
        self.series_list = []
        self.start_year = start_year
        self.end_year = end_year

    def add_series(self, series, start_year=None, end_year=None, color=None):
        self.series_list.append({
            'series': series,
            'start_year': start_year or self.start_year,
            'end_year': end_year or self.end_year,
            'color': color
        })

    def _setup_axes(self, animated=False):
        figsize = GRAPHICS_CONFIG["figsize"] if animated else (20, 7.5)
        fig, ax = plt.subplots(figsize=figsize)
        if animated:
            ax.set_facecolor(GRAPHICS_CONFIG["colors"]["background"])
        return fig, ax

    def _style_axes(self, fig, ax, animated=False, font='Bahnschrift'):
        for spine in ['left', 'right', 'top']:
            ax.spines[spine].set_visible(False)

        ax.set_xlabel("Year")
        if not animated:
            ax.grid(axis='y', alpha=0.3)
            ax.grid(axis='x', visible=False)

            # Title block
            plt.text(0.125, 0.90, self.title, fontname=font, fontsize=20, ha='left', transform=fig.transFigure)
            plt.text(0.125, 0.86, self.subtitle, fontname=font, fontsize=16, ha='left', transform=fig.transFigure)
            fig.add_artist(plt.Line2D([0.1, 0.9], [0.87, 0.87], transform=fig.transFigure, clip_on=False, color='white', linewidth=1.5))
            plt.text(0.125, 0.82, self.ylabel, fontname=font, fontsize=14, ha='left', transform=fig.transFigure, color='#66c2ff')
            plt.text(0.1, 0.05, "Source: Example Data", fontname=font, fontstyle='italic', fontsize=12, ha='left', transform=fig.transFigure)
            plt.subplots_adjust(top=0.8)
        return '#66c2ff'

    def plot(self, font='Bahnschrift'):
        fig, ax = self._setup_axes(animated=False)
        default_color = self._style_axes(fig, ax, animated=False, font=font)

        for entry in self.series_list:
            series = entry['series']
            color = entry['color'] or default_color
            x, y = series.data[:, 0], series.data[:, 1]
            ax.plot(x, y, 'o-', label=series.name, color=color, markerfacecolor=color)

            if series.exp_func:
                x_proj = np.linspace(entry['start_year'], entry['end_year'], 100)
                y_proj = series.exp_func(x_proj, *series.params)
                ax.plot(x_proj, y_proj, '--', color=color)

            ax.annotate(series.name, xy=(x[-1], y[-1]), xytext=(5, -4), textcoords='offset points', fontsize=13, color=color)

        plt.show()

    def animate_to_log(self, series_names=None, font='Bahnschrift'):
        fig, ax = self._setup_axes(animated=True)
        default_color = self._style_axes(fig, ax, animated=True, font=font)

        entries = [e for e in self.series_list if
                   (series_names is None or
                    (isinstance(series_names, str) and e['series'].name == series_names) or
                    (isinstance(series_names, list) and e['series'].name in series_names))]

        if not entries:
            raise ValueError("No matching series found for animation.")

        animation_data, all_y_values = [], []
        for entry in entries:
            s, color = entry['series'], entry['color'] or default_color
            x, y = s.data[:, 0], s.data[:, 1]
            mask = (x >= entry['start_year']) & (x <= entry['end_year'])
            x, y = x[mask], y[mask]
            line, = ax.plot(x, y, 'o-', lw=GRAPHICS_CONFIG["line_width"], color=color, markerfacecolor=color)

            proj_line, y_proj = None, None
            if s.exp_func:
                x_proj = np.linspace(entry['start_year'], entry['end_year'], 100)
                y_proj = s.exp_func(x_proj, *s.params)
                proj_line, = ax.plot(x_proj, y_proj, '--', color=color)

            animation_data.append({'line': line, 'proj_line': proj_line, 'x': x, 'y': y,
                                   'x_proj': x_proj if s.exp_func else None, 'y_proj': y_proj})
            all_y_values.extend(y)
            if y_proj is not None:
                all_y_values.extend(y_proj)

        log_ticks = np.array(GRAPHICS_CONFIG["log_ticks"])
        ax.set_yticks(log_ticks)
        ax.set_yticklabels([str(t) for t in log_ticks])
        ax.set_xlim(min(np.concatenate([d['x'] for d in animation_data])), max(np.concatenate([d['x'] for d in animation_data])))

        frames = GRAPHICS_CONFIG["animation"]["frames"]
        duration_ms = GRAPHICS_CONFIG["animation"]["duration_ms"]
        ease = GRAPHICS_CONFIG["animation"]["easing"]
        t_values = np.array([ease(i / (frames - 1)) for i in range(frames)])
        t_values = (t_values - t_values.min()) / (t_values.max() - t_values.min())

        def log_interp(y_vals, t): return (1 - t) * y_vals + t * np.log10(y_vals)

        def animate(i):
            t = t_values[i]
            ax.set_yticks(log_interp(log_ticks, t))
            ax.set_yticklabels([str(tick) for tick in log_ticks])

            all_current_y = []
            for data in animation_data:
                y_i = log_interp(data['y'], t)
                data['line'].set_ydata(y_i)
                all_current_y.extend(y_i)
                if data['proj_line']:
                    y_proj_i = log_interp(data['y_proj'], t)
                    data['proj_line'].set_ydata(y_proj_i)
                    all_current_y.extend(y_proj_i)

            if all_current_y:
                ax.set_ylim(min(all_current_y), max(all_current_y))

            return [d['line'] for d in animation_data] + [d['proj_line'] for d in animation_data if d['proj_line']]

        def finalize_log_scale():
            ax.set_yscale('log')
            ax.set_yticks(log_ticks)
            ax.set_yticklabels([str(t) for t in log_ticks])
            if all_y_values:
                ax.set_ylim(min(all_y_values), max(all_y_values))
            fig.canvas.draw_idle()

        anim = FuncAnimation(fig, animate, frames=frames, interval=duration_ms / frames, blit=False, repeat=False)
        anim._stop = lambda: (FuncAnimation._stop(anim), finalize_log_scale())[0]

        plt.tight_layout()
        plt.show()
        return anim


# === MAIN SCRIPT ===
data_path = r"C:\Users\barna\downloads\\"
file_name = "solars mad one.csv"
df = pd.read_csv(data_path + file_name)

solar = Series(df, "generation_twh")
solar.fit_exponential(2015, 2030)

plotter = Plotter(
    title="Solar Generation vs Global Demand",
    ylabel="Generation (TWh)",
    start_year=2010,
    end_year=2030
)

plotter.add_series(solar)
# plotter.plot()  # Static
plotter.animate_to_log("generation_twh")  # Animated log
