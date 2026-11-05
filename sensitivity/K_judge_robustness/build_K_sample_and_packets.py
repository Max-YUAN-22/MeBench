#!/usr/bin/env python3
"""Appendix K step 1 — stratified sample + rejudge packets.

Draws a frozen, seed-disclosed stratified sample from the frozen MASTER tables:
  Task 2: 6 systems x (30 chain-pass / 30 chain-fail) = 360 unit-runs; within each
          system's fail stratum, quota-sampled to guarantee coverage of each failed
          axis (>=6 rows with mechanism=0, >=6 mediator=0, >=6 causal-order=0).
  Task 3: full enumeration of all 480 unit-runs (20 units x 6 systems x 4 runs).

Then rebuilds, for every sampled unit-run, the SAME adjudication content the original
judge saw (model input, prediction, reasoning, evaluator-only gold fields), extracted
from the archived per-run packets, and writes batched rejudge packets under packets/.
The original judge's axis values are NOT included. Row keys are composite
`unit_id@system@run` strings; the judge instructions are byte-identical to the shipped
adjudicator prompt.

Seed 20261017. Sample design frozen in sample_design.json before any model call.
"""
import gzip, json, random, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SEED = 20261017
AXES = ["mechanism_correct", "mediator_correct", "causal_role_order_correct",
        "intervention_outcome_link_correct", "no_material_contradiction"]
SLIM = ["mechanism_reasoning", "ground_truth_mechanism", "ground_truth_mediator_type",
        "ground_truth_mediator_entity", "ground_truth_causal_topology", "ground_truth_evidence_chain"]
DISPLAY = {"gpt": "GPT-6-Astra", "claude": "Claude-Sonnet-5.5", "gemini": "Gemini-3.8-Flash",
           "glm": "GLM-5.3-Flash", "grok": "Grok-4.6", "biomni": "Biomni"}
BATCH = 40

SYS_DIRS = {
    "gpt":    [("runs/gpt", 1), ("runs/run2/gpt", 2), ("runs/run3/gpt", 3), ("runs/run4/gpt", 4)],
    "claude": [("runs/claude", 1), ("runs/run2/claude", 2), ("runs/run3/claude", 3), ("runs/run4/claude", 4)],
    "gemini": [("runs_gemini/official", 1), ("runs_gemini/rep1", 2), ("runs_gemini/rep2", 3), ("runs_gemini/rep3", 4)],
    "glm":    [(f"runs_extras/glm/pass{i}", i) for i in (1, 2, 3, 4)],
    "grok":   [(f"runs_extras/grok/pass{i}", i) for i in (1, 2, 3, 4)],
    "biomni": [(f"runs_biomni_agent/pass{i}", i) for i in (1, 2, 3, 4)],
}
def one(v): return str(v).strip() in ("1", "1.0", "true", "True")

