import requests
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# STEP 1: Fetch data
url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
response = requests.get(url)
root = ET.fromstring(response.content)
NS = "{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube"
CURRENCY = "USD"

dates, rates = [], []
for time_cube in root.iter(NS):
    date = time_cube.attrib.get("time")
    if not date:
        continue
    for rate_cube in time_cube:
        if rate_cube.attrib.get("currency") == CURRENCY:
            dates.append(datetime.strptime(date, "%Y-%m-%d"))
            rates.append(float(rate_cube.attrib["rate"]))

pairs = sorted(zip(dates, rates))
dates = [p[0] for p in pairs]
rates = [p[1] for p in pairs]
print(f"Data loaded: {len(rates)} days of EUR/{CURRENCY}")

# STEP 2: Calculate log returns and volatility
rates_arr = np.array(rates)
log_returns = np.diff(np.log(rates_arr))
mu = np.mean(log_returns)       # daily drift
sigma = np.std(log_returns)     # daily volatility

print(f"Daily drift:      {mu:+.6f}")
print(f"Daily volatility: {sigma:.6f}")

# STEP 3: Monte Carlo simulation (500 paths)
np.random.seed(42)
n_simulations = 500
n_days = 90
last_price = rates[-1]

simulations = np.zeros((n_simulations, n_days))
for i in range(n_simulations):
    prices = [last_price]
    for _ in range(n_days - 1):
        shock = np.random.normal(mu, sigma)
        prices.append(prices[-1] * np.exp(shock))
    simulations[i] = prices

future_dates = [dates[-1] + timedelta(days=i+1) for i in range(n_days)]

# Percentiles
p5  = np.percentile(simulations, 5,  axis=0)
p25 = np.percentile(simulations, 25, axis=0)
p50 = np.percentile(simulations, 50, axis=0)
p75 = np.percentile(simulations, 75, axis=0)
p95 = np.percentile(simulations, 95, axis=0)

# STEP 4: Plot
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# --- Top: Monte Carlo ---
ax1 = axes[0]

# Plot a sample of simulation paths
for i in range(0, 500, 5):
    ax1.plot(future_dates, simulations[i], color="red", alpha=0.03, linewidth=0.5)

# Confidence bands
ax1.fill_between(future_dates, p5,  p95, color="red",    alpha=0.10, label="90% range")
ax1.fill_between(future_dates, p25, p75, color="red",    alpha=0.20, label="50% range")
ax1.plot(future_dates, p50, color="darkred", linewidth=2,
         linestyle="--", label="Median prediction")

# Historical
ax1.plot(dates, rates, color="steelblue", linewidth=2, label="Historical (90 days)")
ax1.axvline(x=dates[-1], color="gray", linestyle=":", linewidth=1.5)
ax1.text(dates[-1], min(rates) + 0.001, "  Today", color="gray", fontsize=9)

ax1.set_title(f"EUR / {CURRENCY} — Monte Carlo Simulation (500 paths, Next 90 Days)")
ax1.set_ylabel("Rate vs EUR")
ax1.legend(loc="upper left")
ax1.grid(True, alpha=0.3)
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

# --- Bottom: Daily returns ---
ax2 = axes[1]
colors = ["green" if x > 0 else "red" for x in log_returns]
ax2.bar(dates[1:], log_returns, color=colors, alpha=0.6, label="Daily log return")
ax2.axhline(y=0, color="black", linewidth=0.8)
ax2.axhline(y=mu, color="orange", linewidth=2,
            linestyle="--", label=f"Mean drift: {mu:+.6f}")
ax2.axhline(y=sigma, color="purple", linewidth=1.5,
            linestyle=":", label=f"Volatility: ±{sigma:.6f}")
ax2.axhline(y=-sigma, color="purple", linewidth=1.5, linestyle=":")
ax2.set_title("Daily Log Returns")
ax2.set_ylabel("Log Return")
ax2.set_xlabel("Date")
ax2.legend()
ax2.grid(True, alpha=0.3)
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

plt.tight_layout()
plt.savefig("prediction.png", dpi=150)
plt.show()

print(f"\nMonte Carlo Prediction for EUR/{CURRENCY}:")
print(f"  Today:          {last_price:.4f}")
print(f"  In 30 days:")
print(f"    Bearish (5%): {p5[29]:.4f}")
print(f"    Median:       {p50[29]:.4f}")
print(f"    Bullish (95%):{p95[29]:.4f}")
print(f"  In 90 days:")
print(f"    Bearish (5%): {p5[89]:.4f}")
print(f"    Median:       {p50[89]:.4f}")
print(f"    Bullish (95%):{p95[89]:.4f}")
print(f"\nChart saved → prediction.png")