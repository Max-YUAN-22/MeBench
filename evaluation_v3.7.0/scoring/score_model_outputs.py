#!/usr/bin/env python3
"""Score v3.7.0 entity-conditioned Task 3 intervention inference."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

BASE_PATH = Path(__file__).with_name("score_model_outputs_base_v3_6_1.py")
spec = importlib.util.spec_from_file_location("score_v3_6_1_base", BASE_PATH)
if spec is None or spec.loader is None: raise RuntimeError(f"Cannot load base scorer: {BASE_PATH}")
previous = importlib.util.module_from_spec(spec); spec.loader.exec_module(previous)
core = previous.base

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "evaluation/v3.7.0"


def score_task3(bundle: Path, predictions: list[dict], judgments: list[dict] | None) -> dict:
    hidden = core.read_tsv(bundle / "task3/hidden_labels.tsv.gz")
    pred_map = core.validate_ids(hidden, predictions, "prediction")
    intervention_ok, exact_ok, rescued = {}, {}, []
    for row in hidden:
        unit_id = row["unit_id"]
        predicted = pred_map[unit_id].get("predicted_intervention_type", "")
        raw = core.normalize(predicted); canonical = previous.canonical_intervention(predicted)
        accepted = json.loads(row["accepted_intervention_types_json"])
        exact_values = {core.normalize(x) for x in accepted}
        canonical_values = {previous.canonical_intervention(x) for x in accepted}
        exact_ok[unit_id] = raw in exact_values
        intervention_ok[unit_id] = canonical in canonical_values
        if intervention_ok[unit_id] and not exact_ok[unit_id]: rescued.append(unit_id)
    reasoning, exact_chain = core.reasoning_metrics(hidden, pred_map, judgments)
    result = {
        "task": "task3", "n_units": len(hidden), "n_pairs": len({x["pair_id"] for x in hidden}),
        "accepted_intervention_type_accuracy": core.safe_div(sum(intervention_ok.values()), len(hidden)),
        "exact_pre_normalization_intervention_type_accuracy": core.safe_div(sum(exact_ok.values()), len(hidden)),
        "synonym_rescued_units": len(rescued), "synonym_rescued_unit_ids": rescued,
        "perturbed_entity_is_input_and_not_predicted": True,
        "direction_is_input_and_not_scored": True,
        "matching_policy": "predicted intervention type matched to the accepted types for the supplied entity using the curated synonym whitelist",
        **reasoning,
    }
    if exact_chain is None:
        result["intervention_type_and_full_reasoning_chain_joint_accuracy"] = None
    else:
        result["intervention_type_and_full_reasoning_chain_joint_accuracy"] = core.safe_div(
            sum(intervention_ok[x] and exact_chain[x] for x in exact_chain), len(hidden)
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--task", choices=["task1", "task2", "task3"], required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--reasoning-judgments", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    predictions = core.read_tsv(args.predictions)
    judgments = core.read_tsv(args.reasoning_judgments) if args.reasoning_judgments else None
    scorer = {"task1": core.score_task1, "task2": core.score_task2, "task3": score_task3}[args.task]
    result = scorer(args.bundle, predictions, judgments)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
