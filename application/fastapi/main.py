"""
FastAPI benchmark service - CPU and I/O workloads
for Spring Boot vs FastAPI study.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

app = FastAPI(title="Benchmark Service", version="1.0.0")

_executor = ThreadPoolExecutor(max_workers=50)

# -------------------------
# Prometheus Metrics
# -------------------------
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency in seconds",
    ["endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0),
)

# -------------------------
# CPU-bound helpers
# -------------------------
def is_prime(n: int) -> bool:
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False

    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def cpu_work_sync(duration_ms: int) -> tuple:
    """Synchronous CPU work (runs in thread pool for concurrency)."""
    start = time.perf_counter()
    count = 0
    n = 0
    target_sec = duration_ms / 1000.0

    while time.perf_counter() - start < target_sec:
        if is_prime(n):
            count += 1
        n += 1

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return count, elapsed_ms


# -------------------------
# API Endpoints
# -------------------------
@app.get("/api/cpu/work")
async def cpu_work(duration_ms: int = 200):
    """
    CPU-bound workload.
    Computes primes for `duration_ms`.
    Runs in thread pool (matches Spring Boot concurrency).
    """
    loop = asyncio.get_running_loop()
    count, elapsed_ms = await loop.run_in_executor(
        _executor, cpu_work_sync, duration_ms
    )

    return {
        "primesFound": count,
        "durationMs": elapsed_ms,
        "framework": "fastapi",
    }


@app.get("/api/io/delay")
async def io_delay(delay_ms: int = 200):
    """
    I/O-bound workload.
    Uses asyncio.sleep (non-blocking).
    """
    delay_sec = min(delay_ms, 5000) / 1000.0  # cap at 5s for safety
    start = time.perf_counter()
    await asyncio.sleep(delay_sec)
    actual_ms = int((time.perf_counter() - start) * 1000)

    return {
        "delayMs": delay_ms,
        "actualMs": actual_ms,
        "framework": "fastapi",
    }


@app.get("/health")
async def health():
    return {"status": "UP", "framework": "fastapi"}


@app.get("/metrics")
async def metrics():
    """Prometheus scrape endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )