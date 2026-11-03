#!/usr/bin/env python3
"""Score v3.6.1 with curated Task 3 intervention-type synonym normalization."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

BASE_PATH = Path(__file__).with_name("score_model_outputs_base_v3_6_0.py")
spec = importlib.util.spec_from_file_location("score_v3_6_0_base", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load base scorer: {BASE_PATH}")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "evaluation/v3.6.1"

ALIASES = {
    "agonistactivation": "agonist_activation",
    "agonisttreatment": "agonist_activation",
    "agonist": "agonist_activation",
    "activation": "agonist_activation",
    "sirnaknockdown": "knockdown",
    "shrnaknockdown": "knockdown",
    "knockdown": "knockdown",
    "rnainterference": "knockdown",
    "rnai": "knockdown",
    "overexpression": "overexpression",
    "forcedexpression": "overexpression",
    "ectopicexpression": "overexpression",
    "inhibition": "inhibition",
    "inhibitortreatment": "inhibition",
    "pharmacologicalinhibition": "inhibition",
    "spongeinhibition": "sponge_inhibition",
    "micrornasponge": "sponge_inhibition",
    "sponge": "sponge_inhibition",
    "geneticknockout": "genetic_knockout",
    "knockout": "genetic_knockout",
    "genedeletion": "genetic_knockout",
    "combinedligandstimulation": "combined_ligand_stimulation",
    "ligandstimulation": "combined_ligand_stimulation",
    "costimulation": "combined_ligand_stimulation",
    "combinedstimulation": "combined_ligand_stimulation",
}


def canonical_intervention(value: str) -> str:
    normalized = base.normalize(value)
    return ALIASES.get(normalized, normalized)


def score_task3(bundle: Path, predictions: list[dict], judgments: list[dict] | None) -> dict:
    hidden = base.read_tsv(bundle / "task3/hidden_labels.tsv.gz")
    pred_map = base.validate_ids(hidden, predictions, "prediction")
    perturb_ok, exact_ok, rescued = {}, {}, []
    for row in hidden:
        unit_id = row["unit_id"]
        pred = pred_map[unit_id]
        pred_entity = base.normalize(pred.get("predicted_perturbed_entity", ""))
        pred_type_raw = base.normalize(pred.get("predicted_intervention_type", ""))
        pred_type_canonical = canonical_intervention(pred.get("predicted_intervention_type", ""))
        accepted = json.loads(row["accepted_perturbations_json"])
        exact_signatures = {(base.normalize(x["perturbed_entity"]), base.normalize(x["intervention_type"])) for x in accepted}
        normalized_signatures = {(base.normalize(x["perturbed_entity"]), canonical_intervention(x["intervention_type"])) for x in accepted}
        exact_ok[unit_id] = (pred_entity, pred_type_raw) in exact_signatures
        perturb_ok[unit_id] = (pred_entity, pred_type_canonical) in normalized_signatures
        if perturb_ok[unit_id] and not exact_ok[unit_id]:
            rescued.append(unit_id)
    reasoning, exact_chain = base.reasoning_metrics(hidden, pred_map, judgments)
    result = {
        "task": "task3", "n_units": len(hidden), "n_pairs": len({row["pair_id"] for row in hidden}),
        "accepted_perturbation_accuracy": base.safe_div(sum(perturb_ok.values()), len(hidden)),
        "exact_pre_normalization_perturbation_accuracy": base.safe_div(sum(exact_ok.values()), len(hidden)),
        "synonym_rescued_units": len(rescued), "synonym_rescued_unit_ids": rescued,
        "perturbation_matching_policy": "entity exact after case/punctuation normalization; intervention type matched through curated synonym whitelist",
        "direction_is_input_and_not_scored": True, **reasoning,
    }
    if exact_chain is not None:
        joint = base.safe_div(
            sum(perturb_ok[x] and exact_chain[x] for x in exact_chain), len(hidden)
        )
        result["synonym_normalized_perturbation_and_full_reasoning_chain_joint_accuracy"] = joint
        result["perturbation_and_full_reasoning_chain_joint_accuracy"] = joint
    else:
        result["synonym_normalized_perturbation_and_full_reasoning_chain_joint_accuracy"] = None
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
    predictions = base.read_tsv(args.predictions)
    judgments = base.read_tsv(args.reasoning_judgments) if args.reasoning_judgments else None
    scorer = {"task1": base.score_task1, "task2": base.score_task2, "task3": score_task3}[args.task]
    result = scorer(args.bundle, predictions, judgments)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
