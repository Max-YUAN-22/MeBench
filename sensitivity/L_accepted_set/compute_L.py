#!/usr/bin/env python3
"""Appendix L — Identifiability and Accepted-Set Analysis for Task 3.

Post-freeze sensitivity/identifiability analysis. Read-only w.r.t. the frozen
release: consumes task3/hidden_labels.tsv.gz (raw accepted sets) and
runs/MASTER_task3.tsv (as-submitted predictions, published canonical scoring).
No frozen file is modified; all outputs land under sensitivity/L_accepted_set/outputs/.

Metrics (matches the published scoring path, i.e. m3 in compute_final_stats.py:
canonical matcher + designer-approved entity-conditional RNA alias):
  1. accepted-set size |A_i| per unit (raw and canonical);
  2. exact pre-normalization accuracy vs accepted-set accuracy (the gap is the
     synonym-rescue mass that the published canonical matcher recovers);
  3. performance stratified by canonical |A_i|;
  4. explicit table of units with |A_i| > 1 (one-to-many inverse mapping);
  5. identifiability map: (entity, direction) -> accepted canonical set, flagging
     any unit whose accepted type cannot be inferred from the visible input.
"""
import csv, gzip, json, sys, importlib.util as iu
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent / "outputs"

_s1 = iu.spec_from_file_location("s1", ROOT / "evaluation_v3.7.0/scoring/score_model_outputs_base_v3_6_1.py")
m1 = iu.module_from_spec(_s1); _s1.loader.exec_module(m1)
canon = m1.canonical_intervention
normalize = m1.base.normalize if hasattr(m1, "base") else None
if normalize is None:  # base_v3_6_0 exposes normalize as module attr of `base`
    _s0 = iu.spec_from_file_location("s0", ROOT / "evaluation_v3.7.0/scoring/score_model_outputs_base_v3_6_0.py")
    m0 = iu.module_from_spec(_s0); _s0.loader.exec_module(m0)
    normalize = m0.normalize

def is_rna(entity): return "mir" in (entity or "").lower().replace(" ", "")
def canon_ent(v, ent):
    c = canon(v)
    return "inhibition" if (is_rna(ent) and c == "knockdown") else c

DISPLAY = {"GPT-6-Astra": "GPT-6-Astra", "Claude-Sonnet-5.5": "Claude-Sonnet-5.5",
           "Gemini-3.8-Flash": "Gemini-3.8-Flash", "GLM-5.3-Flash": "GLM-5.3-Flash",
           "Grok-4.6": "Grok-4.6", "Biomni": "Biomni (tools)"}

# ---------- load gold (raw accepted sets) ----------
gold = {}
with gzip.open(ROOT / "evaluation_v3.7.0/task3/hidden_labels.tsv.gz", "rt") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        acc_raw = json.loads(r["accepted_intervention_types_json"])
        gold[r["unit_id"]] = {
            "pair_id": r["pair_id"], "entity": r["input_perturbed_entity"],
            "direction": r["direction"], "acc_raw": acc_raw,
            "acc_canon": sorted({canon(x) for x in acc_raw}),
        }

