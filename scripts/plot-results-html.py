#!/usr/bin/env python3
"""
Generate an HTML report with graphs from load test CSV.
No extra dependencies - just Python stdlib. Open the HTML in a browser.
Usage: python3 plot-results-html.py [path-to-csv]
"""

import sys
import csv
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

def load_csv(path):
    rows = []
    with open(path) as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                elapsed = float(row.get("elapsed", 0))
                if elapsed > 0:
                    rows.append(elapsed)
            except (ValueError, KeyError):
                pass
    return rows

def main():
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        results_dir = PROJECT_DIR / "jmeter" / "results"
        csvs = list(results_dir.glob("*.csv"))
        if not csvs:
            print("No CSV files in jmeter/results/")
            sys.exit(1)
        csv_path = max(csvs, key=lambda p: p.stat().st_mtime)

    latencies = load_csv(csv_path)
    if not latencies:
        print("No valid data")
        sys.exit(1)

    # Sample for chart (max 2000 points)
    step = max(1, len(latencies) // 2000)
    sampled = latencies[::step]

    lat_sorted = sorted(latencies)
    n = len(lat_sorted)
    p50 = lat_sorted[int(n * 0.5)] if n else 0
    p95 = lat_sorted[int(n * 0.95)] if n else 0
    p99 = lat_sorted[int(n * 0.99)] if n else 0
    throughput = n / 300 if n else 0

    name = csv_path.stem
    parts = name.split("_")
    title = f"{parts[0] if parts else '?'} | {parts[1] if len(parts)>1 else '?'} | {parts[2] if len(parts)>2 else '?'}"

    # Histogram bins
    min_lat, max_lat = min(latencies), max(latencies)
    bin_count = 50
    bin_width = max(1, (max_lat - min_lat) / bin_count)
    hist = [0] * bin_count
    for l in latencies:
        idx = min(int((l - min_lat) / bin_width), bin_count - 1)
        hist[idx] += 1

    labels_js = [f"{min_lat + i*bin_width:.0f}" for i in range(bin_count)]

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Load Test - {title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: system-ui, sans-serif; margin: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        .charts {{ display: flex; flex-wrap: wrap; gap: 20px; margin: 20px 0; }}
        .chart-box {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .chart-box h2 {{ margin: 0 0 10px 0; font-size: 1rem; }}
        .chart-box canvas {{ max-width: 500px; max-height: 300px; }}
        .summary {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .summary table {{ border-collapse: collapse; }}
        .summary td {{ padding: 8px 16px 8px 0; }}
        .summary td:first-child {{ font-weight: 600; color: #555; }}
    </style>
</head>
<body>
    <h1>Load Test Results: {title}</h1>
    <div class="summary">
        <table>
            <tr><td>Total requests</td><td>{n:,}</td></tr>
            <tr><td>Throughput</td><td>{throughput:.1f} req/s</td></tr>
            <tr><td>Latency p50</td><td>{p50:.0f} ms</td></tr>
            <tr><td>Latency p95</td><td>{p95:.0f} ms</td></tr>
            <tr><td>Latency p99</td><td>{p99:.0f} ms</td></tr>
        </table>
    </div>

    <div class="charts">
        <div class="chart-box">
            <h2>Latency distribution (histogram)</h2>
            <canvas id="histChart" width="400" height="250"></canvas>
        </div>
        <div class="chart-box">
            <h2>Latency over time (sampled)</h2>
            <canvas id="timeChart" width="400" height="250"></canvas>
        </div>
    </div>

    <script>
        const histData = {hist};
        const timeData = {sampled};
        const labels = {labels_js};

        new Chart(document.getElementById('histChart'), {{
            type: 'bar',
            data: {{
                labels: labels,
                datasets: [{{ label: 'Count', data: histData, backgroundColor: 'rgba(54, 162, 235, 0.6)' }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ title: {{ display: true, text: 'Latency (ms)' }} }},
                    y: {{ title: {{ display: true, text: 'Count' }} }}
                }}
            }}
        }});

        new Chart(document.getElementById('timeChart'), {{
            type: 'line',
            data: {{
                labels: timeData.map((_, i) => i),
                datasets: [{{ label: 'Latency (ms)', data: timeData, borderColor: 'rgb(75, 192, 192)', tension: 0.1, pointRadius: 0 }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ title: {{ display: true, text: 'Request index' }} }},
                    y: {{ title: {{ display: true, text: 'Latency (ms)' }} }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    out_dir = PROJECT_DIR / "analysis" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name}_report.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Generated: {out_path}")
    print("Open this file in your browser to view the graphs.")

if __name__ == "__main__":
    main()