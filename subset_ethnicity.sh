#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="data"
PANEL_FILE="$DATA_DIR/integrated_call_samples_v3.20130502.ALL.panel"

mkdir -p "$DATA_DIR"
cd "$DATA_DIR"

if [ ! -f "$PANEL_FILE" ]; then
  echo "Downloading 1000G sample panel metadata..."
  wget -nc https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/integrated_call_samples_v3.20130502.ALL.panel
fi

awk '$3 == "EUR" {print "0", $1}' "$PANEL_FILE" > lista_europei.txt
awk '$2 == "TSI" {print "0", $1}' "$PANEL_FILE" > lista_toscani.txt

if [ ! -f 1000G_phase3_common_norel.bed ]; then
  echo "ERROR: 1000G PLINK files not found in $DATA_DIR"
  exit 1
fi

cd ..

if [ ! -x ./plink2 ]; then
  echo "ERROR: plink2 not found. Run ./install.sh first."
  exit 1
fi

./plink2 --bfile "$DATA_DIR/1000G_phase3_common_norel" --keep "$DATA_DIR/lista_europei.txt" --make-bed --out "$DATA_DIR/1000G_EUR_hg19"
./plink2 --bfile "$DATA_DIR/1000G_phase3_common_norel" --keep "$DATA_DIR/lista_toscani.txt" --make-bed --out "$DATA_DIR/1000G_TSI_hg19"

echo "Created European and TSI subsets in $DATA_DIR"
