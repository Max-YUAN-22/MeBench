#!/usr/bin/env python3
"""Appendix K step 3 — judge-agreement metrics + APPENDIX_K HTML.

Merges the Gemini re-judgments with the frozen original-judge axes (from the
packets manifests, which mirror runs/MASTER_task{2,3}.tsv) and computes, per task:

  - overall agreement and Cohen's kappa per axis (binary 0/1), with confusion rates;
  - chain-level agreement (all five axes) and pass-rate difference under the two judges;
  - per-system pass rates under both judges on the identical sample, rank orders,
    Kendall tau, and order changes;
  - self-preference check (agreement on Gemini's own rows vs other systems' rows);
  - leniency rates (fail->pass vs pass->fail flips).

This analysis quantifies sensitivity to the choice of automated judge. It CANNOT
establish which judge's calls are biologically correct; no gold standard for the
adjudication axes exists beyond the evaluator-only construction fields shown to both
judges. All frozen values remain untouched.
"""
import json, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
OUT.mkdir(exist_ok=True)
AXES = ["mechanism_correct", "mediator_correct", "causal_role_order_correct",
        "intervention_outcome_link_correct", "no_material_contradiction"]
SYSTEMS = ["GPT-6-Astra", "Claude-Sonnet-5.5", "Gemini-3.8-Flash",
           "GLM-5.3-Flash", "Grok-4.6", "Biomni"]
REJUDGE = "gemini-3.8-flash"

def b01(v):
    s = str(v).strip().lower()
    if s in ("1", "1.0", "true"): return 1
    if s in ("0", "0.0", "false"): return 0
    return None

def kappa(pairs):
    n = len(pairs)
    if n == 0: return None
    po = sum(a == b for a, b in pairs) / n
    p1 = sum(a for a, _ in pairs) / n
    p2 = sum(b for _, b in pairs) / n
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    return None if abs(1 - pe) < 1e-12 else (po - pe) / (1 - pe)

def tau_b(x, y):
    n = len(x); s = 0
    for i in range(n):
        for j in range(i + 1, n):
            a = (x[i] > x[j]) - (x[i] < x[j])
            b = (y[i] > y[j]) - (y[i] < y[j])
            s += a * b
    return s / (n * (n - 1) / 2)

def load(task):
    manifest = {}
    for r in json.load(open(HERE / "packets" / f"{task}_manifest.json")):
        manifest[r["key"]] = r
    new = {}
    for f in sorted((HERE / "judgments").glob(f"{task}_rejudge_batch*_judgments.tsv")):
        lines = f.read_text(encoding="utf-8").splitlines()[1:]
        for l in lines:
            parts = l.split("\t")
            if len(parts) >= 6: new[parts[0].strip()] = [b01(x) for x in parts[1:6]]
    rows = []
    for key, m in manifest.items():
        if key not in new: continue
        nx = new[key]
        sysname = key.split("@")[1]
        rows.append({"key": key, "unit_id": key.split("@")[0], "system": sysname,
                     "orig": m["orig_axes"], "orig_chain": m["orig_chain_pass"], "new": nx})
    return rows

def chain(v): return int(all(x == 1 for x in v))