def rd(path):
    """Records keyed lines start with a unit id; continuation lines append to the
    last record's final column (verbatim-rd convention). Returns a list of dicts."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t"); rows = []; last = None
    for l in lines[1:]:
        if not l.strip(): continue
        parts = l.split("\t")
        if parts[0].strip().startswith(("T2U_", "T3VP_")):
            vals = parts + [""] * (len(header) - len(parts))
            last = dict(zip(header, vals[:len(header)])); rows.append(last)
        elif last is not None:
            last[header[-1]] += " " + l.strip()
    return rows

def master_rows(task):
    rows = rd(ROOT / f"runs/MASTER_{task}.tsv")
    for r in rows:
        if r["system"] == "Biomni":
            r["system"] = "Biomni"
        r["run"] = int(r["run"])
    return rows

def packet_path(base: Path, task):
    for cand in (base / task / f"{task}_packet.tsv", base / f"{task}_packet.tsv",
                 base / f"{task}_reasoning_review.tsv"):
        if cand.exists(): return cand
    raise FileNotFoundError(f"no packet for {base}/{task}")

m2 = master_rows("task2"); m3 = master_rows("task3")
rng = random.Random(SEED)

# ---------- Task 2 stratified sample ----------
sample2 = []
marg = {"pass": defaultdict(int), "fail": defaultdict(int)}
axis_fail_cover = defaultdict(int)
for sysname in DISPLAY.values():
    pool = [r for r in m2 if r["system"] == sysname]
    passes = [r for r in pool if one(r["chain_pass"])]
    fails = [r for r in pool if not one(r["chain_pass"])]
    rng.shuffle(passes); rng.shuffle(fails)
    take = passes[:30]
    # quota fill for axis coverage inside the fail stratum
    quotas = {"mechanism_correct": 6, "mediator_correct": 6, "causal_role_order_correct": 6}
    chosen, seen = [], set()
    for ax, q in quotas.items():
        cand = [r for r in fails if not one(r[ax]) and r["unit_id"] not in seen]
        rng.shuffle(cand)
        for r in cand[:q]:
            chosen.append(r); seen.add(r["unit_id"]); axis_fail_cover[ax] += 1
    rest = [r for r in fails if r["unit_id"] not in seen]
    chosen += rest[:30 - len(chosen)]
    for r in take:
        sample2.append(r); marg["pass"]["chain_pass"] += 1
        for ax in AXES: marg["pass"][ax] += one(r[ax])
    for r in chosen:
        sample2.append(r); marg["fail"]["chain_pass"] += 0
        for ax in AXES: marg["fail"][ax] += one(r[ax])
assert len(sample2) == 360, len(sample2)

# ---------- Task 3 full enumeration ----------
sample3 = sorted(m3, key=lambda r: (r["system"], r["run"], r["unit_id"]))
assert len(sample3) == 480, len(sample3)

# ---------- packets ----------
def load_packets(task):
    """packet rows keyed by (system, run, unit_id)"""
    out = {}
    for skey, dirs in SYS_DIRS.items():
        for d, run in dirs:
            p = packet_path(ROOT / d, task)
            for r in rd(p):
                out[(DISPLAY[skey], run, r["unit_id"])] = r
    return out

pk2 = load_packets("task2"); pk3 = load_packets("task3")
missing = [k for k in [(r["system"], r["run"], r["unit_id"]) for r in sample2 + sample3]
           if k not in pk2 and k not in pk3]
if missing:
    print("MISSING PACKETS:", missing[:10], "...", len(missing)); sys.exit(1)

design = {"seed": SEED, "batch_size": BATCH,
          "judge": "gemini-3.8-flash (never used as a judge in the frozen pipeline)",
          "task2_sample": [], "task3_sample": []}
for r in sample2:
    key = f"{r['unit_id']}@{r['system']}@run{r['run']}"
    design["task2_sample"].append({"key": key, "stratum": "pass" if one(r["chain_pass"]) else "fail"})
for r in sample3:
    key = f"{r['unit_id']}@{r['system']}@run{r['run']}"
    design["task3_sample"].append({"key": key})
design["task2_axis_marginals"] = {k: dict(v) for k, v in marg.items()}
design["task3_axis_marginals"] = {
    ax: sum(one(r[ax]) for r in sample3) for ax in AXES}
design["task3_chain_pass_orig"] = sum(one(r["chain_pass"]) for r in sample3)

JUDGE_INSTR = (ROOT / "run_v37.py").read_text(encoding="utf-8").split('JUDGE_INSTR = """')[1].split('"""')[0]

def write_batches(rows, pkmap, task, tag):
    rows = sorted(rows, key=lambda r: r["unit_id"])
    (HERE / "packets" / f"{task}_manifest.json").write_text(json.dumps(
        [{"key": f"{r['unit_id']}@{r['system']}@run{r['run']}",
          "orig_axes": {a: int(one(r[a])) for a in AXES},
          "orig_chain_pass": int(one(r["chain_pass"]))} for r in rows], indent=1))
    n_batches = 0
    for b in range(0, len(rows), BATCH):
        chunk = rows[b:b + BATCH]
        body = "unit_id\t" + "\t".join(SLIM) + "\n"
        for r in chunk:
            pk = pkmap[(r["system"], r["run"], r["unit_id"])]
            body += f"{r['unit_id']}@{r['system']}@run{r['run']}\t" + \
                    "\t".join((pk.get(c, "") or "").replace("\t", " ").replace("\n", " ").strip()
                              for c in SLIM) + "\n"
        n_batches += 1
        (HERE / "packets" / f"{tag}_batch{n_batches:02d}.txt").write_text(
            JUDGE_INSTR + "\n\n" + body, encoding="utf-8")
    return n_batches

nb2 = write_batches(sample2, pk2, "task2", "task2_rejudge")
nb3 = write_batches(sample3, pk3, "task3", "task3_rejudge")
(HERE / "sample_design.json").write_text(json.dumps(design, indent=1))
print(f"task2: {len(sample2)} rows in {nb2} batches; task3: {len(sample3)} rows in {nb3} batches")
print("fail-stratum axis coverage:", dict(axis_fail_cover))
print("task2 pass-stratum axis means:", {a: round(100 * marg['pass'][a] / 180, 1) for a in AXES})
print("task2 fail-stratum axis means:", {a: round(100 * marg['fail'][a] / 180, 1) for a in AXES})
print("task3 orig chain pass:", design["task3_chain_pass_orig"], "/480")
