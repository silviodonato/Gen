#!/usr/bin/env bash
set -euo pipefail

echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

if [ ! -x "./plink2" ]; then
  echo "Downloading plink2..."
  wget -nc https://s3.amazonaws.com/plink2-assets/plink2_linux_x86_64_latest.zip
  unzip -o plink2_linux_x86_64_latest.zip
  chmod +x plink2
fi

echo "Installation complete. plink2 is available in $(pwd)."
