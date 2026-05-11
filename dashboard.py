import requests
import xml.etree.ElementTree as ET
from datetime import datetime

url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
response = requests.get(url)
root = ET.fromstring(response.content)

NS = "{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube"
TRACK = ["USD", "GBP", "JPY", "TRY", "CHF"]

history = {c: {"dates": [], "rates": []} for c in TRACK}

for time_cube in root.iter(NS):
    date = time_cube.attrib.get("time")
    if not date:
        continue
    for rate_cube in time_cube:
        currency = rate_cube.attrib.get("currency")
        rate = rate_cube.attrib.get("rate")
        if currency in TRACK:
            history[currency]["dates"].append(date)
            history[currency]["rates"].append(float(rate))

for c in TRACK:
    pairs = sorted(zip(history[c]["dates"], history[c]["rates"]))
    history[c]["dates"] = [p[0] for p in pairs]
    history[c]["rates"] = [p[1] for p in pairs]

def make_svg(dates, rates, color):
    w, h, pad = 500, 150, 10
    if not rates:
        return ""
    mn, mx = min(rates), max(rates)
    rng = mx - mn if mx != mn else 1
    pts = []
    for i, r in enumerate(rates):
        x = pad + i * (w - 2*pad) / (len(rates)-1)
        y = h - pad - (r - mn) / rng * (h - 2*pad)
        pts.append(f"{x:.1f},{y:.1f}")
    poly = " ".join(pts)
    first_x, first_y = pts[0].split(",")
    last_x, last_y = pts[-1].split(",")
    fill_pts = f"{first_x},{h-pad} " + poly + f" {last_x},{h-pad}"
    label_l = dates[0] if dates else ""
    label_m = dates[len(dates)//2] if dates else ""
    label_r = dates[-1] if dates else ""
    vl = f"{mn:.4f}"
    vh = f"{mx:.4f}"
    return f"""<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:150px">
  <polygon points="{fill_pts}" fill="{color}" opacity="0.15"/>
  <polyline points="{poly}" fill="none" stroke="{color}" stroke-width="2"/>
  <text x="{pad}" y="{h-1}" font-size="10" fill="#64748b">{label_l}</text>
  <text x="{w//2}" y="{h-1}" font-size="10" fill="#64748b" text-anchor="middle">{label_m}</text>
  <text x="{w-pad}" y="{h-1}" font-size="10" fill="#64748b" text-anchor="end">{label_r}</text>
  <text x="{pad}" y="{pad+10}" font-size="10" fill="#64748b">{vh}</text>
  <text x="{pad}" y="{h-pad-2}" font-size="10" fill="#64748b">{vl}</text>
</svg>"""

colors = {"USD": "#3b82f6", "GBP": "#8b5cf6", "JPY": "#f59e0b", "TRY": "#ef4444", "CHF": "#22c55e"}

cards_html = ""
charts_html = ""
today = datetime.now().strftime("%B %d, %Y")

for c in TRACK:
    rates = history[c]["rates"]
    dates = history[c]["dates"]
    if not rates:
        continue
    latest = rates[-1]
    change = round(rates[-1] - rates[0], 4)
    pct = round((change / rates[0]) * 100, 2)
    color = colors[c]
    sign = "+" if change >= 0 else ""
    chg_color = "#22c55e" if change >= 0 else "#ef4444"

    cards_html += f"""
    <div class="card">
        <div class="label">EUR / {c}</div>
        <div class="value">{latest}</div>
        <div class="change" style="color:{chg_color}">{sign}{change} ({sign}{pct}%)</div>
    </div>"""

    svg = make_svg(dates, rates, color)
    charts_html += f"""
    <div class="chart-box">
        <h2>EUR / {c} — Last 90 Days</h2>
        {svg}
    </div>"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ECB Dashboard</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,sans-serif; background:#0f172a; color:#f1f5f9; }}
header {{ background:#1e293b; padding:24px 40px; border-bottom:1px solid #334155; display:flex; justify-content:space-between; align-items:center; }}
header h1 {{ font-size:20px; font-weight:600; }}
header span {{ color:#94a3b8; font-size:13px; }}
.cards {{ display:flex; gap:16px; padding:32px 40px 0; flex-wrap:wrap; }}
.card {{ background:#1e293b; border:1px solid #334155; border-radius:12px; padding:20px 24px; flex:1; min-width:150px; }}
.card .label {{ font-size:12px; color:#94a3b8; margin-bottom:6px; }}
.card .value {{ font-size:22px; font-weight:600; }}
.card .change {{ font-size:13px; margin-top:4px; }}
.charts {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(440px,1fr)); gap:24px; padding:32px 40px; }}
.chart-box {{ background:#1e293b; border:1px solid #334155; border-radius:12px; padding:24px; }}
.chart-box h2 {{ font-size:14px; font-weight:500; color:#cbd5e1; margin-bottom:12px; }}
footer {{ text-align:center; padding:24px; color:#475569; font-size:12px; }}
</style>
</head>
<body>
<header>
    <h1>📈 ECB Exchange Rate Dashboard</h1>
    <span>Last updated: {today} &nbsp;|&nbsp; Source: European Central Bank</span>
</header>
<div class="cards">{cards_html}</div>
<div class="charts">{charts_html}</div>
<footer>Data sourced from the European Central Bank · eurofxref-hist-90d.xml</footer>
</body>
</html>"""

with open("dashboard.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Done → dashboard.html")