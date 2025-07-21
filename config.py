GRAPHICS_CONFIG = {
    "figsize": (16, 9),  # Widescreen aspect for presentations
    "line_width": 2.5,
    "colors": {
        "background": "#111111",         # Deep charcoal
        "left_axis": "#4FC3F7",          # Bright sky blue
        "right_axis": "#FF8A65",         # Warm coral
        "title": "#FFFFFF",              # White title text
        "subtitle": "#CCCCCC",           # Light grey subtitle
        "annotation": "#DDDDDD",         # Slightly muted for readability
        "grid": "#444444"                # Subtle gridlines
    },
    "log_ticks": [1, 10, 100, 1_000, 10_000, 100_000, 1_000_000],
    "animation": {
        "frames": 60,
        "duration_ms": 2000,
        "easing": lambda t: t**2 * (3 - 2 * t)  # Smoothstep easing for nicer visual transitions
    },
    "fonts": {
        "main": "Bahnschrift",
        "fallback": "DejaVu Sans"
    }
}
