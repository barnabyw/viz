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
    def __init__(self, title="", subtitle="", ylabel_left="", ylabel_right="", start_year=None, end_year=None):
        self.title = title
        self.subtitle = subtitle
        self.ylabel_left = ylabel_left
        self.ylabel_right = ylabel_right
        self.series_list = []
        self.global_start_year = start_year
        self.global_end_year = end_year

    def add_series(self, series, start_year=None, end_year=None, axis='left', color=None):
        self.series_list.append({
            'series': series,
            'start_year': start_year,
            'end_year': end_year,
            'axis': axis,
            'color': color
        })

    def _setup_figure_and_axes(self, font='Bahnschrift', animated=False):
        if animated:
            config = GRAPHICS_CONFIG
            fig, ax_left = plt.subplots(figsize=config["figsize"])
            ax_left.set_facecolor(config["colors"]["background"])
        else:
            fig, ax_left = plt.subplots(figsize=(20, 7.5))
        ax_right = ax_left.twinx()
        return fig, ax_left, ax_right

    def _apply_styling(self, fig, ax_left, ax_right, font='Bahnschrift', animated=False):
        default_colors = {'left': '#66c2ff', 'right': '#ff6666'}
        used_axes = {'left': False, 'right': False}
        for entry in self.series_list:
            used_axes[entry['axis']] = True

        if not animated or len([e for e in self.series_list if used_axes[e['axis']]]) > 1:
            ax_left.set_ylabel("")
            ax_right.set_ylabel("")

        for spine in ['left', 'right', 'top']:
            ax_left.spines[spine].set_visible(False)
            ax_right.spines[spine].set_visible(False)

        if not animated:
            ax_left.grid(axis='y', alpha=0.3)
            ax_left.grid(axis='x', visible=False)

        ax_left.set_xlabel("Year")

        if not animated:
            plt.text(0.125, 0.90, self.title, fontname=font, fontsize=20, ha='left', transform=fig.transFigure)
            plt.text(0.125, 0.86, self.subtitle, fontname=font, fontsize=16, ha='left', transform=fig.transFigure)
            fig.add_artist(plt.Line2D([0.1, 0.9], [0.87, 0.87], transform=fig.transFigure, clip_on=False, color='white', linewidth=1.5))

            if used_axes['left']:
                plt.text(0.125, 0.82, self.ylabel_left, fontname=font, fontsize=14, ha='left', transform=fig.transFigure, color=default_colors['left'])
            if used_axes['right']:
                plt.text(0.875, 0.82, self.ylabel_right, fontname=font, fontsize=14, ha='right', transform=fig.transFigure, color=default_colors['right'])

            plt.text(0.1, 0.05, "Source: Example Data", fontname=font, fontstyle='italic', fontsize=12, ha='left', transform=fig.transFigure)
            plt.subplots_adjust(top=0.8, wspace=0.3)

        return default_colors

    def plot(self, font='Bahnschrift'):
        fig, ax_left, ax_right = self._setup_figure_and_axes(font, animated=False)
        default_colors = self._apply_styling(fig, ax_left, ax_right, font, animated=False)

        for entry in self.series_list:
            series = entry['series']
            start_year = entry['start_year'] or self.global_start_year
            end_year = entry['end_year'] or self.global_end_year
            axis = entry['axis']
            color = entry['color'] or default_colors[axis]

            x_real = series.data[:, 0]
            y_real = series.data[:, 1]
            ax = ax_left if axis == 'left' else ax_right
            ax.plot(x_real, y_real, 'o-', label=f'{series.name}', color=color, markerfacecolor=color)

            if series.exp_func and series.params is not None:
                x_proj = np.linspace(start_year, end_year, 100)
                y_proj = series.exp_func(x_proj, *series.params)
                ax.plot(x_proj, y_proj, '--', color=color)

            ax.annotate(
                text=series.name,
                xy=(x_real[-1], y_real[-1]),
                textcoords='offset points',
                xytext=(5, -4),
                fontsize=13,
                color=color
            )

        plt.show()

    def animate_to_log(self, series_names=None, font='Bahnschrift'):
        config = GRAPHICS_CONFIG
        if series_names is None:
            entries_to_animate = self.series_list
        elif isinstance(series_names, str):
            entry = next((e for e in self.series_list if e['series'].name == series_names), None)
            if not entry:
                raise ValueError(f"Series '{series_names}' not found")
            entries_to_animate = [entry]
        else:
            entries_to_animate = []
            for name in series_names:
                entry = next((e for e in self.series_list if e['series'].name == name), None)
                if not entry:
                    raise ValueError(f"Series '{name}' not found")
                entries_to_animate.append(entry)

        if not entries_to_animate:
            raise ValueError("No series found to animate")

        fig, ax_left, ax_right = self._setup_figure_and_axes(font, animated=True)
        default_colors = self._apply_styling(fig, ax_left, ax_right, font, animated=True)

        animation_data = []
        all_y_values = []

        for entry in entries_to_animate:
            series_obj = entry['series']
            axis = entry['axis']
            color = entry['color'] or default_colors[axis]
            ax = ax_left if axis == 'left' else ax_right

            x = series_obj.data[:, 0]
            y = series_obj.data[:, 1]
            start_year = entry['start_year'] or self.global_start_year or x.min()
            end_year = entry['end_year'] or self.global_end_year or x.max()
            mask = (x >= start_year) & (x <= end_year)
            x, y = x[mask], y[mask]

            line_width = config.get("line_width", 2)
            line, = ax.plot(x, y, 'o-', color=color, lw=line_width, markerfacecolor=color, label=series_obj.name)

            proj_line = None
            y_proj = None
            if series_obj.exp_func and series_obj.params is not None:
                x_proj = np.linspace(start_year, end_year, 100)
                y_proj = series_obj.exp_func(x_proj, *series_obj.params)
                proj_line, = ax.plot(x_proj, y_proj, '--', color=color)

            animation_data.append({
                'line': line,
                'proj_line': proj_line,
                'x': x,
                'y': y,
                'x_proj': x_proj if proj_line else None,
                'y_proj': y_proj,
                'ax': ax,
                'series': series_obj,
                'start_year': start_year,
                'end_year': end_year,
                'color': color
            })

            all_y_values.extend(y)
            if y_proj is not None:
                all_y_values.extend(y_proj)

        log_ticks = np.array(config["log_ticks"])
        log_tick_labels = [str(t) for t in log_ticks]

        for ax in [ax_left, ax_right]:
            ax.set_yticks(log_ticks)
            ax.set_yticklabels(log_tick_labels)

        all_x = np.concatenate([data['x'] for data in animation_data])
        ax_left.set_xlim(all_x.min(), all_x.max())
        ax_left.set_xlabel("Year", fontsize=14)

        frames = config["animation"]["frames"]
        duration_ms = config["animation"]["duration_ms"]
        ease = config["animation"]["easing"]
        t_values = [ease(i / (frames - 1)) for i in range(frames)]
        t_values = (np.array(t_values) - min(t_values)) / (max(t_values) - min(t_values))

        def log_interp(y_vals, t):
            return (1 - t) * y_vals + t * np.log10(y_vals)

        def animate(i):
            t = t_values[i]
            animated_objects = []
            for data in animation_data:
                y_interp = log_interp(data['y'], t)
                data['line'].set_ydata(y_interp)
                animated_objects.append(data['line'])
                if data['proj_line'] is not None:
                    y_proj_interp = log_interp(data['y_proj'], t)
                    data['proj_line'].set_ydata(y_proj_interp)
                    animated_objects.append(data['proj_line'])

            tick_interp = log_interp(log_ticks, t)
            for ax in [ax_left, ax_right]:
                ax.set_yticks(tick_interp)
                ax.set_yticklabels(log_tick_labels)

            all_current_y = []
            for data in animation_data:
                y_interp = log_interp(data['y'], t)
                all_current_y.extend(y_interp)
                if data['y_proj'] is not None:
                    y_proj_interp = log_interp(data['y_proj'], t)
                    all_current_y.extend(y_proj_interp)

            if all_current_y:
                y_min, y_max = min(all_current_y), max(all_current_y)
                for ax in [ax_left, ax_right]:
                    ax.set_ylim(y_min, y_max)

            return animated_objects

        def finalize_log_scale():
            for ax in [ax_left, ax_right]:
                ax.set_yscale('log')
                ax.set_yticks(log_ticks)
                ax.set_yticklabels(log_tick_labels)
            for data in animation_data:
                data['line'].set_ydata(data['y'])
                if data['proj_line'] is not None:
                    data['proj_line'].set_ydata(data['y_proj'])
            if all_y_values:
                y_min, y_max = min(all_y_values), max(all_y_values)
                for ax in [ax_left, ax_right]:
                    ax.set_ylim(y_min, y_max)
            fig.canvas.draw_idle()

        anim = FuncAnimation(fig, animate, frames=frames, interval=duration_ms / frames, blit=False, repeat=False)

        def on_animation_end(*args):
            finalize_log_scale()

        anim._stop = lambda: (FuncAnimation._stop(anim), on_animation_end())[0]

        plt.tight_layout()
        plt.show()
        return anim

# === MAIN SCRIPT ===
data_path = r"C:\Users\barnaby.winser\Documents\solar bes\input data\learning curves\\"
file_name = "solars mad one.csv"
df = pd.read_csv(data_path + file_name)

solar = Series(df, "generation_twh")
demand = Series(df, "global demand")

solar.fit_exponential(2015, 2030)
demand.fit_exponential(2005, 2015)

plotter = Plotter(
    title="Solar Generation vs Global Demand",
    ylabel_left="Generation (TWh)",
    start_year=2010,
    end_year=2030
)

plotter.add_series(solar, start_year=2010, end_year=2030, axis='left')

# Plot (static): plotter.plot()
# Animate (log scale):
plotter.animate_to_log("generation_twh")
