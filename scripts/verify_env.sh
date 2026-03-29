#!/usr/bin/env bash
set -euo pipefail

echo "Python:"
python --version
echo

echo "Conda env:"
echo "${CONDA_DEFAULT_ENV:-<none>}"
echo

echo "Import test:"
python -c "import tau_bench; print('tau_bench import ok')"
