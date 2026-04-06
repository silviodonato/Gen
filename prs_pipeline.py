#!/usr/bin/env python3
import argparse
import gzip
import os
import subprocess
import sys
import urllib.request

PGS_URL_TEMPLATE = (
    "https://ftp.ebi.ac.uk/pub/databases/spot/pgs/scores/{pgs_id}/ScoringFiles/"
    "{pgs_id}_hmPOS_GRCh37.txt.gz"
)


def download_pgs_file(pgs_id: str, target_dir: str) -> str:
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, f"{pgs_id}_hmPOS_GRCh37.txt.gz")
    if not os.path.exists(target_path):
        url = PGS_URL_TEMPLATE.format(pgs_id=pgs_id)
        print(f"Downloading PGS file {pgs_id} from {url}...")
        urllib.request.urlretrieve(url, target_path)
    return target_path


def build_score_file(pgs_path: str, score_path: str) -> int:
    header = None
    columns = {}
    kept = 0
    seen = set()

    with gzip.open(pgs_path, "rt") as inp, open(score_path, "w") as out:
        out.write("ID\tALLELE\tWEIGHT\n")
        for line in inp:
            if line.startswith("#"):
                continue
            if not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            if header is None:
                header = parts
                for name in ["chr_name", "chr_position", "effect_allele", "other_allele", "effect_weight"]:
                    if name not in header:
                        raise RuntimeError(f"Missing required column '{name}' in PGS file")
                    columns[name] = header.index(name)
                continue

            chr_name = parts[columns["chr_name"]].strip()
            chr_pos = parts[columns["chr_position"]].strip()
            effect_allele = parts[columns["effect_allele"]].strip()
            weight = parts[columns["effect_weight"]].strip()

            if not chr_name or not chr_pos.isdigit():
                continue
            if chr_name.startswith("chr"):
                chr_name = chr_name[3:]
            if chr_name not in {str(i) for i in range(1, 23)}:
                continue
            if len(effect_allele) != 1:
                continue
            try:
                float(weight)
            except ValueError:
                continue

            variant_id = f"{chr_name}:{chr_pos}"
            key = (variant_id, effect_allele, weight)
            if key in seen:
                continue
            seen.add(key)
            out.write(f"{variant_id}\t{effect_allele}\t{weight}\n")
            kept += 1

    return kept


def run_plink(score_path: str, out_prefix: str, vcf_path: str = None, bfile_prefix: str = None):
    if not os.path.exists("./plink2"):
        raise FileNotFoundError("plink2 binary not found in the repository root. Run install.sh first.")

    if vcf_path and bfile_prefix:
        raise ValueError("Specify only one of --vcf or --bfile")
    if not vcf_path and not bfile_prefix:
        raise ValueError("Specify either --vcf or --bfile")

    cmd = ["./plink2"]
    if vcf_path:
        cmd += ["--vcf", vcf_path, "--chr", "1-22", "--set-all-var-ids", "@:#"]
    else:
        cmd += ["--bfile", bfile_prefix]

    cmd += [
        "--score", score_path, "1", "2", "3", "header",
        "no-mean-imputation", "list-variants", "ignore-dup-ids",
        "--out", out_prefix,
    ]

    print("Running PLINK:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError("PLINK2 scoring failed")


def parse_args():
    parser = argparse.ArgumentParser(description="Compute PRS from a VCF or PLINK dataset using a PGS Catalog score file.")
    parser.add_argument("--pgs-id", required=True, help="PGS Catalog ID, e.g. PGS002746")
    parser.add_argument("--work-dir", default="results", help="Working directory for output")
    parser.add_argument("--vcf", help="Input VCF or VCF.gz file")
    parser.add_argument("--bfile", help="Input PLINK binary prefix")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.vcf is None and args.bfile is None:
        raise ValueError("Specify either --vcf or --bfile")
    if args.vcf and args.bfile:
        raise ValueError("Cannot specify both --vcf and --bfile")

    os.makedirs(args.work_dir, exist_ok=True)
    pgs_path = download_pgs_file(args.pgs_id, args.work_dir)
    score_path = os.path.join(args.work_dir, f"{args.pgs_id}.chrpos.score.tsv")
    print(f"Building score file: {score_path}")
    kept = build_score_file(pgs_path, score_path)
    print(f"Score file created with {kept} variants")

    base_name = args.bfile if args.bfile else os.path.splitext(os.path.basename(args.vcf))[0]
    out_prefix = os.path.join(args.work_dir, f"{base_name}.{args.pgs_id}")
    run_plink(score_path, out_prefix, vcf_path=args.vcf, bfile_prefix=args.bfile)
    print(f"PRS scoring complete. Output prefix: {out_prefix}")


if __name__ == "__main__":
    main()
