#!/usr/bin/env python3
import argparse
import gzip
import os
import subprocess
import sys
import urllib.request

PGS_URL_TEMPLATE = (
    "https://ftp.ebi.ac.uk/pub/databases/spot/pgs/scores/{pgs_id}/ScoringFiles/"
    "Harmonized/{pgs_id}_hmPOS_GRCh37.txt.gz"
)


def download_pgs_file(pgs_id: str, target_dir: str) -> str:
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, f"{pgs_id}_hmPOS_GRCh37.txt.gz")

    if not os.path.exists(target_path):
        url = PGS_URL_TEMPLATE.format(pgs_id=pgs_id)
        print(f"Downloading PGS file {pgs_id} from {url}...")
        try:
            urllib.request.urlretrieve(url, target_path)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise RuntimeError(
                    f"PGS file not found at {url}. Check PGS ID or file availability."
                )
            raise
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
                for name in ["hm_chr", "hm_pos", "effect_allele", "other_allele", "effect_weight"]:
                    if name not in header:
                        raise RuntimeError(f"Missing required column '{name}' in PGS file")
                    columns[name] = header.index(name)
                continue

            chr_name = parts[columns["hm_chr"]].strip()
            chr_pos = parts[columns["hm_pos"]].strip()
            effect_allele = parts[columns["effect_allele"]].strip()
            other_allele = parts[columns["other_allele"]].strip()
            weight = parts[columns["effect_weight"]].strip()

            if not chr_name or not chr_pos.isdigit():
                continue
            if chr_name.startswith("chr"):
                chr_name = chr_name[3:]
            if chr_name not in {str(i) for i in range(1, 23)}:
                continue
            if len(effect_allele) != 1 or len(other_allele) != 1:
                continue
            try:
                float(weight)
            except ValueError:
                continue

            allele1, allele2 = sorted([effect_allele, other_allele])
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

    if vcf_path:
        cmd = [
            "./plink2",
            "--vcf", vcf_path,
            "--chr", "1-22",
            "--snps-only", "just-acgt",
            "--max-alleles", "2",
            "--set-all-var-ids", "@:#",
            "--var-id-multi", "@:#",
        ]
    else:
        expected_files = [f"{bfile_prefix}.bed", f"{bfile_prefix}.bim", f"{bfile_prefix}.fam"]
        missing = [f for f in expected_files if not os.path.exists(f)]
        if missing:
            raise FileNotFoundError(
                f"PLINK binary prefix files not found for '{bfile_prefix}': {', '.join(missing)}"
            )

        tmp_pfile_prefix = os.path.join(os.path.dirname(out_prefix), os.path.basename(bfile_prefix) + ".chrid")
        if not os.path.exists(f"{tmp_pfile_prefix}.pvar"):
            plink_cmd = [
                "./plink2",
                "--bfile", bfile_prefix,
                "--snps-only", "just-acgt",
                "--max-alleles", "2",
                "--set-all-var-ids", "@:#",
                "--var-id-multi", "@:#",
                "--make-pgen",
                "--out", tmp_pfile_prefix,
            ]
            result = subprocess.run(plink_cmd, capture_output=True, text=True)
            print(result.stdout)
            if result.returncode != 0:
                print(result.stderr, file=sys.stderr)
                raise RuntimeError("PLINK2 conversion to PGEN failed")
        cmd = ["./plink2", "--pfile", tmp_pfile_prefix]

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
    parser.add_argument("--pgs-id", required=True, help="PGS Catalog ID, e.g. PGS003835")
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

    if args.bfile:
        base_name = os.path.basename(args.bfile)
    else:
        base_name = os.path.splitext(os.path.basename(args.vcf))[0]
    out_prefix = os.path.join(args.work_dir, f"{base_name}.{args.pgs_id}")
    run_plink(score_path, out_prefix, vcf_path=args.vcf, bfile_prefix=args.bfile)
    print(f"PRS scoring complete. Output prefix: {out_prefix}")


if __name__ == "__main__":
    main()
