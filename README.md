# PRS 1000G Workflow

This repository contains a complete workflow for:

- installing `plink2` and the required Python tools
- scoring a single sample for a single disease PRS (example: ADHD)
- downloading the 1000 Genomes reference dataset
- selecting an ethnic reference population (EUR or TSI)
- scoring the ethnic subset and plotting the PRS distribution

## Repository layout

- `install.sh` — install Python dependencies and download `plink2`
- `download_1000g.sh` — download the 1000G Phase 3 common dataset
- `subset_ethnicity.sh` — create EUR/TSI sample subsets from the 1000G data
- `prs_pipeline.py` — download PGS score files and run PRS scoring
- `plot_prs_distribution.py` — plot a reference distribution and overlay a sample score
- `run_adhd_prs.sh` — example script to compute ADHD PRS for a single sample
- `requirements.txt` — Python dependencies
- `.gitignore` — excludes binaries and generated data files

## Prerequisites

- Linux/macOS terminal
- `python3` installed
- `wget`, `unzip`, `awk`, `bash`
- enough disk space for the 1000G reference files

## 1. Install tools

Run:

```bash
cd prs-1000g-repo
bash install.sh
```

This installs the Python dependencies and downloads `plink2` into the repository root.

## 2. Run a single PRS for ADHD

Use the sample script with a VCF file:

```bash
cd prs-1000g-repo
bash run_adhd_prs.sh /path/to/sample.vcf.gz
```

The output will be written to `results/adhd/`.

## 3. Download 1000 Genomes reference data

Run:

```bash
cd prs-1000g-repo
bash download_1000g.sh
```

This downloads the 1000G PLINK dataset archive into `data/` and extracts it.

> If you already have the 1000G PLINK files in a different location, set `DATA_DIR` inside `download_1000g.sh` or copy them into `data/`.

## 4. Select an ethnic reference population

Create European (EUR) and Toscani (TSI) subsets:

```bash
cd prs-1000g-repo
bash subset_ethnicity.sh
```

This produces:

- `data/1000G_EUR_hg19.bed/.bim/.fam`
- `data/1000G_TSI_hg19.bed/.bim/.fam`

## 5. Score an ethnic subset and plot distribution

Example: score the European subset for ADHD and plot it against the 1000G distribution.

```bash
cd prs-1000g-repo
python3 prs_pipeline.py \
  --pgs-id PGS002746 \
  --bfile data/1000G_EUR_hg19 \
  --work-dir results/1000G_EUR_ADHD

python3 plot_prs_distribution.py \
  --reference-sscore results/1000G_EUR_ADHD/1000G_EUR_hg19.PGS002746.sscore \
  --sample-value 0.000361668 \
  --sample-label "My sample" \
  --output results/1000G_EUR_ADHD/ADHD_EUR_distribution.png
```

## 6. Notes

- `PGS002746` is the ADHD score used in this example.
- The pipeline uses harmonized PGS Catalog files in GRCh37 coordinate space.
- The distribution plot uses the `.sscore` values produced by PLINK.

## Customization

- To score a different trait, change `--pgs-id` to another PGS catalog ID.
- To score a different sample VCF, use `--vcf /path/to/sample.vcf.gz`.
- To create a different subset, edit `subset_ethnicity.sh` and adjust the population condition.
