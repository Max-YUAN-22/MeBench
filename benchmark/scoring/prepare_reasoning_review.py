#!/usr/bin/env python3
"""Prepare an evaluator-only semantic review packet for v3.5.1 reasoning."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "evaluation/v3.5.1"
AXES = [
    "mechanism_correct",
    "mediator_correct",
    "causal_role_order_correct",
    "intervention_outcome_link_correct",
    "no_material_contradiction",
]


def read_tsv(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_jsonl(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--task", choices=["task2", "task3"], required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    hidden = read_tsv(args.bundle / args.task / "hidden_labels.tsv.gz")
    inputs = {row["unit_id"]: row["model_input"] for row in read_jsonl(args.bundle / args.task / "inputs.jsonl.gz")}
    predictions = read_tsv(args.predictions)
    pred_map = {row["unit_id"]: row for row in predictions}
    hidden_ids = {row["unit_id"] for row in hidden}
    if len(pred_map) != len(predictions) or set(pred_map) != hidden_ids:
        raise SystemExit("Prediction IDs must match the complete hidden-label unit set exactly")

    rows = []
    for label in hidden:
        unit_id = label["unit_id"]
        truth = json.loads(label["reasoning_ground_truth_json"])
        pred = pred_map[unit_id]
        row = {
            "unit_id": unit_id,
            "model_input_json": json.dumps(inputs[unit_id], ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "model_prediction_json": json.dumps({k: v for k, v in pred.items() if k != "unit_id"}, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "mechanism_reasoning": pred.get("mechanism_reasoning", ""),
            "ground_truth_mechanism": truth["mechanism_class"],
            "ground_truth_mediator_type": truth["mediator_type"],
            "ground_truth_mediator_entity": truth["mediator_entity"],
            "ground_truth_causal_topology": truth["causal_topology"],
            "ground_truth_evidence_chain": truth["evidence_chain_statement"],
            "ground_truth_task_link_json": json.dumps(truth["task_specific_link"], ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        }
        row.update({axis: "" for axis in AXES})
        row["adjudicator_notes"] = ""
        rows.append(row)

    fields = list(rows[0])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)

    guide = args.output.with_suffix(args.output.suffix + ".GUIDE.md")
    guide.write_text(f"""# v3.5.1 {args.task} reasoning-chain adjudication guide

This packet is evaluator-only. Never provide it to the tested model.

For every row, fill each of the five fields with `1` or `0`:

1. `mechanism_correct`: the reasoning uses the ground-truth mechanism, not merely a compatible generic statement.
2. `mediator_correct`: it identifies the ground-truth key mediator. For direct-cis cases, an accurate target-linked cis-element type is sufficient; exact coordinates are not required. For chromatin, combinatorial-TF, and regulatory-RNA cases, the named mediator must match the hidden annotation or an unambiguous synonym.
3. `causal_role_order_correct`: the mediator is assigned the correct role and causal order/topology. Mere keyword co-occurrence fails.
4. `intervention_outcome_link_correct`: the explanation connects the supplied/inferred intervention to the target direction without reversing the effect logic.
5. `no_material_contradiction`: no statement contradicts the hidden chain, accepted perturbation, or direction.

Full-chain correctness requires all five fields to equal `1`. A bare mechanism name, a definition of a mechanism, or a restatement of the input must fail at least the mediator, causal-role/order, and intervention-outcome axes. Use `adjudicator_notes` for borderline cases.
""")
    print(json.dumps({"task": args.task, "rows": len(rows), "output": str(args.output), "guide": str(guide)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
