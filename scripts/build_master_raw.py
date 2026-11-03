#!/usr/bin/env python3
"""Build consolidated master raw-data tables:
  runs/MASTER_task1.tsv  (unit x system x run: Task 1 mechanism classification)
  runs/MASTER_task2.tsv  (Task 2 direction + five-axis chain, with reasoning text)
  runs/MASTER_task3.tsv  (Task 3 inverse inference, with reasoning text)
Every row carries the question, the gold, the model's raw answer, the five-axis
judgments, and the derived flags used in every published number."""
import csv, gzip, json, re, glob, os, statistics as st
import importlib.util as iu

BASE = "/Users/Apple/Desktop/UIUC项目/test10:8/v3.7"
os.chdir(BASE)

# canonical scorer layer (type normalization + RNA alias) — same as published T3 scoring
spec = iu.spec_from_file_location("s37", "evaluation_v3.7.0/scoring/score_model_outputs.py")
mm = iu.module_from_spec(spec); spec.loader.exec_module(mm)
prev = mm.previous
def is_rna(e): e = (e or '').lower().replace(' ', ''); return 'mir' in e
def canon(v, ent):
    c = prev.canonical_intervention(v)
    return 'inhibition' if (is_rna(ent) and c == 'knockdown') else c

def rd(p):
    lines = open(p, encoding='utf-8').read().splitlines()
    if not lines: return {}
    header = lines[0].split('\t'); ncol = len(header)
    rows = {}; last = None
    for l in lines[1:]:
        if not l.strip(): continue
        parts = l.split('\t'); uid = parts[0].strip()
        if re.match(r"^(T1U_|T2U_|T3VP_)", uid):
            vals = parts + [""]*(ncol-len(parts))
            rows[uid] = dict(zip(header, vals[:ncol])); last = uid
        elif last is not None:
            rows[last][header[-1]] += " " + l.strip()
    return rows

def jud_path(d, task):
    g = sorted(glob.glob(f"{d}/{task}/{task}*judgments.tsv")) + sorted(glob.glob(f"{d}/{task}*judgments.tsv"))
    return g[0] if g else None

AXES = ["mechanism_correct","mediator_correct","causal_role_order_correct",
        "intervention_outcome_link_correct","no_material_contradiction"]
def truthy(v):
    return str(v).strip() in ('1','1.0','true','True')

SYS = [("GPT-6-Astra","gpt",["runs/gpt","runs/run2/gpt","runs/run3/gpt","runs/run4/gpt"]),
       ("Claude-Sonnet-5.5","claude",["runs/claude","runs/run2/claude","runs/run3/claude","runs/run4/claude"]),
       ("Gemini-3.8-Flash","gemini",[f"runs_gemini/{r}" for r in ("official","rep1","rep2","rep3")]),
       ("GLM-5.3-Flash","glm",[f"runs_extras/glm/pass{i}" for i in (1,2,3,4)]),
       ("Grok-4.6","grok",[f"runs_extras/grok/pass{i}" for i in (1,2,3,4)]),
       ("Biomni","biomni-agent",[f"runs_biomni_agent/pass{i}" for i in (1,2,3,4)])]

def load_inputs(task):
    out = {}
    with gzip.open(f'evaluation_v3.7.0/{task}/inputs.jsonl.gz','rt') as f:
        for line in f:
            d = json.loads(line); out[d['unit_id']] = d['model_input']
    return out
def load_hidden(task):
    return {r['unit_id']: r for r in csv.DictReader(gzip.open(f'evaluation_v3.7.0/{task}/hidden_labels.tsv.gz','rt'), delimiter='\t')}
def gold_json(u, hmap):
    return json.loads(hmap[u]['reasoning_ground_truth_json'])

def pred_path(d, task):
    p = os.path.join(d, f"{task}_predictions.tsv")
    if os.path.exists(p): return p
    return os.path.join(d, task, f"{task}_predictions.tsv")

# ---------- Task 1 ----------
i1 = load_inputs('task1'); h1 = load_hidden('task1')
out1 = []
for nm, mk, dirs in SYS:
    for ri, d in enumerate(dirs, 1):
        pred = rd(pred_path(d, "task1"))
        for u, h in h1.items():
            mi = i1.get(u, {})
            pm = (pred.get(u, {}).get('predicted_mechanism') or '').strip()
            out1.append({
                "unit_id": u, "pair_id": h['pair_id'],
                "tf": mi.get('tf',''), "target_gene": mi.get('target_gene',''),
                "gold_mechanism": h['mechanism'],
                "system": nm, "run": ri,
                "predicted_mechanism": pm,
                "correct": int(pm == h['mechanism']),
            })
with open('runs/MASTER_task1.tsv','w',newline='',encoding='utf-8') as f:
    w = csv.DictWriter(f, delimiter='\t', fieldnames=list(out1[0].keys()))
    w.writeheader(); w.writerows(out1)
print(f"MASTER_task1.tsv: {len(out1)} rows")

