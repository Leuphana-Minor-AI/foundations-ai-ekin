import requests
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from datetime import datetime

# ECB 90 day historical data
url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
response = requests.get(url)
root = ET.fromstring(response.content)

NS = "{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube"

# Choose which currencies to track
TRACK = ["USD", "GBP", "JPY", "TRY", "CHF"]

# Collect data
history = {c: {"dates": [], "rates": []} for c in TRACK}

for time_cube in root.iter(NS):
    date = time_cube.attrib.get("time")
    if not date:
        continue
    for rate_cube in time_cube:
        currency = rate_cube.attrib.get("currency")
        rate = rate_cube.attrib.get("rate")
        if currency in TRACK:
            history[currency]["dates"].append(datetime.strptime(date, "%Y-%m-%d"))
            history[currency]["rates"].append(float(rate))

# Sort by date
for c in TRACK:
    pairs = sorted(zip(history[c]["dates"], history[c]["rates"]))
    history[c]["dates"] = [p[0] for p in pairs]
    history[c]["rates"] = [p[1] for p in pairs]

# Plot
fig, axes = plt.subplots(len(TRACK), 1, figsize=(14, 3 * len(TRACK)))
fig.suptitle("EUR Exchange Rates — Last 90 Days (ECB)", fontsize=14)

for i, currency in enumerate(TRACK):
    ax = axes[i]
    ax.plot(history[currency]["dates"], history[currency]["rates"],
            color="steelblue", linewidth=1.5)
    ax.set_title(f"EUR / {currency}")
    ax.set_ylabel("Rate")
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis="x", rotation=45)

plt.tight_layout()
plt.savefig("ecb_history.png", dpi=150)
plt.show()

print("Chart saved → ecb_history.png")