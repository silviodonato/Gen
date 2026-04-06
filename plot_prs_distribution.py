#!/usr/bin/env python3
import argparse
import matplotlib.pyplot as plt


def read_sscore(sscore_path):
    values = []
    with open(sscore_path) as fh:
        header = fh.readline().strip().split()
        if "SCORE1_AVG" not in header:
            raise ValueError("Could not find SCORE1_AVG in .sscore header")
        idx = header.index("SCORE1_AVG")
        for line in fh:
            if not line.strip():
                continue
            parts = line.split()
            values.append(float(parts[idx]))
    return values


def main():
    parser = argparse.ArgumentParser(description="Plot PRS distribution from a PLINK .sscore file.")
    parser.add_argument("--reference-sscore", required=True, help="Reference .sscore file from PLINK")
    parser.add_argument("--sample-value", type=float, required=True, help="Sample PRS value to overlay")
    parser.add_argument("--sample-label", default="Sample", help="Label for the sample line")
    parser.add_argument("--output", default="prs_distribution.png", help="Output PNG file")
    args = parser.parse_args()

    values = read_sscore(args.reference_sscore)
    values.sort()
    n = len(values)
    below = sum(1 for v in values if v < args.sample_value)
    equal = sum(1 for v in values if v == args.sample_value)
    percentile = (below + 0.5 * equal) / n * 100

    plt.figure(figsize=(10, 6))
    plt.hist(values, bins=80, density=True, color="#8da0cb", alpha=0.8, edgecolor="black")
    plt.axvline(
        args.sample_value,
        color="#e41a1c",
        linewidth=3,
        label=f"{args.sample_label}: {args.sample_value:.6g} ({percentile:.1f}th percentile)",
    )
    plt.title("PRS distribution")
    plt.xlabel("PRS score")
    plt.ylabel("Density")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(args.output, dpi=200)
    print(f"Saved plot to {args.output}")
    print(f"Sample PRS percentile: {percentile:.1f}% of reference samples are below or equal to this score.")


if __name__ == "__main__":
    main()
