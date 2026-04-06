#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="data"
mkdir -p "$DATA_DIR"
cd "$DATA_DIR"

if [ ! -f 1000G_phase3_common_norel.zip ]; then
  echo "Downloading 1000G Phase 3 common dataset..."
  wget -nc https://ndownloader.figshare.com/files/17838962 -O 1000G_phase3_common_norel.zip
fi

if [ ! -f 1000G_phase3_common_norel.bed ] || [ ! -f 1000G_phase3_common_norel.bim ] || [ ! -f 1000G_phase3_common_norel.fam ]; then
  echo "Extracting 1000G files..."
  unzip -o 1000G_phase3_common_norel.zip
fi

echo "1000G data is available in $(pwd)"
