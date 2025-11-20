import pandas as pd
import matplotlib.pyplot as plt

path = r"C:\Users\barna\OneDrive\Documents\data\caiso\caiso_fuel_mix_may_range.csv"

df = pd.read_csv(path)
df["Time"] = pd.to_datetime(df["Time"])
df = df.set_index("Time")

df.index = df.index.tz_convert("America/Los_Angeles").tz_localize(None)

day = "2025-05-01"
day_df = df.loc[day].copy()

# Positive values = discharge
day_df["Battery Discharge"] = day_df["Batteries"].clip(lower=0)

# Negative values (charging) → make positive
day_df["Battery Charge"] = (-day_df["Batteries"].clip(upper=0))

# Build the clean stack AFTER creating the new columns
stack = pd.DataFrame({
    "Nuclear": day_df["Nuclear"],
    "Hydro": day_df["Small Hydro"] + day_df["Large Hydro"],
    "Wind": day_df["Wind"],
    "Solar": day_df["Solar"],
    "Battery Discharge": day_df["Battery Discharge"],
    "Battery Charge": day_df["Battery Charge"],
    "Gas": day_df["Natural Gas"],
    "Imports": day_df["Imports"]
})

# Ensure a consistent 5-minute index, fill gaps
stack = stack.resample("5min").mean().ffill().fillna(0)

# enforce order
order = ["Nuclear", "Hydro", "Wind", "Solar",
         "Battery Discharge", "Battery Charge",
         "Gas", "Imports"]

stack = stack[order]

colors = {
    "Solar": "#FFE082",
    "Battery Discharge": "#FB8C00",   # orange
    "Battery Charge": "#FFB74D",      # lighter orange
    "Wind": "#90CAF9",
    "Hydro": "#64B5F6",
    "Gas": "#B0BEC5",
    "Imports": "#CFD8DC",
    "Nuclear": "#B3E5FC"
}

# Plot
fig, ax = plt.subplots(figsize=(14, 6))
ax.stackplot(
    stack.index,
    [stack[col] for col in order],
    labels=order,
    colors=[colors[col] for col in order],
    alpha=0.95
)

ax.spines["right"].set_visible(False)
ax.spines["top"].set_visible(False)
ax.grid(alpha=0.2)

ax.set_ylabel("megawatts", fontsize=12)
ax.set_xlabel("")
ax.set_title("How California powered itself", fontsize=18, weight="bold")
ax.legend(loc="upper left", frameon=False)
plt.tight_layout()
plt.show()
