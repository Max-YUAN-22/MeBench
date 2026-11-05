#!/usr/bin/env python3
"""Joint-level accuracy metrics for all systems:
T2: Joint Pass Rate, Balanced Joint Acc, Joint F1
T3: Type Acc (accepted), Balanced Joint Acc, Joint F1

Convention (aligned with compute_final_stats.py / compute_recomb_tables.py):
chain-gated metrics are computed ONLY over runs that have a judgment file;
unadjudicated runs are excluded from the mean, never counted as zero.
T3 uses the designer-approved rna-knockdown≡inhibition alias (same as m3 in
compute_final_stats.py), so these values match the published tables.

v2 fix (2026-10-16): earlier version appended zero-filled joint metrics for
unadjudicated runs (Claude T2 runs 2-3 had no judgment files at the time),
which reported Claude T2 JointF1 as 38.2 instead of 76.4; and computed T3 via
a re-imported scorer layer whose canonicalization diverged from the published
one (Claude T3 JointF1 18.2 vs 25.6). Both paths now reuse the published logic.
"""
import json, csv, gzip, glob, re, statistics as st
from pathlib import Path
import importlib.util as iu

AXES = ["mechanism_correct","mediator_correct","causal_role_order_correct",
        "intervention_outcome_link_correct","no_material_contradiction"]
_s2 = iu.spec_from_file_location("s2", "evaluation_v3.7.0/scoring/score_model_outputs.py")
_mm = iu.module_from_spec(_s2); _s2.loader.exec_module(_mm)
prev = _mm.previous
def is_rna(e): e=(e or '').lower().replace(' ',''); return 'mir' in e

def rd(p):
    with open(p, encoding='utf-8') as f:
        lines = f.read().splitlines()
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

def jud_path(base, task):
    for pat in [str(Path(base)/task/f"{task}*judgments.tsv"), str(Path(base)/f"{task}*judgments.tsv")]:
        g = sorted(glob.glob(pat))
        if g: return g[0]
    return None

_h2 = {r['unit_id']: r for r in csv.DictReader(gzip.open('evaluation_v3.7.0/task2/hidden_labels.tsv.gz','rt'), delimiter='\t')}
_h3 = {r['unit_id']: r for r in csv.DictReader(gzip.open('evaluation_v3.7.0/task3/hidden_labels.tsv.gz','rt'), delimiter='\t')}

def f1(tp,fp,fn): return 2*tp/(2*tp+fp+fn) if (2*tp+fp+fn) else None
def cok_of(j,u): j=j.get(u); return bool(j) and all(str(j.get(a,"")).strip() in ('1','1.0','true','True') for a in AXES)

def canon(v, ent):
    c = prev.canonical_intervention(v)
    return 'inhibition' if (is_rna(ent) and c == 'knockdown') else c

def t3_classes():
    s = set()
    for _h in _h3.values():
        s |= {prev.canonical_intervention(x) for x in json.loads(_h['accepted_intervention_types_json'])}
    return sorted(s)

def t3_hit(c):
    return [u for u, _h in _h3.items()
            if c in {prev.canonical_intervention(x) for x in json.loads(_h['accepted_intervention_types_json'])}]

def t2m(pred, judg):
    def cok(u): return cok_of(judg,u)
    jp = st.mean([1*(pred[u]['predicted_direction'].strip().lower()==_h2[u]['direction'] and cok(u)) for u in _h2])
    bal=[]
    for c in ("up","down"):
        gold=[u for u in _h2 if _h2[u]['direction']==c]
        bal.append(st.mean([1*(pred[u]['predicted_direction'].strip().lower()==c and cok(u)) for u in gold]))
    f1s=[]
    for c in ("up","down"):
        tp=sum(1 for u,_h in _h2.items() if _h['direction']==c and pred[u]['predicted_direction'].strip().lower()==c and cok(u))
        fp=sum(1 for u,_h in _h2.items() if pred[u]['predicted_direction'].strip().lower()==c and not cok(u))
        fn=sum(1 for u,_h in _h2.items() if _h['direction']==c and not (pred[u]['predicted_direction'].strip().lower()==c and cok(u)))
        f1s.append(f1(tp,fp,fn))
    return {"jp":jp*100, "bj":st.mean(bal)*100, "jf1":st.mean(f1s)*100}

