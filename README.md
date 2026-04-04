# Spring_Boot_vs_FastAPI_Benchmark_T23_2210994778_2210994857

## Project Title
**Spring Boot vs FastAPI: Resource Efficiency Benchmark Study**

## Software/Platforms Used
| Component | Version | Purpose |
|-----------|---------|---------|
| Docker | Latest | Containerization |
| Docker Compose | Latest | Orchestration |
| Python | 3.11 | FastAPI app, scripts |
| Java | 17 | Spring Boot app |
| Spring Boot | 3.2 | Java benchmark service |
| FastAPI | 0.109 | Python benchmark service |
| Prometheus | 2.45 | Metrics collection |
| Grafana | 10.2 | Dashboards |
| VS Code / PyCharm / IntelliJ | Any | Development |

## Programming Languages Used
- Python 3.11 (FastAPI)
- Java 17 (Spring Boot)
- Bash (scripts)
- YAML (configs)

## Steps to Run the Code

### 1. Prerequisites
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git clone this repo

### 2. Start Benchmark Service (Spring Boot or FastAPI)
```bash
# Spring Boot (port 8080)
docker compose --profile spring-boot up -d

# OR FastAPI (port 8000)
docker compose --profile fastapi up -d
```
*Prometheus (9090) + Grafana (3000, admin/admin) auto-start.*

**Verify:**
- App: `curl http://localhost:8080/health` (Spring) or `:8000/health` (FastAPI)
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

### 3. Run Load Tests (Python-based)
```bash
cd scripts
# Main script (Python load testing)
python simple-load-test.py spring-boot cpu normal   # Framework Workload Phase
# Examples: fastapi io stress, warmup, high

# Wrapper (auto Python)
chmod +x run-load-test.sh
./run-load-test.sh spring-boot cpu normal
```
*Results → `results/` folder*

### 4. Export & Plot Results
```bash
# Export Prometheus memory data
python scripts/export-prometheus-memory.py

# Plot graphs
python scripts/plot-results.py
# HTML report: plot-results-html.py
```

### 5. View Results
- Grafana dashboards at http://localhost:3000
- `results/` folder for CSVs/exports/plots

## Required Libraries/Tools
**Apps (auto via Docker):**
- FastAPI: `fastapi==0.109.2 uvicorn==0.27.1 prometheus-client==0.19.0`
- Spring Boot: Micrometer Prometheus, Spring Web/Actuator

**Scripts (host):**
```bash
pip install pandas matplotlib seaborn jinja2 requests prometheus-client numpy
# Java for Spring: OpenJDK 17
```

**No database/API keys needed.** Synthetic CPU/IO workloads.

**Username/Password:**
- Grafana: admin / admin

## Database / Dataset
- **None required.** Uses synthetic workloads:
  - CPU: Prime number computation (~200ms/request)
  - IO: Async delays (50-500ms)
- Config: `config/experiment-config.yml` (phases: warmup/normal/high/stress)
- Sample results: `results/run-logs/run-log-template.csv`

## Run File / Execution Support
- **Primary:** `scripts/simple-load-test.py` (Python load testing)
- **Wrapper:** `scripts/run-load-test.sh`
- **Services:** `docker-compose.yml`
- **Analysis:** `scripts/plot-results.py`, `scripts/plot-results-html.py`

## Input and Expected Output

**Input:** Load test phase/users (e.g., 100 users, CPU workload)
**Expected Output:**
- App responds with `{"primesFound": X, "durationMs": 200, "framework": "fastapi"}`
- Metrics in Prometheus/Grafana (latency, errors, CPU/memory)
- CSV results: Throughput, latency percentiles, error rates
- Plots: Memory usage graphs, performance comparison

**Folder Structure for Submission:**
```
Spring_Boot_vs_FastAPI_Benchmark_T23_2210994778_2210994857/
├── Source_Code/          # (copy all project files)
├── README.md            # This file
├── Requirements/        # (Copy this section to txt)
├── Database/            # (experiment-config.yml + sample CSV)
```

**Project is fully runnable on standard Windows/Linux/Mac with Docker.**
