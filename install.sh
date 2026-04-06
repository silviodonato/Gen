#!/usr/bin/env bash
set -euo pipefail

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating Python virtual environment in $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Upgrading pip and installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -x "./plink2" ]; then
  echo "Downloading plink2..."
  wget -nc https://s3.amazonaws.com/plink2-assets/plink2_linux_x86_64_latest.zip
  unzip -o plink2_linux_x86_64_latest.zip
  chmod +x plink2
fi

echo "Installation complete. Use 'source $VENV_DIR/bin/activate' to activate the environment."