def t3m(pred, judg):
    def cok(u): return cok_of(judg,u)
    acc = st.mean([1*(canon(pred[u]['predicted_intervention_type'], _h3[u]['input_perturbed_entity']) in {prev.canonical_intervention(x) for x in json.loads(_h['accepted_intervention_types_json'])}) for u,_h in _h3.items()])
    vals=[]
    for c in t3_classes():
        vals.append(st.mean([1*(canon(pred[u]['predicted_intervention_type'], _h3[u]['input_perturbed_entity'])==c and cok(u)) for u in t3_hit(c)]))
    bj = st.mean(vals)*100
    f1j=[]
    for c in t3_classes():
        tp=fp=fn=0
        for uid,_h in _h3.items():
            accset={prev.canonical_intervention(x) for x in json.loads(_h['accepted_intervention_types_json'])}
            pc=canon(pred[uid]['predicted_intervention_type'], _h3[uid]['input_perturbed_entity'])
            ok_u = cok(uid)
            if pc==c:
                if c in accset and ok_u: tp+=1
                else: fp+=1
            else:
                if c in accset and ok_u: fn+=1
        v=f1(tp,fp,fn)
        if v is not None: f1j.append(v)
    return {"acc":acc*100, "bj":bj, "jf1":st.mean(f1j)*100}

SYSTEMS = {
 "gpt":    ["runs/gpt","runs/run2/gpt","runs/run3/gpt","runs/run4/gpt"],
 "claude": ["runs/claude","runs/run2/claude","runs/run3/claude","runs/run4/claude"],
 "gemini": ["runs_gemini/official","runs_gemini/rep1","runs_gemini/rep2","runs_gemini/rep3"],
 "glm":    [f"runs_extras/glm/pass{i}" for i in (1,2,3,4)],
 "grok":   [f"runs_extras/grok/pass{i}" for i in (1,2,3,4)],
 "biomni-agent": [f"runs_biomni_agent/pass{i}" for i in (1,2,3,4)],
 "biomni-notools": ["runs_biomni_notools/official","runs_biomni_notools/rep1","runs_biomni_notools/rep2","runs_biomni_notools/rep3"],
}
OUT={}
for mk, passes in SYSTEMS.items():
    A={"t2jp":[],"t2bj":[],"t2jf1":[],"t3acc":[],"t3bj":[],"t3jf1":[]}
    n2 = n3 = 0
    for b in passes:
        bb=Path(b)
        p2 = bb/"task2/task2_predictions.tsv"
        if not p2.exists(): p2 = bb/"task2_predictions.tsv"
        pred2 = rd(p2); j2p = jud_path(bb, "task2"); j2 = rd(j2p) if j2p else {}
        if j2:  # 链/joint 只计已判卷的轮（未判轮不计为 0）
            m2 = t2m(pred2, j2)
            A["t2jp"].append(m2["jp"]); A["t2bj"].append(m2["bj"]); A["t2jf1"].append(m2["jf1"]); n2 += 1
        p3 = bb/"task3/task3_predictions.tsv"
        if not p3.exists(): p3 = bb/"task3_predictions.tsv"
        pred3 = rd(p3); j3p = jud_path(bb, "task3"); j3 = rd(j3p) if j3p else {}
        if j3:
            m3 = t3m(pred3, j3)
            A["t3acc"].append(m3["acc"]); A["t3bj"].append(m3["bj"]); A["t3jf1"].append(m3["jf1"]); n3 += 1
    OUT[mk] = {k: round(st.mean(v),1) for k,v in A.items()}
    OUT[mk]["runs_t2"] = n2; OUT[mk]["runs_t3"] = n3
json.dump(OUT, open('runs/JOINT_ACC_STATS.json','w'), indent=1)
hdr = f"{'系统':<15} | {'T2jp':>6} {'T2bj':>6} {'T2jf1':>6} (n) | {'T3acc':>6} {'T3bj':>6} {'T3jf1':>6} (n)"
print(hdr); print("-"*len(hdr))
for mk, v in OUT.items():
    print(f"{mk:<15} | {v['t2jp']:>6.1f} {v['t2bj']:>6.1f} {v['t2jf1']:>6.1f} ({v['runs_t2']}) | {v['t3acc']:>6.1f} {v['t3bj']:>6.1f} {v['t3jf1']:>6.1f} ({v['runs_t3']})")
