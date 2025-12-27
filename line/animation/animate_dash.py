import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from line.plots.double import build_dashboard

# --------------------------------------------------
# Build figure + axes (layout only)
# --------------------------------------------------
fig = plt.figure(figsize=(19.2, 16.2), dpi=100)

gs = fig.add_gridspec(
    3, 1,
    height_ratios=[1, 1, 1],
    left=0.08,
    right=0.80,
    top=0.94,
    bottom=0.08,
    hspace=0.30,
)

ax_top = fig.add_subplot(gs[0, 0])
ax_mid = fig.add_subplot(gs[1, 0])
ax_bot = fig.add_subplot(gs[2, 0])

update, availabilities = build_dashboard(fig, (ax_top, ax_mid, ax_bot))

# --------------------------------------------------
# Animate (2 per second)
# --------------------------------------------------
anim = FuncAnimation(
    fig,
    update,
    frames=availabilities,
    interval=500,
    repeat=True,
)

output = r"C:\Users\barna\OneDrive\Documents\Solar_BESS\Good charts\video\availability_loop2.mp4"

anim.save(
    output,
    writer="ffmpeg",
    fps=2,
    dpi=200,
)

print(f"Saved animation to {output}")
