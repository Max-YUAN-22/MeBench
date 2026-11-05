# Locally corrected ranking metrics; author-supplied original remains in M_pair_bootstrap/.
#!/usr/bin/env python3
"""Appendix M — Pair-Level Statistical Robustness (Task 2).

Post-freeze sensitivity addendum. Read-only w.r.t. frozen files; outputs land in
sensitivity/M_pair_bootstrap/outputs/.

Computational design specified in the supplied appendix (preregistration timing not independently verified):
- Primary resampling unit = the TF-gene PAIR (168 pairs in Task 2), not the unit-run.
  All units and all 4 runs of a pair move together in every replicate.
- The 4 runs per system are technical repeats of one administration protocol
  (temperature 0 through relay serving is not bit-deterministic). They are treated as
  within-pair repeated measurements and are NEVER counted as independent biological
  replicates; there is no level in this analysis at which runs are resampled as if
  they were independent experiments.
- Estimator per system: unweighted mean over pairs of the per-pair pass rate
  (per-pair rate = mean over the pair's unit-runs). Published headline numbers are
  unit-run-pooled and are quoted alongside for continuity.
- B = 10,000 bootstrap replicates, seed 20261017, percentile CIs.
- GPT-vs-Claude differences are computed within each replicate on the SAME resampled
  pair set (paired by construction).
- Ranking stability: per replicate, rank the 6 systems; report the probability of the
  published ordering, P(GPT first), mean Kendall tau vs the published ordering
  (tau-b evaluated on aligned system score vectors; ties allowed), and adjacent-flip probabilities.
- Study-level bootstrap: pairs mapped to their primary source study (GSE accession,
  else DOI) from the evaluator-only provenance file; 31 source groups resampled with
  replacement. Reported separately WITH a concentration disclosure: one study
  (GSE266489, the ZNF143 collection) contributes 99/168 pairs, so study-level CIs
  are wide and the effective number of independent studies is small.
"""
import csv, gzip, json, random, re, sys
from collections import defaultdict
from pathlib import Path

