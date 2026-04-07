#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 sample.vcf.gz"
  exit 1
fi

SAMPLE_VCF="$1"
WORK_DIR="results/adhd"
mkdir -p "$WORK_DIR"

python3 ./prs_pipeline.py --pgs-id PGS003753 --vcf "$SAMPLE_VCF" --work-dir "$WORK_DIR"

echo "ADHD PRS completed. Results are in $WORK_DIR"
