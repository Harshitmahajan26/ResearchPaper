#!/usr/bin/env python3
"""
Simple load test fallback when JMeter is not installed.
Uses only Python stdlib (no extra deps). Saves results to CSV.
Usage: python3 simple-load-test.py [spring-boot|fastapi] [cpu|io] [phase]
"""

import sys
import time
import csv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import urlopen, Request

# Project root
PROJECT_DIR = Path(__file__).resolve().parent.parent

def load_test(base_url, path, num_threads, duration_sec, ramp_up_sec):
    """Run load test and return latency samples."""
    results = []
    start = time.perf_counter()

    def worker(thread_id):
        latencies = []
        end_time = start + duration_sec
        # Ramp up: stagger thread starts
        time.sleep(ramp_up_sec * (thread_id / max(num_threads, 1)))
        while time.perf_counter() < end_time:
            try:
                t0 = time.perf_counter()
                with urlopen(Request(f"{base_url}{path}"), timeout=30) as r:
                    r.read()
                latencies.append((time.perf_counter() - t0) * 1000)
            except Exception as e:
                latencies.append(-1) # Error
            time.sleep(0.01) # Small pause to avoid 100% CPU
        return latencies

    with ThreadPoolExecutor(max_workers=num_threads) as ex:
        futures = [ex.submit(worker, i) for i in range(num_threads)]
        for f in as_completed(futures):
            results.extend(f.result())

    return [r for r in results if r >= 0]

def percentile(sorted_list, p):
    if not sorted_list:
        return 0
    k = (len(sorted_list) - 1) * p / 100
    f = int(k)
    return sorted_list[f] if f >= len(sorted_list) - 1 else sorted_list[f] + (k - f) * (sorted_list[f + 1] - sorted_list[f])

def main():
    framework = sys.argv[1] if len(sys.argv) > 1 else "spring-boot"
    workload = sys.argv[2] if len(sys.argv) > 2 else "cpu"
    phase = sys.argv[3] if len(sys.argv) > 3 else "normal"

    port = 8080 if framework == "spring-boot" else 8000
    base_url = f"http://localhost:{port}"
    path = "/api/cpu/work?durationMs=200" if workload == "cpu" else "/api/io/delay?delayMs=200"

    phases = {
        "warmup": (50, 60, 120),
        "normal": (100, 30, 300),
        "high": (500, 60, 300),
        "stress": (1000, 120, 600),
    }
    
    threads, ramp_up, duration = phases.get(phase, phases["normal"])

    print(f"Running: {framework} | {workload} | {phase} | {threads} users | {duration}s")
    print(f"Target: {base_url}{path}")

    results = load_test(base_url, path, threads, duration, ramp_up)

    if not results:
        print("No successful requests. Is the server running?")
        sys.exit(1)

    results.sort()
    total = len(results)
    elapsed = duration
    throughput = total / elapsed if elapsed else 0
    p50 = percentile(results, 50)
    p95 = percentile(results, 95)
    p99 = percentile(results, 99)

    print(f"\n--- Results ---")
    print(f"Total requests: {total}")
    print(f"Throughput: {throughput:.1f} req/s")
    print(f"Latency p50: {p50:.0f} ms")
    print(f"Latency p95: {p95:.0f} ms")
    print(f"Latency p99: {p99:.0f} ms")

    out_dir = PROJECT_DIR / "jmeter" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{framework}_{workload}_{phase}_{int(time.time())}.csv"
    
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timeStamp", "elapsed", "success"])
        for i, r in enumerate(results):
            w.writerow([i, r, "true"])
            
    print(f"\nSaved to: {out}")

if __name__ == "__main__":
    main()