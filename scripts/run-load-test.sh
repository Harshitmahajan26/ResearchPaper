#!/bin/bash
# Run JMeter load test for Spring Boot vs FastAPI study
# Usage:
# ./run-load-test.sh [spring-boot|fastapi] [cpu|io] [phase]
# phase: warmup | normal | high | stress
#
# Examples:
# ./run-load-test.sh spring-boot cpu normal
# ./run-load-test.sh fastapi io stress

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
JMETER_DIR="${JMETER_HOME:-$HOME/apache-jmeter-5.6.3}"

FRAMEWORK="${1:-spring-boot}"
WORKLOAD="${2:-cpu}"
PHASE="${3:-normal}"

# Ports: Spring Boot=8080, FastAPI=8000
if [ "$FRAMEWORK" = "spring-boot" ]; then
    PORT=8080
elif [ "$FRAMEWORK" = "fastapi" ]; then
    PORT=8000
else
    echo "Unknown framework: $FRAMEWORK (use spring-boot or fastapi)"
    exit 1
fi

# Load phases from experiment config
case "$PHASE" in
    warmup)  THREADS=50;  RAMP_UP=60;  DURATION=120 ;;
    normal)  THREADS=100; RAMP_UP=30;  DURATION=300 ;;
    high)    THREADS=500; RAMP_UP=60;  DURATION=300 ;;
    stress)  THREADS=1000; RAMP_UP=120; DURATION=600 ;;
    *)       echo "Unknown phase: $PHASE"; exit 1 ;;
esac

if [ "$WORKLOAD" = "cpu" ]; then
    JMX="$PROJECT_DIR/jmeter/test-plans/cpu-workload.jmx"
else
    JMX="$PROJECT_DIR/jmeter/test-plans/io-delay-workload.jmx"
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_DIR="${PROJECT_DIR}/jmeter/results"
RESULT_CSV="${RESULT_DIR}/${FRAMEWORK}_${WORKLOAD}_${PHASE}_${TIMESTAMP}.csv"

mkdir -p "$RESULT_DIR"

if [ ! -d "$JMETER_DIR" ]; then
    echo "JMeter not found at $JMETER_DIR."
    echo ""
    echo "Option 1 - Use Python fallback (no install needed):"
    echo "  python3 $PROJECT_DIR/scripts/simple-load-test.py $FRAMEWORK $WORKLOAD $PHASE"
    echo ""
    echo "Option 2 - Install JMeter:"
    echo "  Download from https://jmeter.apache.org/download_jmeter.cgi"
    echo "  Extract to ~/apache-jmeter-5.6.3 and set: export JMETER_HOME=\$HOME/apache-jmeter-5.6.3"
    exit 1
fi

echo "Running: $FRAMEWORK | $WORKLOAD | $PHASE | ${THREADS} users | ${DURATION}s"
echo "Results: $RESULT_CSV"

"$JMETER_DIR/bin/jmeter" -n \
    -t "$JMX" \
    -JTHREADS=$THREADS \
    -JRAMP_UP=$RAMP_UP \
    -JDURATION=$DURATION \
    -JTARGET_HOST=localhost \
    -JTARGET_PORT=$PORT \
    -JDELAY_MS=200 \
    -l "$RESULT_CSV" \
    -j "$RESULT_DIR/jmeter.log"

echo "Done. CSV saved to: $RESULT_CSV"