# ---------- Task 2 ----------
i2 = load_inputs('task2'); h2 = load_hidden('task2')
g2 = {u: gold_json(u, h2) for u in h2}
out2 = []
for nm, mk, dirs in SYS:
    for ri, d in enumerate(dirs, 1):
        pred = rd(pred_path(d, "task2"))
        jp = jud_path(d, "task2")
        judg = rd(jp) if jp else {}
        for u, h in h2.items():
            mi = i2.get(u, {}); g = g2[u]
            pr = pred.get(u, {})
            dir_ok = int((pr.get('predicted_direction','') or '').strip().lower() == g['task_specific_link']['expected_direction'])
            axes = {a: int(truthy(judg.get(u, {}).get(a,''))) for a in AXES} if u in judg else {a: '' for a in AXES}
            chain = int(all(axes[a] == 1 for a in AXES)) if u in judg else ''
            out2.append({
                "unit_id": u, "pair_id": h['pair_id'],
                "tf": mi.get('tf',''), "target_gene": mi.get('target_gene',''),
                "intervention_type": mi.get('perturbation',{}).get('intervention_type',''),
                "perturbed_entity": mi.get('perturbation',{}).get('perturbed_entity',''),
                "gold_mechanism": g['mechanism_class'],
                "gold_mediator": g['mediator_entity'],
                "gold_causal_topology": g['causal_topology'],
                "expected_direction": g['task_specific_link']['expected_direction'],
                "system": nm, "run": ri,
                "predicted_direction": (pr.get('predicted_direction','') or '').strip(),
                "dir_correct": dir_ok,
                **axes,
                "chain_pass": chain,
                "joint_pass": (dir_ok * chain) if chain != '' else '',
                "mechanism_reasoning": (pr.get('mechanism_reasoning','') or '').strip(),
            })
with open('runs/MASTER_task2.tsv','w',newline='',encoding='utf-8') as f:
    w = csv.DictWriter(f, delimiter='\t', fieldnames=list(out2[0].keys()))
    w.writeheader(); w.writerows(out2)
print(f"MASTER_task2.tsv: {len(out2)} rows")

# ---------- Task 3 ----------
i3 = load_inputs('task3'); h3 = load_hidden('task3')
g3 = {u: gold_json(u, h3) for u in h3}
out3 = []
for nm, mk, dirs in SYS:
    for ri, d in enumerate(dirs, 1):
        pred = rd(pred_path(d, "task3"))
        jp = jud_path(d, "task3")
        judg = rd(jp) if jp else {}
        for u, h in h3.items():
            mi = i3.get(u, {}); g = g3[u]
            pr = pred.get(u, {})
            ent = mi.get('perturbation',{}).get('perturbed_entity','')
            pc = canon((pr.get('predicted_intervention_type','') or '').strip(), ent)
            acc = {canon(x, ent) for x in json.loads(h['accepted_intervention_types_json'])}
            type_ok = int(pc in acc)
            axes = {a: int(truthy(judg.get(u, {}).get(a,''))) for a in AXES} if u in judg else {a: '' for a in AXES}
            chain = int(all(axes[a] == 1 for a in AXES)) if u in judg else ''
            out3.append({
                "unit_id": u, "pair_id": h['pair_id'],
                "tf": mi.get('tf',''), "target_gene": mi.get('target_gene',''),
                "given_direction": mi.get('direction',''),
                "given_perturbed_entity": ent,
                "gold_accepted_types": ";".join(json.loads(h['accepted_intervention_types_json'])),
                "gold_mechanism": g['mechanism_class'],
                "gold_mediator": g['mediator_entity'],
                "gold_causal_topology": g['causal_topology'],
                "system": nm, "run": ri,
                "predicted_intervention_type": (pr.get('predicted_intervention_type','') or '').strip(),
                "predicted_type_canonical": pc,
                "type_accepted": type_ok,
                **axes,
                "chain_pass": chain,
                "joint_pass": (type_ok * chain) if chain != '' else '',
                "mechanism_reasoning": (pr.get('mechanism_reasoning','') or '').strip(),
            })
with open('runs/MASTER_task3.tsv','w',newline='',encoding='utf-8') as f:
    w = csv.DictWriter(f, delimiter='\t', fieldnames=list(out3[0].keys()))
    w.writeheader(); w.writerows(out3)
print(f"MASTER_task3.tsv: {len(out3)} rows")

# sanity: recompute published means from the master tables and compare
def mean_from(rows, key, pred=None):
    vals = [r[key] for r in rows if r[key] != '']
    return st.mean(vals)*100 if vals else None
t2 = out2
for nm, mk, _ in SYS:
    sub = [r for r in t2 if r['system'] == nm]
    jp = st.mean([r['joint_pass'] for r in sub])*100
    m = json.load(open('runs/MASTER_FINAL_STATS.json'))[mk]['t2jp']
    assert abs(jp - m) < 0.051, (nm, jp, m)
print("cross-check vs MASTER_FINAL_STATS: OK (joint pass matches for all systems)")
EOF_MARKER = True
