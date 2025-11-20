import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplotlib.animation import FuncAnimation

plt.style.use('dark_background')


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


class AnimatedPlotter:
    def __init__(self, title="", subtitle="", ylabel="", start_year=None, end_year=None):
        self.title = title
        self.subtitle = subtitle
        self.ylabel = ylabel
        self.series_list = []
        self.global_start_year = start_year
        self.global_end_year = end_year

    def add_series(self, series, start_year=None, end_year=None, color=None):
        self.series_list.append({
            'series': series,
            'start_year': start_year,
            'end_year': end_year,
            'color': color or '#66c2ff'
        })

    def animate_plot(self, font='Bahnschrift ', frames=60, duration_ms=2000):
        fig, ax = plt.subplots(figsize=(20, 7.5))
        ax.set_position([0.15, 0.15, 0.6, 0.7])

        # Store all plot elements for animation
        lines = []
        projection_lines = []
        annotations = []

        # Default log ticks for animation
        log_ticks = np.array([1, 10, 100, 1000, 10000, 100000])
        log_tick_labels = [str(t) for t in log_ticks]

        for entry in self.series_list:
            series = entry['series']
            start_year = entry['start_year'] or self.global_start_year
            end_year = entry['end_year'] or self.global_end_year
            color = entry['color']

            # Get data within range
            x_real = series.data[:, 0]
            y_real = series.data[:, 1]

            if start_year or end_year:
                mask = True
                if start_year:
                    mask = mask & (x_real >= start_year)
                if end_year:
                    mask = mask & (x_real <= end_year)
                x_real = x_real[mask]
                y_real = y_real[mask]

            # Create line
            line, = ax.plot(x_real, y_real, 'o-', color=color,
                            markerfacecolor=color, linewidth=2, markersize=6)
            lines.append((line, x_real, y_real))

            # Add projection if available
            if series.exp_func and series.params is not None:
                x_proj = np.linspace(start_year, end_year, 100)
                y_proj = series.exp_func(x_proj, *series.params)
                proj_line, = ax.plot(x_proj, y_proj, '--', color=color, alpha=0.7)
                projection_lines.append((proj_line, x_proj, y_proj))

            # Skip annotations for now
            # annotations.append(None)

        # Style the plot with your design
        ax.set_ylabel(self.ylabel, fontsize=14)
        ax.set_xlabel("Year", fontsize=14)

        for spine in ['right', 'top']:
            ax.spines[spine].set_visible(False)

        ax.grid(axis='y', alpha=0.3)
        ax.grid(axis='x', visible=False)

        # Title and subtitle
        plt.text(0, 1.15, self.title, fontname=font, fontsize=20,
                 ha='left', transform=ax.transAxes)
        plt.text(0, 1.10, self.subtitle, fontname=font, fontsize=16,
                 ha='left', transform=ax.transAxes)

        # Set initial limits including projections
        all_y = np.concatenate([y for _, _, y in lines])
        if projection_lines:
            proj_y = np.concatenate([y_proj for _, _, y_proj in projection_lines])
            all_y = np.concatenate([all_y, proj_y])
        y_min, y_max = all_y.min(), all_y.max()
        ax.set_ylim(y_min, y_max)

        # Animation easing function
        def ease_in_out_cubic(t):
            return 3 * t ** 2 - 2 * t ** 3

        # Precompute eased time values
        t_values = [ease_in_out_cubic(i / (frames - 1)) for i in range(frames)]
        t_values = np.array(t_values)

        def log_interp(y_vals, t):
            """Interpolate between linear and log scale"""
            return (1 - t) * y_vals + t * np.log10(np.maximum(y_vals, 1e-10))

        def animate(frame):
            t = t_values[frame]

            # Update all data lines
            y_interp_all = []
            for line, x_data, y_data in lines:
                y_interp = log_interp(y_data, t)
                line.set_ydata(y_interp)
                y_interp_all.extend(y_interp)

            # Update projection lines with same transformation
            for proj_line, x_proj, y_proj in projection_lines:
                y_proj_interp = log_interp(y_proj, t)
                proj_line.set_ydata(y_proj_interp)
                y_interp_all.extend(y_proj_interp)

            # Update y-axis ticks
            valid_ticks = log_ticks[log_ticks <= y_max]
            tick_interp = log_interp(valid_ticks, t)
            ax.set_yticks(tick_interp)
            ax.set_yticklabels([str(int(tick)) for tick in valid_ticks])

            # Update y-limits
            y_interp_all = np.array(y_interp_all)
            ax.set_ylim(y_interp_all.min() * 0.9, y_interp_all.max() * 1.1)

            return [line for line, _, _ in lines] + [proj_line for proj_line, _, _ in projection_lines]

        def finalize_animation():
            """Set final log scale after animation"""
            ax.set_yscale('log')
            for line, x_data, y_data in lines:
                line.set_ydata(y_data)

            # Reset projection lines to original data
            for proj_line, x_proj, y_proj in projection_lines:
                proj_line.set_ydata(y_proj)

            valid_ticks = log_ticks[(log_ticks >= y_min) & (log_ticks <= y_max)]
            ax.set_yticks(valid_ticks)
            ax.set_yticklabels([str(int(tick)) for tick in valid_ticks])
            ax.set_ylim(y_min, y_max)
            fig.canvas.draw_idle()

        # Create and run animation
        anim = FuncAnimation(fig, animate, frames=frames,
                             interval=duration_ms / frames, blit=False, repeat=False)

        # Finalize after animation completes
        def on_animation_complete(event):
            finalize_animation()

        anim.event_source.stop()
        anim = FuncAnimation(fig, animate, frames=frames,
                             interval=duration_ms / frames, blit=False, repeat=False)

        #plt.subplots_adjust(top=0.8, left=0.125, right=0.9)
        #plt.tight_layout()
        plt.show()

        # Auto-finalize after animation
        fig.canvas.mpl_connect('draw_event', lambda evt:
        plt.get_current_fig_manager().window.after(
            duration_ms + 100, finalize_animation)
        if hasattr(plt.get_current_fig_manager(), 'window') else None)

        return anim


# === USAGE EXAMPLE ===
if __name__ == "__main__":
    # Load data (replace with your actual path)
    data_path = r"C:\Users\barna\downloads\\"
    file_name = "solar5.csv"
    df = pd.read_csv(data_path + file_name)

    # Create series
    solar = Series(df, "generation_twh")

    # Fit exponential curves
    solar.fit_exponential(2015, 2030)

    # Create plotter
    plotter = AnimatedPlotter(
        title= "Solar growth",
        subtitle="GW global capacity",
        start_year=2010,
        end_year=2035
    )

    # Add series (you can add both if needed)
    plotter.add_series(solar, color='#66c2ff')
    bloomberg_solar = Series(df, "bloomberg")
    plotter.add_series(bloomberg_solar, start_year=2022, end_year=2030, color='#ff4444')
    # plotter.add_series(demand, color='#ff6b6b')

    # Run animated plot
    plotter.animate_plot()