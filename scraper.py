import requests
import xml.etree.ElementTree as ET
import csv
import matplotlib.pyplot as plt
from datetime import datetime

# ECB XML API - direct exchange rates
url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
response = requests.get(url)

root = ET.fromstring(response.content)

currencies = []
values = []

for cube in root.iter("{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube"):
    if "currency" in cube.attrib and "rate" in cube.attrib:
        currencies.append(cube.attrib["currency"])
        values.append(float(cube.attrib["rate"]))

print(f"Found {len(currencies)} currencies")
for c, v in zip(currencies, values):
    print(f"{c:<8} {v}")

# Save to CSV
date = datetime.now().strftime("%Y-%m-%d")
with open(f"ecb_rates_{date}.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Currency", "Rate (EUR)"])
    writer.writerows(zip(currencies, values))

# Chart
plt.figure(figsize=(16, 6))
plt.bar(currencies, values, color="steelblue")
plt.yscale("log")
plt.title("EUR Exchange Rates (ECB)")
plt.xlabel("Currency")
plt.ylabel("Rate vs EUR")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("ecb_chart.png")
plt.show()

print("Done!")
