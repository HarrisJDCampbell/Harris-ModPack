#!/usr/bin/env bash
# Harris ModPack: one-command install for macOS.
#
#   ./install.sh            install or update, then open Prism Launcher
#   ./install.sh --no-open  same, but don't open Prism
#
# Installs (via Homebrew, if missing): Python 3.11+, Java 21, Prism Launcher.
# Then builds the Prism instance "Harris ModPack" with every mod downloaded and
# hash-checked. Re-run it any time to update; it only downloads what changed.
set -euo pipefail
cd "$(dirname "$0")"

bold() { printf '\033[1m%s\033[0m\n' "$*"; }

if [[ "$(uname)" != "Darwin" ]]; then
  echo "This script is for macOS. On other systems: python3 scripts/modpack.py install"
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required: https://brew.sh"
  exit 1
fi

need_formula() { brew list --formula "$1" >/dev/null 2>&1 || { bold "Installing $1"; brew install "$1"; }; }
need_cask()    { brew list --cask "$1" >/dev/null 2>&1 || [[ -d "/Applications/$2" ]] || { bold "Installing $2"; brew install --cask "$1"; }; }

# Any Python 3.11+ works (the tool uses tomllib); install one only if needed.
PY=""
for cand in python3 python3.14 python3.13 python3.12 python3.11; do
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
    PY="$(command -v "$cand")"; break
  fi
done
if [[ -z "$PY" ]]; then
  need_formula python@3.13
  PY="$(brew --prefix python@3.13)/bin/python3.13"
fi
need_formula openjdk@21
need_cask prismlauncher "Prism Launcher.app"

"$PY" scripts/modpack.py install

if [[ "${1:-}" != "--no-open" ]]; then
  open -a "Prism Launcher"
  cat <<'MSG'

Prism Launcher is opening.
  First time only: finish the setup wizard, then add your Microsoft account
  (top right: Accounts > Manage Accounts > Add Microsoft).
  Then select "Harris ModPack" and hit Launch.
MSG
fi
