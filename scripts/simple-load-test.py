#!/usr/bin/env python3
"""
Generate graphs from load test CSV results.
Usage: python3 plot-results.py [path-to-csv]
If no path given, uses the most recent CSV in jmeter/results/
"""

import sys
import csv
from pathlib import Path

# Check for matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
except ImportError:
    print("matplotlib not installed. Run: pip install matplotlib")
    sys.exit(1)

PROJECT_DIR = Path(__file__).resolve().parent.parent

def load_csv(path):
    """Load CSV and return lists of (index, latency_ms)."""
    rows = []
    with open(path) as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                elapsed = float(row.get("elapsed", 0))
                if elapsed > 0:
                    rows.append((len(rows), elapsed))
            except (ValueError, KeyError):
                pass
    return rows

def plot_results(csv_path):
    rows = load_csv(csv_path)
    if not rows:
        print("No valid data in CSV")
        return

    indices = [r[0] for r in rows]
    latencies = [r[1] for r in rows]

    # Parse filename for title (e.g. spring-boot_cpu_normal_1774092524.csv)
    name = Path(csv_path).stem
    parts = name.split("_")
    framework = parts[0] if len(parts) >= 1 else "unknown"
    workload = parts[1] if len(parts) >= 2 else "unknown"
    phase = parts[2] if len(parts) >= 3 else "unknown"
    title = f"{framework} | {workload} | {phase}"

    out_dir = PROJECT_DIR / "analysis" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Main Dashboard: 2x2 Layout
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Latency over time (sampled for performance)
    sample = 5000 if len(indices) > 5000 else len(indices)
    step = max(1, len(indices) // sample)
    idx_samp = indices[::step]
    lat_samp = latencies[::step]

    axes[0, 0].scatter(idx_samp, lat_samp, s=1, alpha=0.5)
    axes[0, 0].set_xlabel("Request index")
    axes[0, 0].set_ylabel("Latency (ms)")
    axes[0, 0].set_title("Latency over time")
    axes[0, 0].grid(True, alpha=0.3)

    # Latency histogram
    axes[0, 1].hist(latencies, bins=50, edgecolor="black", alpha=0.7)
    axes[0, 1].set_xlabel("Latency (ms)")
    axes[0, 1].set_ylabel("Count")
    axes[0, 1].set_title("Latency distribution")
    axes[0, 1].grid(True, alpha=0.3)

    # Throughput calculation (rolling window)
    window_sec = 10
    total_sec = 300  # Default test duration
    time_per_req = total_sec / len(rows) if rows else 1
    window_size = int(window_sec / time_per_req) if time_per_req > 0 else 100
    
    throughput_x, throughput_y = [], []
    for i in range(0, len(rows) - window_size, max(1, window_size // 5)):
        chunk = latencies[i : i + window_size]
        t = (i + window_size / 2) * time_per_req
        rps = len(chunk) / window_sec
        throughput_x.append(t)
        throughput_y.append(rps)

    if throughput_x:
        axes[1, 0].plot(throughput_x, throughput_y, color="green")
        axes[1, 0].set_xlabel("Time (s)")
        axes[1, 0].set_ylabel("Throughput (req/s)")
        axes[1, 0].set_title("Throughput over time (10s window)")
        axes[1, 0].grid(True, alpha=0.3)

    # Summary stats text block
    lat_sorted = sorted(latencies)
    n = len(lat_sorted)
    p50, p95, p99 = lat_sorted[int(n*0.5)], lat_sorted[int(n*0.95)], lat_sorted[int(n*0.99)]
    
    summary = f"Total requests: {n}\nThroughput: {n/300:.1f} req/s\n\n"
    summary += f"p50: {p50:.0f} ms\np95: {p95:.0f} ms\np99: {p99:.0f} ms"
    
    axes[1, 1].text(0.1, 0.5, summary, fontsize=12, family="monospace", va="center")
    axes[1, 1].axis("off")
    axes[1, 1].set_title("Summary Statistics")

    fig.suptitle(title, fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(out_dir / f"{name}.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 2. Publication-Ready Histogram with Percentiles
    fig2, ax = plt.subplots(figsize=(10, 5))
    ax.hist(latencies, bins=80, edgecolor="black", alpha=0.7, color="steelblue")
    ax.axvline(p50, color="green", linestyle="--", label=f"p50: {p50:.0f} ms")
    ax.axvline(p95, color="orange", linestyle="--", label=f"p95: {p95:.0f} ms")
    ax.axvline(p99, color="red", linestyle="--", label=f"p99: {p99:.0f} ms")
    ax.set_title(f"{title} - Latency Distribution")
    ax.set_xlabel("Latency (ms)")
    ax.set_ylabel("Count")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.savefig(out_dir / f"{name}_histogram.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Graphs saved to {out_dir}")

def main():
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        results_dir = PROJECT_DIR / "jmeter" / "results"
        csvs = list(results_dir.glob("*.csv"))
        if not csvs:
            print("No CSV files found.")
            sys.exit(1)
        csv_path = max(csvs, key=lambda p: p.stat().st_mtime)

    plot_results(csv_path)

if __name__ == "__main__":
    main()