#!/usr/bin/env python3
"""Batch fold sequences from ProteinMPNN output using ESMFold."""

import argparse, os, glob, csv, torch, esm, re
from tqdm import tqdm

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--fasta_dir", required=True)
    p.add_argument("--output_dir", required=True)
    p.add_argument("--limit", type=int, default=0, help="max sequences to fold (0=all)")
    return p.parse_args()

def find_fasta_files(fasta_dir):
    return sorted(glob.glob(f"{fasta_dir}/**/*.fa", recursive=True))

def parse_mpnn_fasta(path):
    """Parse ProteinMPNN output: first seq is backbone (all G), second is designed."""
    seqs = []
    current_seq = ""
    current_header = ""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                if current_seq:
                    seqs.append((current_header, current_seq))
                current_header = line
                current_seq = ""
            else:
                current_seq += line
        if current_seq:
            seqs.append((current_header, current_seq))
    return seqs

def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    fasta_files = find_fasta_files(args.fasta_dir)
    if args.limit > 0:
        fasta_files = fasta_files[:args.limit]

    # collect all sequences
    entries = []
    for fa_path in fasta_files:
        rel = os.path.relpath(fa_path, args.fasta_dir)
        design_id = os.path.dirname(rel)
        seqs = parse_mpnn_fasta(fa_path)
        for si, (header, seq) in enumerate(seqs):
            # skip backbone (first seq in pair) — it's all G
            if si == 0:
                continue
            # extract score
            score_match = re.search(r"score=([\d.]+)", header)
            score = float(score_match.group(1)) if score_match else 0.0
            entries.append({
                "design_id": design_id,
                "seq_idx": si - 1,  # 0-indexed
                "header": header,
                "sequence": seq,
                "mpnn_score": score,
            })

    print(f"Found {len(fasta_files)} fasta files → {len(entries)} designed sequences")

    # load model once
    model = esm.pretrained.esmfold_v1()
    model = model.eval().cuda()

    csv_rows = []
    for entry in tqdm(entries, desc="Folding"):
        seq = entry["sequence"]
        # sanitize: replace / with _ in design_id
        clean_id = entry['design_id'].replace('/', '_')
        out_name = f"{clean_id}_seq{entry['seq_idx']}"
        pdb_path = os.path.join(args.output_dir, f"{out_name}.pdb")

        if os.path.exists(pdb_path):
            continue

        try:
            with torch.no_grad():
                output = model.infer_pdb(seq)
            os.makedirs(os.path.dirname(pdb_path) or '.', exist_ok=True)
            with open(pdb_path, "w") as f:
                f.write(output)
        except Exception as e:
            print(f"  FAIL {out_name}: {e}")
            continue

        csv_rows.append({
            "name": out_name,
            "design_id": entry["design_id"],
            "seq_idx": entry["seq_idx"],
            "length": len(seq),
            "sequence": seq,
            "mpnn_score": entry["mpnn_score"],
        })

    # write summary
    csv_path = os.path.join(args.output_dir, "folded.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=csv_rows[0].keys() if csv_rows else [])
        w.writeheader()
        w.writerows(csv_rows)

    print(f"\nDone. {len(csv_rows)} folded → {csv_path}")


if __name__ == "__main__":
    main()
