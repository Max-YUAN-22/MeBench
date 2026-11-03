#!/usr/bin/env python3
"""Score v3.5.1 outcomes plus adjudicated natural-language reasoning chains."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "evaluation/v3.5.1"
MECHANISMS = [
    "direct_cis_regulatory_dna",
    "chromatin_mediated_regulation",
    "combinatorial_tf_regulation",
    "regulatory_rna_mediated_indirect_regulation",
]
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


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def classification(y_true: list[str], y_pred: list[str]) -> dict:
    classes = sorted(set(y_true))
    invalid = sorted(set(y_pred) - set(classes))
    per_class, recalls, f1s = {}, [], []
    for cls in classes:
        tp = sum(a == cls and b == cls for a, b in zip(y_true, y_pred))
        fp = sum(a != cls and b == cls for a, b in zip(y_true, y_pred))
        fn = sum(a == cls and b != cls for a, b in zip(y_true, y_pred))
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2 * precision * recall, precision + recall)
        per_class[cls] = {"support": sum(x == cls for x in y_true), "precision": precision, "recall": recall, "f1": f1}
        recalls.append(recall); f1s.append(f1)
    result = {
        "accuracy": safe_div(sum(a == b for a, b in zip(y_true, y_pred)), len(y_true)),
        "balanced_accuracy": safe_div(sum(recalls), len(recalls)),
        "macro_f1": safe_div(sum(f1s), len(f1s)),
        "invalid_outputs": invalid,
        "per_class": per_class,
    }
    if set(classes) == {"down", "up"} and not invalid:
        tp = sum(a == "up" and b == "up" for a, b in zip(y_true, y_pred))
        tn = sum(a == "down" and b == "down" for a, b in zip(y_true, y_pred))
        fp = sum(a == "down" and b == "up" for a, b in zip(y_true, y_pred))
        fn = sum(a == "up" and b == "down" for a, b in zip(y_true, y_pred))
        denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
        result["mcc"] = (tp * tn - fp * fn) / denominator if denominator else 0.0
    return result


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def validate_ids(hidden: list[dict], rows: list[dict], name: str) -> dict[str, dict]:
    row_map = {row["unit_id"]: row for row in rows}
    hidden_ids = {row["unit_id"] for row in hidden}
    if len(row_map) != len(rows):
        raise SystemExit(f"Duplicate {name} unit_id")
    if set(row_map) != hidden_ids:
        raise SystemExit(f"{name} IDs mismatch: missing={len(hidden_ids-set(row_map))}, extra={len(set(row_map)-hidden_ids)}")
    return row_map


def mechanism_mentions(reasoning: str) -> set[str]:
    text = reasoning.lower()
    return {label for label in MECHANISMS if re.search(rf"(?<![a-z0-9_]){re.escape(label)}(?![a-z0-9_])", text)}


def parse_bool(value: str, field: str, unit_id: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "pass"}:
        return True
    if normalized in {"0", "false", "no", "fail"}:
        return False
    raise SystemExit(f"Invalid {field} for {unit_id}: expected 0/1, true/false, yes/no, or pass/fail")


def reasoning_metrics(hidden: list[dict], pred_map: dict[str, dict], judgments: list[dict] | None) -> tuple[dict, dict[str, bool] | None]:
    present = [bool(pred_map[row["unit_id"]].get("mechanism_reasoning", "").strip()) for row in hidden]
    mentioned = [
        row["mechanism"] in mechanism_mentions(pred_map[row["unit_id"]].get("mechanism_reasoning", ""))
        for row in hidden
    ]
    base = {
        "reasoning_present_rate": safe_div(sum(present), len(hidden)),
        "exact_mechanism_label_mention_rate_diagnostic_only": safe_div(sum(mentioned), len(hidden)),
        "label_mention_is_not_chain_credit": True,
    }
    if judgments is None:
        base.update({
            "reasoning_chain_status": "not_scored: provide --reasoning-judgments after blinded semantic adjudication",
            "full_reasoning_chain_accuracy": None,
            "mean_reasoning_chain_component_score": None,
        })
        return base, None
    judgment_map = validate_ids(hidden, judgments, "reasoning judgment")
    exact, component_scores, per_axis = [], [], {axis: [] for axis in AXES}
    invalid_label_only = []
    for row in hidden:
        unit_id = row["unit_id"]
        values = {axis: parse_bool(judgment_map[unit_id].get(axis, ""), axis, unit_id) for axis in AXES}
        for axis, value in values.items():
            per_axis[axis].append(value)
        chain_ok = all(values.values())
        exact.append(chain_ok)
        component_scores.append(sum(values.values()) / len(AXES))
        reasoning = pred_map[unit_id].get("mechanism_reasoning", "").strip()
        if len(mechanism_mentions(reasoning)) == 1 and len(reasoning.split()) <= 3 and chain_ok:
            invalid_label_only.append(unit_id)
    if invalid_label_only:
        raise SystemExit("Label-only reasoning cannot receive a full-chain pass: " + ",".join(invalid_label_only[:10]))
    base.update({
        "reasoning_chain_status": "scored_by_supplied_blinded_adjudication",
        "full_reasoning_chain_accuracy": safe_div(sum(exact), len(exact)),
        "mean_reasoning_chain_component_score": safe_div(sum(component_scores), len(component_scores)),
        "per_axis_accuracy": {axis: safe_div(sum(values), len(values)) for axis, values in per_axis.items()},
        "full_chain_correct_units": sum(exact),
        "full_chain_incorrect_units": len(exact) - sum(exact),
    })
    return base, {row["unit_id"]: ok for row, ok in zip(hidden, exact)}


def score_task1(bundle: Path, predictions: list[dict], judgments: list[dict] | None) -> dict:
    if judgments is not None:
        raise SystemExit("Task 1 does not use reasoning judgments")
    hidden = read_tsv(bundle / "task1/hidden_labels.tsv.gz")
    pred_map = validate_ids(hidden, predictions, "prediction")
    y_true = [row["mechanism"] for row in hidden]
    y_pred = [pred_map[row["unit_id"]]["predicted_mechanism"].strip() for row in hidden]
    return {"task": "task1", "n_units": len(hidden), **classification(y_true, y_pred)}


def score_task2(bundle: Path, predictions: list[dict], judgments: list[dict] | None) -> dict:
    hidden = read_tsv(bundle / "task2/hidden_labels.tsv.gz")
    pred_map = validate_ids(hidden, predictions, "prediction")
    y_true = [row["direction"] for row in hidden]
    y_pred = [pred_map[row["unit_id"]]["predicted_direction"].strip().lower() for row in hidden]
    outcome = classification(y_true, y_pred)
    reasoning, exact_map = reasoning_metrics(hidden, pred_map, judgments)
    result = {"task": "task2", "n_units": len(hidden), "direction_metrics": outcome, **reasoning}
    if exact_map is not None:
        direction_ok = {row["unit_id"]: pred_map[row["unit_id"]]["predicted_direction"].strip().lower() == row["direction"] for row in hidden}
        result["direction_and_full_reasoning_chain_joint_accuracy"] = safe_div(
            sum(direction_ok[x] and exact_map[x] for x in exact_map), len(hidden)
        )
    else:
        result["direction_and_full_reasoning_chain_joint_accuracy"] = None
    return result


def score_task3(bundle: Path, predictions: list[dict], judgments: list[dict] | None) -> dict:
    hidden = read_tsv(bundle / "task3/hidden_labels.tsv.gz")
    pred_map = validate_ids(hidden, predictions, "prediction")
    perturb_ok = {}
    for row in hidden:
        pred = pred_map[row["unit_id"]]
        predicted = (normalize(pred.get("predicted_perturbed_entity", "")), normalize(pred.get("predicted_intervention_type", "")))
        accepted = {
            (normalize(x["perturbed_entity"]), normalize(x["intervention_type"]))
            for x in json.loads(row["accepted_perturbations_json"])
        }
        perturb_ok[row["unit_id"]] = predicted in accepted
    reasoning, exact_map = reasoning_metrics(hidden, pred_map, judgments)
    result = {
        "task": "task3", "n_units": len(hidden), "n_pairs": len({row["pair_id"] for row in hidden}),
        "accepted_perturbation_accuracy": safe_div(sum(perturb_ok.values()), len(hidden)),
        "direction_is_input_and_not_scored": True, **reasoning,
    }
    if exact_map is not None:
        result["perturbation_and_full_reasoning_chain_joint_accuracy"] = safe_div(
            sum(perturb_ok[x] and exact_map[x] for x in exact_map), len(hidden)
        )
    else:
        result["perturbation_and_full_reasoning_chain_joint_accuracy"] = None
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--task", choices=["task1", "task2", "task3"], required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--reasoning-judgments", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    predictions = read_tsv(args.predictions)
    judgments = read_tsv(args.reasoning_judgments) if args.reasoning_judgments else None
    result = {"task1": score_task1, "task2": score_task2, "task3": score_task3}[args.task](args.bundle, predictions, judgments)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
