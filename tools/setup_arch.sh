#!/usr/bin/env bash
set -euo pipefail
base="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Install system packages first; see README.
python -m venv "$base/.venv"
"$base/.venv/bin/pip" install -r "$base/src/third_party/esa2026/python-requirements.txt"
rustup toolchain install 1.99.0 --profile minimal