def task_metrics(task):
    rows = load(task)
    n_parsed = len(rows)
    res = {"n_sampled": {"task2": 360, "task3": 480}[task], "n_parsed": n_parsed,
           "parse_coverage": round(100 * n_parsed / {"task2": 360, "task3": 480}[task], 1),
           "axes": {}, "chain": {}, "per_system": {}, "self_preference": {}, "leniency": {}}
    # per-axis agreement / kappa / confusion
    for i, ax in enumerate(AXES):
        pairs = [(r["orig"][ax], r["new"][i]) for r in rows if r["new"][i] is not None]
        o1n0 = sum(1 for a, b in pairs if a == 1 and b == 0)
        o0n1 = sum(1 for a, b in pairs if a == 0 and b == 1)
        res["axes"][ax] = {
            "n": len(pairs),
            "agreement": round(100 * sum(a == b for a, b in pairs) / len(pairs), 1) if pairs else None,
            "kappa": round(kappa(pairs), 3) if pairs else None,
            "orig1_new0": o1n0, "orig0_new1": o0n1,
            "orig_pos_rate": round(100 * sum(a for a, _ in pairs) / len(pairs), 1) if pairs else None,
            "new_pos_rate": round(100 * sum(b for _, b in pairs) / len(pairs), 1) if pairs else None,
        }
    # chain level
    valid = [r for r in rows if all(x is not None for x in r["new"])]
    oc = [r["orig_chain"] for r in valid]; nc = [chain(r["new"]) for r in valid]
    res["chain"] = {
        "n_valid": len(valid),
        "agreement": round(100 * sum(a == b for a, b in zip(oc, nc)) / len(valid), 1),
        "kappa": round(kappa(list(zip(oc, nc))), 3),
        "orig_pass_rate": round(100 * sum(oc) / len(valid), 1),
        "new_pass_rate": round(100 * sum(nc) / len(valid), 1),
        "delta": round(100 * (sum(nc) - sum(oc)) / len(valid), 1),
        "fail_to_pass": sum(1 for a, b in zip(oc, nc) if a == 0 and b == 1),
        "pass_to_fail": sum(1 for a, b in zip(oc, nc) if a == 1 and b == 0),
    }
    # per-system under both judges
    per = {}
    for s in SYSTEMS:
        v = [r for r in valid if r["system"] == s]
        if not v: continue
        per[s] = {"n": len(v),
                  "orig_pass": round(100 * sum(r["orig_chain"] for r in v) / len(v), 1),
                  "new_pass": round(100 * sum(chain(r["new"]) for r in v) / len(v), 1),
                  "fail_to_pass": sum(1 for r in v if r["orig_chain"] == 0 and chain(r["new"]) == 1),
                  "pass_to_fail": sum(1 for r in v if r["orig_chain"] == 1 and chain(r["new"]) == 0)}
    res["per_system"] = per
    order_o = sorted(per, key=lambda s: -per[s]["orig_pass"])
    order_n = sorted(per, key=lambda s: -per[s]["new_pass"])
    res["ranking"] = {"ranking_applicable": task == "task3",
                      "design_note": ("task2 sample is balanced by design (30 pass / 30 fail per system), so "
                                      "per-system chain-pass levels on the sample are pinned at ~50% and the "
                                      "sample cannot support a ranking claim; ranking stability is assessed on "
                                      "the task3 full enumeration and at the population level in Appendix M"
                                      if task == "task2" else ""),
                      "order_original_judge": order_o, "order_rejudge": order_n,
                      "kendall_tau": round(tau_b([SYSTEMS.index(s) for s in order_o],
                                                 [SYSTEMS.index(s) for s in order_n]), 3),
                      "identical_order": order_o == order_n,
                      "top_system_same": order_o[0] == order_n[0],
                      "bottom_system_same": order_o[-1] == order_n[-1]}
    # self-preference: rows whose *predicted answer* came from Gemini
    gem = [r for r in valid if r["system"] == "Gemini-3.8-Flash"]
    oth = [r for r in valid if r["system"] != "Gemini-3.8-Flash"]
    def agree(rs):
        if not rs: return None
        return round(100 * sum(sum(a == b for a, b in zip([r["orig"][ax] for ax in AXES],
                                                          [x for x in r["new"] if x is not None])) / 5
                               for r in rs if all(x is not None for x in r["new"])) / len(rs), 1)
    res["self_preference"] = {
        "gemini_rows": len(gem), "other_rows": len(oth),
        "gemini_f2p": sum(1 for r in gem if r["orig_chain"] == 0 and chain(r["new"]) == 1),
        "gemini_p2f": sum(1 for r in gem if r["orig_chain"] == 1 and chain(r["new"]) == 0),
        "other_f2p": sum(1 for r in oth if r["orig_chain"] == 0 and chain(r["new"]) == 1),
        "other_p2f": sum(1 for r in oth if r["orig_chain"] == 1 and chain(r["new"]) == 0),
        "gemini_fail_rows": sum(1 for r in gem if r["orig_chain"] == 0),
        "other_fail_rows": sum(1 for r in oth if r["orig_chain"] == 0),
        "axis_agreement_gemini_rows": agree(gem), "axis_agreement_other_rows": agree(oth),
        "pass_delta_gemini_rows": round(100 * (sum(chain(r["new"]) for r in gem) / len(gem)
                                               - sum(r["orig_chain"] for r in gem) / len(gem)), 1) if gem else None,
        "pass_delta_other_rows": round(100 * (sum(chain(r["new"]) for r in oth) / len(oth)
                                              - sum(r["orig_chain"] for r in oth) / len(oth)), 1),
    }
    return res

K = {"judge": REJUDGE, "task2": task_metrics("task2"), "task3": task_metrics("task3")}
json.dump(K, open(OUT / "K_METRICS.json", "w"), indent=1)
print(json.dumps(K, indent=1)[:4000])
print("WROTE", OUT / "K_METRICS.json")
