import requests
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
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

# STEP 2: ARIMA(1,1,1) - captures trend better
model = ARIMA(rates, order=(1, 1, 1))
fitted = model.fit()
print("Model trained!")

# STEP 3: Forecast
forecast = fitted.get_forecast(steps=90)
predicted_mean = np.array(forecast.predicted_mean)
conf_int = np.array(forecast.conf_int(alpha=0.05))
lower_ci = conf_int[:, 0]
upper_ci = conf_int[:, 1]

future_dates = [dates[-1] + timedelta(days=i+1) for i in range(90)]

# STEP 4: Calculate daily change stats
daily_changes = np.diff(rates)
avg_change = np.mean(daily_changes[-14:])  # last 14 days trend
std_change = np.std(daily_changes)

print(f"\nRecent trend: {avg_change:+.5f} per day")
print(f"Volatility:   ±{std_change:.5f}")

# STEP 5: Plot
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# --- Top chart: Full view ---
ax1 = axes[0]
ax1.plot(dates, rates, color="steelblue", linewidth=2, label="Historical (90 days)")
ax1.plot(future_dates, predicted_mean, color="red", linewidth=2,
         linestyle="--", label="ARIMA(1,1,1) Prediction")
ax1.fill_between(future_dates, lower_ci, upper_ci,
                 color="red", alpha=0.15, label="95% confidence interval")
ax1.axvline(x=dates[-1], color="gray", linestyle=":", linewidth=1.5)
ax1.text(dates[-1], min(rates) + 0.001, "  Today", color="gray", fontsize=9)
ax1.set_title(f"EUR / {CURRENCY} — ARIMA Prediction (Next 90 Days)")
ax1.set_ylabel("Rate vs EUR")
ax1.legend()
ax1.grid(True, alpha=0.3)

# --- Bottom chart: Daily changes ---
ax2 = axes[1]
ax2.bar(dates[1:], daily_changes, color=["green" if x > 0 else "red" for x in daily_changes],
        alpha=0.6, label="Daily change")
ax2.axhline(y=0, color="black", linewidth=0.8)
ax2.axhline(y=avg_change, color="orange", linewidth=1.5,
            linestyle="--", label=f"14-day avg trend: {avg_change:+.5f}")
ax2.set_title("Daily Rate Changes")
ax2.set_ylabel("Change")
ax2.set_xlabel("Date")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("prediction.png", dpi=150)
plt.show()

print(f"\nARIMA(1,1,1) Prediction for EUR/{CURRENCY}:")
print(f"  Today:      {rates[-1]:.4f}")
print(f"  In 30 days: {predicted_mean[29]:.4f}")
print(f"  In 60 days: {predicted_mean[59]:.4f}")
print(f"  In 90 days: {predicted_mean[89]:.4f}")
print(f"\nChart saved → prediction.png")