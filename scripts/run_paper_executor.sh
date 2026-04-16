#!/bin/bash
set -e

PROJECT_ROOT="$HOME/Projects/Trading-app-"
LOG_DIR="$PROJECT_ROOT/logs"
PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"
export PYTHONPATH=.

EXEC_LOG="$LOG_DIR/paper_executor_$(date +%F).log"

"$PYTHON_BIN" execution/paper_executor.py >> "$EXEC_LOG" 2>&1