import argparse
parser=argparse.ArgumentParser(description='Reproduce pair-equal chain/joint sensitivity with corrected rank comparisons and tie handling; no model calls.')
parser.add_argument('--root',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();ROOT=args.root
OUT = args.output;OUT.mkdir(parents=True,exist_ok=True)
B = 10_000
SEED = 20261017
SYSTEMS = ["GPT-6-Astra", "Claude-Sonnet-5.5", "Gemini-3.8-Flash",
           "GLM-5.3-Flash", "Grok-4.6", "Biomni"]
RNG = random.Random(SEED)

def one(v): return str(v).strip() in ("1", "1.0", "true", "True")

def rd(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t"); rows = []; last = None
    for l in lines[1:]:
        if not l.strip(): continue
        parts = l.split("\t")
        if parts[0].strip().startswith("T2U_"):
            vals = parts + [""] * (len(header) - len(parts))
            last = dict(zip(header, vals[:len(header)])); rows.append(last)
        elif last is not None:
            last[header[-1]] += " " + l.strip()
    return rows

rows = rd(ROOT / "runs/MASTER_task2.tsv")
assert len(rows) == 4632, len(rows)

# ---------- pair-level table ----------
# pair_rates[pair][system] = (chain_mean, joint_mean) over that pair's unit-runs
pair_rates = defaultdict(dict)
for r in rows:
    p = pair_rates[r["pair_id"]].setdefault(r["system"], [0, 0, 0])
    p[0] += one(r["chain_pass"]); p[1] += one(r["joint_pass"]); p[2] += 1
PAIRS = sorted(pair_rates)
assert len(PAIRS) == 168, len(PAIRS)
pr = {}
for p, v in pair_rates.items():
    pr[p] = {}
    for s in SYSTEMS:
        c, j, n = v[s]
        pr[p][s] = (c / n, j / n)

pooled_point = {}
for metric in (0, 1):
    for s in SYSTEMS:
        num = sum(pair_rates[p][s][metric] for p in PAIRS)
        den = sum(pair_rates[p][s][2] for p in PAIRS)
        pooled_point[(s, metric)] = 100 * num / den

def pair_mean(sample_pairs, metric_idx):
    out = {}
    for s in SYSTEMS:
        vals = [pr[p][s][metric_idx] for p in sample_pairs]
        out[s] = sum(vals) / len(vals)
    return out

# ---------- pair-level cluster bootstrap ----------
CH, JO = 0, 1
res = {m: {s: [] for s in SYSTEMS} for m in ("chain", "joint")}
diffs = {m: [] for m in ("chain", "joint")}
rank_counts = {"chain": defaultdict(int), "joint": defaultdict(int)}
gpt_first = {"chain": 0, "joint": 0}
tau_sum = {"chain": 0.0, "joint": 0.0}
pair_flip = {"chain": defaultdict(int), "joint": defaultdict(int)}
ORDER = {s: i for i, s in enumerate(SYSTEMS)}          # published order = system list order? NOT assumed:
# published ordering is determined from the data (descending pooled pair-weighted mean), computed below.

point = {m: pair_mean(PAIRS, CH if m == "chain" else JO) for m in ("chain", "joint")}
published_order = {m: sorted(SYSTEMS, key=lambda s: -point[m][s]) for m in ("chain", "joint")}

def kendall_tau_b(x, y):
    c=d=tx=ty=0
    for i in range(len(x)):
        for j in range(i):
            dx=0 if abs(x[i]-x[j])<1e-12 else (1 if x[i]>x[j] else -1)
            dy=0 if abs(y[i]-y[j])<1e-12 else (1 if y[i]>y[j] else -1)
            if dx and dy:
                if dx==dy:c+=1
                else:d+=1
            elif dx:ty+=1
            elif dy:tx+=1
    den=((c+d+tx)*(c+d+ty))**0.5
    return (c-d)/den if den else 0.0

for _ in range(B):
    samp = [PAIRS[RNG.randrange(len(PAIRS))] for _ in range(len(PAIRS))]
    for m, mi in (("chain", CH), ("joint", JO)):
        mu = pair_mean(samp, mi)
        for s in SYSTEMS:
            res[m][s].append(mu[s])
        diffs[m].append(mu["GPT-6-Astra"] - mu["Claude-Sonnet-5.5"])
        order = sorted(SYSTEMS, key=lambda s: -mu[s])
        if all(mu[x]>mu[y]+1e-12 for x,y in zip(published_order[m],published_order[m][1:])):
            rank_counts[m]["published"] += 1
        tops=[s for s in SYSTEMS if abs(mu[s]-max(mu.values()))<1e-12]
        if "GPT-6-Astra" in tops:gpt_first[m] += 1/len(tops)
        tau_sum[m] += kendall_tau_b([mu[s] for s in SYSTEMS], [point[m][s] for s in SYSTEMS])
        for a, b_ in zip(published_order[m], published_order[m][1:]):
            if mu[b_] > mu[a] + 1e-12:
                pair_flip[m][(a, b_)] += 1        # published-adjacent pair seen inverted

def ci(vals):
    vals = sorted(vals)
    lo = vals[int(0.025 * (B - 1))]; hi = vals[int(0.975 * (B - 1))]
    return 100 * lo, 100 * hi

summary = {
    "seed": SEED, "B": B, "n_pairs": len(PAIRS), "n_unit_runs": len(rows),
    "published_pooled_unitrun": {f"{s}|{'chain' if m == CH else 'joint'}": round(pooled_point[(s, m)], 1)
                                 for s in SYSTEMS for m in (CH, JO)},
    "pair_weighted_point": {m: {s: round(100 * point[m][s], 1) for s in SYSTEMS} for m in ("chain", "joint")},
    "bootstrap": {m: {s: {"point": round(100 * point[m][s], 1),
                          "ci95": [round(x, 1) for x in ci(res[m][s])],
                          "width": round(ci(res[m][s])[1] - ci(res[m][s])[0], 1)} for s in SYSTEMS}
                  for m in ("chain", "joint")},
    "gpt_minus_claude": {m: {"point": round(100 * (point[m]["GPT-6-Astra"] - point[m]["Claude-Sonnet-5.5"]), 1),
                             "ci95": [round(x, 1) for x in ci(diffs[m])],
                             "p_diff_gt_0": round(sum(1 for d in diffs[m] if d > 0) / B, 4)}
                         for m in ("chain", "joint")},
    "ranking": {m: {"pair_equal_reference_order": published_order[m],
                    "p_reproduce_published": round(rank_counts[m]["published"] / B, 4),
                    "p_gpt_first": round(gpt_first[m] / B, 4),
                    "mean_kendall_tau_b_vs_pair_equal_order": round(tau_sum[m] / B, 4)}
                for m in ("chain", "joint")},
}
summary["ranking"]["chain"]["adjacent_flip_prob"] = {
    f"flip {b_} above {a}": round(c / B, 4) for (a, b_), c in sorted(pair_flip["chain"].items())}
summary["ranking"]["joint"]["adjacent_flip_prob"] = {
    f"flip {b_} above {a}": round(c / B, 4) for (a, b_), c in sorted(pair_flip["joint"].items())}

# ---------- study-level ----------
meta = list(csv.DictReader(gzip.open(ROOT / "evaluation_v3.7.0/task2/evaluator_metadata.tsv.gz", "rt"), delimiter="\t"))
pair_study = {}
for r in meta:
    studies = []
    for src in json.loads(r["sources_json"]):
        acc = src.get("citation_or_accession", "")
        gse = re.findall(r"GSE\d+", acc)
        doi = re.findall(r"10\.\d{4,9}/\S+", acc)
        studies.append(gse[0] if gse else ("doi:" + doi[0] if doi else acc[:50]))
    pair_study.setdefault(r["pair_id"], set()).update(studies)
# primary study = lexicographically first identifier per pair (deterministic, disclosed)
pair2study = {p: sorted(v)[0] for p, v in pair_study.items()}
study_pairs = defaultdict(list)
for p in PAIRS:
    study_pairs[pair2study[p]].append(p)
STUDIES = sorted(study_pairs)
conc = sorted(((len(v), s) for s, v in study_pairs.items()), reverse=True)

study_res = {"chain": {s: [] for s in SYSTEMS}}
for _ in range(B):
    samp_studies = [STUDIES[RNG.randrange(len(STUDIES))] for _ in range(len(STUDIES))]
    samp_pairs = [p for st in samp_studies for p in study_pairs[st]]
    mu = pair_mean(samp_pairs, CH)
    for s in SYSTEMS:
        study_res["chain"][s].append(mu[s])

summary["study_level"] = {
    "n_studies": len(STUDIES),
    "pairs_per_study_top": [{"study": s, "pairs": n} for n, s in conc[:5]],
    "mapping_rule": "primary = lexicographically first identifier among the pair's sources (5 pairs have 2 sources)",
    "chain_bootstrap": {s: {"point": round(100 * point["chain"][s], 1),
                            "ci95": [round(x, 1) for x in ci(study_res["chain"][s])]}
                        for s in SYSTEMS},
}

json.dump(summary, open(OUT / "M_CORRECTED_RANKING.json", "w"), indent=1)

# ---------- console ----------
print(f"pairs={len(PAIRS)}  unit-runs={len(rows)}  B={B}  seed={SEED}")
print("\n== published (unit-run pooled) vs pair-weighted point ==")
for s in SYSTEMS:
    print(f"  {s:<22} chain {pooled_point[(s,CH)]:.1f} / {100*point['chain'][s]:.1f}   joint {pooled_point[(s,JO)]:.1f} / {100*point['joint'][s]:.1f}")
print("\n== pair-level bootstrap CIs ==")
for m in ("chain", "joint"):
    for s in SYSTEMS:
        b_ = summary["bootstrap"][m][s]
        print(f"  {m:<6} {s:<22} {b_['point']:>5}  [{b_['ci95'][0]:>5}, {b_['ci95'][1]:>5}]  width {b_['width']}")
print("\n== GPT - Claude =="); print(" ", summary["gpt_minus_claude"])
print("\n== ranking ==")
for m in ("chain",):
    r = summary["ranking"][m]
    print(f"  published order: {' > '.join(r['pair_equal_reference_order'])}")
    print(f"  P(full published order)={r['p_reproduce_published']}  P(GPT first)={r['p_gpt_first']}  mean tau={r['mean_kendall_tau_b_vs_pair_equal_order']}")
print("\n== study-level ==")
print(f"  studies={summary['study_level']['n_studies']}, top: {summary['study_level']['pairs_per_study_top'][:3]}")
for s in SYSTEMS:
    b_ = summary["study_level"]["chain_bootstrap"][s]
    print(f"  chain {s:<22} {b_['point']:>5}  [{b_['ci95'][0]:>5}, {b_['ci95'][1]:>5}]")
print("WROTE", OUT / "M_CORRECTED_RANKING.json")
