#!/usr/bin/env bash
# Idempotent dependency refresh for the ARIADNE Cloud Agent environment.
# Prepares the Python venv (CPU-only PyTorch, matching CI) and frontend deps.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# 1. System packages needed to create the venv and build native wheels
#    (filterpy, noise). No-op when already present (e.g. from the snapshot).
if command -v sudo >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    python3-venv python3-dev build-essential
fi

# 2. Python virtual environment. CPU-only torch keeps the install lean and
#    matches the wheels used in CI (.github/workflows/test.yml).
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --upgrade pip wheel
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 3. Frontend dependencies (npm ci = reproducible install from the lockfile).
( cd frontend && npm ci )

echo "ARIADNE install complete."
