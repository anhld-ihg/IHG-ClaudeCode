#!/usr/bin/env bash
# IHG Test Runner (Linux/macOS) — chay 25 test case, luu log + exit code
# Su dung: ./run-tests.sh
# Log: state/test-results-YYYYMMDD-HHMMSS.log
# Exit: 0=PASS, 1=FAIL, 2=runtime error

set -e
cd "$(dirname "$0")"

# Tao thu muc tam
IHG_ROOT_TMP=$(mktemp -d -t ihg-test-XXXXX)
export IHG_ROOT="$IHG_ROOT_TMP"
export IHG_STATE_DIR="$IHG_ROOT_TMP/state"
export IHG_OUTPUT_DIR="$IHG_ROOT_TMP/output"
export IHG_LOG_DIR="$IHG_ROOT_TMP/logs"

TS=$(date +%Y%m%d-%H%M%S)
LOG_FILE="state/test-results-${TS}.log"
SUMMARY="state/test-summary-${TS}.json"
export IHG_TEST_SUMMARY="$SUMMARY"

mkdir -p state

echo "===============================================================" | tee "$LOG_FILE"
echo "IHG AI OS Test Runner" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "Working dir: $(pwd)" | tee -a "$LOG_FILE"
echo "Tmp root: $IHG_ROOT_TMP" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "===============================================================" >> "$LOG_FILE"

# Kiem tra python
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 khong co trong PATH" | tee -a "$LOG_FILE"
    exit 2
fi

PYVER=$(python3 --version 2>&1)
echo "Python: $PYVER" | tee -a "$LOG_FILE"

# Chay test
echo "[RUNNING] python3 tests/runtests.py ..."
python3 tests/runtests.py >> "$LOG_FILE" 2>&1
RC=$?

echo "[RESULT] Exit code: $RC" | tee -a "$LOG_FILE"
if [ $RC -eq 0 ]; then
    echo "[OK] All tests PASS" | tee -a "$LOG_FILE"
else
    echo "[FAIL] Co test FAIL. Xem log: $LOG_FILE" | tee -a "$LOG_FILE"
fi
echo "Finished: $(date)" >> "$LOG_FILE"
exit $RC