# ---------- load MASTER task3 (frozen per-unit-run rows) ----------
def rd(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t"); rows = []; last = None
    for l in lines[1:]:
        if not l.strip(): continue
        parts = l.split("\t")
        if parts[0].strip().startswith("T3VP_"):
            vals = parts + [""] * (len(header) - len(parts))
            last = dict(zip(header, vals[:len(header)])); rows.append(last)
        elif last is not None:
            last[header[-1]] += " " + l.strip()
    return header, rows

_, rows = rd(ROOT / "runs/MASTER_task3.tsv")
hdr, _ = rd(ROOT / "runs/MASTER_task3.tsv")
IDX = {c: i for i, c in enumerate(hdr)}
def one(r): return str(r).strip() in ("1", "1.0", "true", "True")

# ---------- per-unit-run scoring ----------
rescued = {"rna_alias": [], "other_synonym": []}
per_sys = defaultdict(lambda: {"n": 0, "exact": 0, "acc": 0, "chain": 0, "joint": 0})
per_card = defaultdict(lambda: {"n": 0, "exact": 0, "acc": 0, "chain": 0, "joint": 0})
tot = {"n": 0, "exact": 0, "acc": 0, "chain": 0, "joint": 0}
per_unit = defaultdict(lambda: {"n": 0, "exact": 0, "acc": 0, "chain": 0, "joint": 0})

for r in rows:
    u = r["unit_id"]; g = gold[u]; ent = g["entity"]; pc = r["predicted_intervention_type"]
    exact_ok = normalize(pc) in {normalize(x) for x in g["acc_raw"]}
    acc_ok = one(r["type_accepted"])                     # published canonical + RNA alias
    chain_ok = one(r["chain_pass"]); joint_ok = one(r["joint_pass"])
    card = len(g["acc_canon"])
    sysname = DISPLAY.get(r["system"], r["system"])
    for bucket in (per_sys[sysname], per_card[card], tot, per_unit[u]):
        bucket["n"] += 1
        bucket["exact"] += exact_ok; bucket["acc"] += acc_ok
        bucket["chain"] += chain_ok; bucket["joint"] += joint_ok
    if acc_ok and not exact_ok:
        tag = "rna_alias" if (is_rna(ent) and canon(pc) == "knockdown") else "other_synonym"
        rescued[tag].append({"unit_id": u, "system": sysname, "run": r["run"], "pred": pc,
                             "accepted_raw": g["acc_raw"]})

pct = lambda a, b: round(100 * a / b, 1) if b else None

summary = {
    "scope": "Task 3, 6 systems x 4 runs x 20 units = 480 unit-runs (frozen MASTER_task3.tsv)",
    "per_system": {s: {k: (v[k] if k == "n" else pct(v[k], v["n"])) for k in v} for s, v in per_sys.items()},
    "per_cardinality": {str(k): {kk: (vv[kk] if kk == "n" else pct(vv[kk], vv["n"])) for kk in vv}
                        for k, vv in sorted(per_card.items())},
    "pooled": {k: (v if k == "n" else pct(v, tot["n"])) for k, v in tot.items()},
    "rescued_by_category": {k: len(v) for k, v in rescued.items()},
    "rescued_examples_other": rescued["other_synonym"][:12],
    "rescued_ids_rna": sorted({x["unit_id"] for x in rescued["rna_alias"]}),
}
multi = {u: g for u, g in gold.items() if len(g["acc_canon"]) > 1}
summary["units_with_multi_accepted"] = [
    {"unit_id": u, "pair_id": g["pair_id"], "entity": g["entity"], "direction": g["direction"],
     "accepted_raw": g["acc_raw"], "accepted_canonical": g["acc_canon"]} for u, g in sorted(multi.items())]

# ---------- identifiability map: (entity, direction) -> accepted canonical sets ----------
ed2sets = defaultdict(set); ed2units = defaultdict(list)
for u, g in gold.items():
    ed2sets[(g["entity"].lower(), g["direction"])].add(tuple(g["acc_canon"]))
    ed2units[(g["entity"].lower(), g["direction"])].append(u)
conflicts = {k: sorted(v) for k, v in ed2sets.items() if len(v) > 1}
# same entity, different directions mapping to different types (input-disambiguated, not a conflict)
ent2dir_type = defaultdict(dict)
for (e, d), sets_ in ed2sets.items():
    ent2dir_type[e][d] = sorted({t for s_ in sets_ for t in s_})
summary["identifiability"] = {
    "n_entity_direction_combos": len(ed2sets),
    "combos_with_conflicting_accepted_sets": conflicts,
    "combo_table": [
        {"entity": e, "direction": d, "units": ed2units[(e, d)],
         "accepted_canonical_union": sorted({t for s_ in ed2sets[(e, d)] for t in s_})}
        for (e, d) in sorted(ed2sets)],
}
# per-unit exact vs accepted gap (largest gaps)
unit_gaps = sorted(per_unit.items(), key=lambda kv: (kv[1]["acc"] - kv[1]["exact"]), reverse=True)
summary["per_unit_exact_vs_accepted"] = [
    {"unit_id": u, "entity": gold[u]["entity"], "direction": gold[u]["direction"],
     "card": len(gold[u]["acc_canon"]), "n": v["n"],
     "exact_pct": pct(v["exact"], v["n"]), "accepted_pct": pct(v["acc"], v["n"])}
    for u, v in unit_gaps]

json.dump(summary, open(OUT / "L_ACCEPTED_SET.json", "w"), indent=1, ensure_ascii=False)

# ---------- HTML ----------
CSS = """<html><head><meta charset="utf-8"><title>Appendix L — Identifiability and Accepted-Set Analysis for Task 3</title><style>
body{font-family:'Times New Roman',serif;font-size:11pt;max-width:720px;margin:36px auto;color:#111;line-height:1.6;}
h1{font-size:13pt;} h2{font-size:11.5pt;margin:22px 0 6px;} h3{font-size:11pt;margin:14px 0 4px;color:#222;font-style:italic;}
p{margin:8px 0;text-align:justify;}
table{border-collapse:collapse;margin:12px auto;width:100%;}
th,td{border:1px solid #bbb;padding:4px 7px;font-size:9.5pt;text-align:center;}
th{background:#f2f2f2;} td:first-child{text-align:left;}
.fn{font-size:8.5pt;color:#555;margin:5px 0;line-height:1.4;text-align:left;}
code{font-family:Menlo,monospace;font-size:8.5pt;background:#f6f6f2;padding:0 3px;}
</style></head><body>"""

S = summary
ps = S["per_system"]; pcs = S["per_cardinality"]
sys_rows = "".join(
    f"<tr><td>{s}</td><td>{v['exact']}</td><td>{v['acc']}</td><td><b>{round(v['acc']-v['exact'],1)}</b></td>"
    f"<td>{v['joint']}</td></tr>"
    for s, v in ps.items())
card_rows = "".join(
    f"<tr><td>|A<sub>i</sub>| = {k} ({v['n']} unit-runs)</td><td>{v['exact']}</td><td>{v['acc']}</td>"
    f"<td>{v['chain']}</td><td>{v['joint']}</td></tr>" for k, v in pcs.items())
multi_rows = "".join(
    f"<tr><td>{m['unit_id']}</td><td>{m['entity']} ({m['direction']})</td>"
    f"<td>{', '.join(m['accepted_raw'])}</td><td>{', '.join(m['accepted_canonical'])}</td></tr>"
    for m in S["units_with_multi_accepted"]) or "<tr><td colspan=4>none</td></tr>"
gap_rows = "".join(
    f"<tr><td>{d['unit_id']}</td><td>{d['entity']} ({d['direction']})</td><td>{d['card']}</td>"
    f"<td>{d['exact_pct']}</td><td>{d['accepted_pct']}</td><td>{round(d['accepted_pct']-d['exact_pct'],1)}</td></tr>"
    for d in S["per_unit_exact_vs_accepted"][:8])
combo_rows = "".join(
    f"<tr><td>{c['entity']} ({c['direction']})</td><td>{', '.join(c['units'])}</td>"
    f"<td>{', '.join(c['accepted_canonical_union'])}</td></tr>"
    for c in S["identifiability"]["combo_table"])

html = CSS + f"""
<h1>Appendix L — Identifiability and Accepted-Set Analysis for Task 3</h1>
<p><b>Status.</b> Post-freeze analysis addendum ({OUT.name} layer). This appendix introduces no new biological
labels and does not alter any frozen value. It re-examines the Task 3 answer space as defined by the shipped
per-unit accepted intervention sets <i>A<sub>i</sub></i> (evaluation bundle, <code>accepted_intervention_types_json</code>),
using the same scoring path as the main tables (canonical matcher plus the disclosed designer-approved
entity-conditional RNA alias).</p>

<h2>L.1 Accepted-set cardinality</h2>
<p>Task 3 contains 20 units over 9 bidirectional pairs. The number of accepted intervention types per unit,
|<i>A<sub>i</sub></i>| (after canonicalization), is <b>1 for {20 - len(S['units_with_multi_accepted'])} units and
&gt;1 for {len(S['units_with_multi_accepted'])} units</b>. Where |<i>A<sub>i</sub></i>| &gt; 1 the inverse mapping
from the observed direction and perturbed entity back to the intervention that was applied is genuinely
one-to-many: more than one intervention is consistent with the benchmark's own labels, and a system cannot be
expected to distinguish them from the visible input alone. These units are therefore reported separately
throughout this appendix and should not be treated as strict one-to-one inverse-mapping probes.</p>

<h3>Table L1 | Units with multiple accepted intervention types (|A<sub>i</sub>| &gt; 1)</h3>
<table><tr><th>Unit</th><th>Entity (direction)</th><th>Accepted (raw label set)</th><th>Accepted (canonical)</th></tr>
{multi_rows}</table>
<p class="fn">Raw sets are the shipped <code>accepted_intervention_types_json</code>; canonical sets apply the shipped
synonym whitelist. Any answer inside either set is scored accepted under the published rule
(<code>multiple_answer_policy: any accepted perturbation for the same pair and supplied direction is correct</code>).</p>

<h2>L.2 Exact-match vs accepted-set accuracy</h2>
<p>The shipped scorer reports two layers: <i>exact pre-normalization</i> accuracy (the raw answer string matches a
raw gold label verbatim after case/punctuation normalization) and <i>accepted-set</i> accuracy (the canonicalized
answer falls in the canonical accepted set). The gap between the two is synonym-rescue mass: answers that are
methodologically equivalent to an accepted label but worded outside the raw label set. The main tables use the
accepted-set layer, with the RNA alias disclosed in Appendix B; the exact layer is reported here for transparency.</p>

<h3>Table L2 | Per-system exact vs accepted-set type accuracy, chain pass and joint pass (%, 4-run pooled)</h3>
<table><tr><th>System</th><th>Exact (pre-norm.)</th><th>Accepted set (published)</th><th>Rescue gap</th><th>Joint pass</th></tr>
{sys_rows}</table>
<p class="fn">Pooled over 480 unit-runs: exact {S['pooled']['exact']}% vs accepted-set {S['pooled']['acc']}%
(rescued unit-runs: {S['rescued_by_category']['rna_alias']} via the disclosed RNA alias,
{S['rescued_by_category']['other_synonym']} via other whitelist synonyms). Chain pass is identical under both
layers by construction — the adjudication axes do not depend on the type matcher — so only the joint metric moves.</p>

<h3>Table L3 | Performance stratified by accepted-set cardinality</h3>
<table><tr><th>Stratum</th><th>Exact (%)</th><th>Accepted set (%)</th><th>Chain pass (%)</th><th>Joint pass (%)</th></tr>
{card_rows}</table>
<p class="fn">Units with |<i>A<sub>i</sub></i>| &gt; 1 are easier on the type metric by construction (a larger
acceptance region); the cardinality split is reported so that the strict one-to-one subset can be read in isolation.</p>

<h2>L.3 Identifiability of the inverse task from the visible input</h2>
<p>Task 3 shows the model a (TF–gene pair, direction, perturbed entity) triple and asks which intervention was
applied to the entity. The task is identifiable from the visible input only if the benchmark's own labels make
(entity, direction) determine the accepted set. The map below enumerates every (entity, direction) combination
in the task with its accepted canonical union.
{('<b>Every (entity, direction) combination maps to a single accepted canonical set, so no unit is unidentifiable from the input given the labels.</b>' if not conflicts else '<b>Conflicting combinations (same visible input, different accepted sets across units): ' + str(conflicts) + '</b>')}
The residual non-identifiability is of a second kind and is disclosed in Appendix B.6: the input does not always
determine which concrete method within an accepted class was used (e.g. siRNA vs shRNA vs knockout; agonist vs
overexpression), and the whitelist settles those cases by construction rather than by inference.</p>

<h3>Table L4 | (Entity, direction) → accepted canonical set</h3>
<table><tr><th>Entity (direction)</th><th>Units</th><th>Accepted canonical union</th></tr>
{combo_rows}</table>

<h2>L.4 Largest exact-vs-accepted gaps per unit</h2>
<h3>Table L5 | Units with the largest rescue mass (exact vs accepted-set type accuracy, pooled 4 runs)</h3>
<table><tr><th>Unit</th><th>Entity (direction)</th><th>|A<sub>i</sub>|</th><th>Exact (%)</th><th>Accepted (%)</th><th>Gap</th></tr>
{gap_rows}</table>

<h2>L.5 Reading guidance</h2>
<p>(i) Joint-pass values on |<i>A<sub>i</sub></i>| &gt; 1 units should be read as "the system found one of the
benchmark-accepted interventions", not "the system recovered the intervention that was performed".
(ii) The cardinality split (Table L3) is the strict one-to-one readout.
(iii) All values in this appendix are recomputed from the frozen MASTER table and the shipped hidden-label
bundle; none modifies or supersedes the main-text Task 3 numbers, which remain the accepted-set (published) layer.</p>
</body></html>"""

(OUT / "APPENDIX_L_accepted_set.html").write_text(html, encoding="utf-8")
print("== pooled ==");  print(S["pooled"])
print("== per-system ==")
for s, v in ps.items(): print(f"  {s:<22} exact {v['exact']:>5}  accepted {v['acc']:>5}  chain {ps[s]}")
print("== per cardinality ==")
for k, v in pcs.items(): print(f"  |A|={k}: n={v['n']} exact={v['exact']} acc={v['acc']} chain={v['chain']} joint={v['joint']}")
print("== |A|>1 units:", [m['unit_id'] for m in S['units_with_multi_accepted']])
print("== conflicts:", S["identifiability"]["combos_with_conflicting_accepted_sets"])
print("== rescued:", S["rescued_by_category"])
print("WROTE", OUT / "APPENDIX_L_accepted_set.html")
