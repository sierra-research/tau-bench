#!/usr/bin/env bash

# Simple runner to execute all test_*.py files in the tests/ directory one by one.

set -u

# Activate Conda environment (mirrors existing usage in run_batch_original.sh)
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  # shellcheck source=/dev/null
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
  conda activate taubench-py312
else
  echo "Warning: Conda initialization script not found; running tests without activating taubench-py312."
fi

cd "$(dirname "$0")" || exit 1

echo "Running tests one by one..."

for test_file in tests/test_*.py; do
  if [ ! -f "$test_file" ]; then
    echo "No test files matching tests/test_*.py found."
    exit 1
  fi

  echo "========================================"
  echo "Running: $test_file"
  echo "========================================"

  pytest "$test_file" -v
  status=$?

  if [ $status -ne 0 ]; then
    echo "Tests failed in $test_file (exit code $status). Stopping."
    exit $status
  fi
done

echo "All tests completed successfully."

