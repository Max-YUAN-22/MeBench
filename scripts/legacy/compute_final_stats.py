#!/usr/bin/env python3
"""Final master statistics for all v3.7.0 systems (accuracy + balanced accuracy + mF1 + joint)."""
import json, csv, gzip, glob, statistics as st
from pathlib import Path
import importlib.util as iu

AXES = ["mechanism_correct","mediator_correct","causal_role_order_correct",
        "intervention_outcome_link_correct","no_material_contradiction"]
s2 = iu.spec_from_file_location("s2", "evaluation_v3.7.0/scoring/score_model_outputs.py")
mm = iu.module_from_spec(s2); s2.loader.exec_module(mm); prev = mm.previous

def is_rna(e): e=(e or '').lower().replace(' ',''); return 'mir' in e
def f1(tp,fp,fn): return 2*tp/(2*tp+fp+fn) if (2*tp+fp+fn) else None
def rd(p):
    import re as _re
    with open(p, encoding='utf-8') as f:
        lines = f.read().splitlines()
    if not lines: return {}
    header = lines[0].split('\t')
    ncol = len(header)
    rows = {}; last_uid = None
    for l in lines[1:]:
        if not l.strip(): continue
        parts = l.split('\t')
        uid = parts[0].strip() if parts else ""
        if _re.match(r"^(T1U_|T2U_|T3VP_)", uid) or uid in ("unit_id",):
            if uid == "unit_id": continue
            vals = parts + [""]*(ncol-len(parts))
            rows[uid] = dict(zip(header, vals[:ncol])); last_uid = uid
        elif last_uid is not None:
            # wrapped continuation line: append to previous record's last column
            rows[last_uid][header[-1]] += " " + l.strip()
    return rows
def cok_of(j,u): j=j.get(u); return bool(j) and all(str(j.get(a,"")).strip() in ('1','1.0','true','True') for a in AXES)

_h1 = {r['unit_id']: r['mechanism'] for r in csv.DictReader(gzip.open('evaluation_v3.7.0/task1/hidden_labels.tsv.gz','rt'), delimiter='\t')}
_h2 = {r['unit_id']: r for r in csv.DictReader(gzip.open('evaluation_v3.7.0/task2/hidden_labels.tsv.gz','rt'), delimiter='\t')}
_h3 = {r['unit_id']: r for r in csv.DictReader(gzip.open('evaluation_v3.7.0/task3/hidden_labels.tsv.gz','rt'), delimiter='\t')}

def m1(pred):
    acc = st.mean(1*(pred[u]['predicted_mechanism']==_h1[u]) for u in _h1)
    recs=[]; f1s=[]
    for c in sorted(set(_h1.values())):
        recs.append(st.mean(1*(pred[u]['predicted_mechanism']==c) for u in _h1 if _h1[u]==c))
        tp=sum(1 for u in _h1 if pred[u]['predicted_mechanism']==c==_h1[u])
        fp=sum(1 for u in _h1 if pred[u]['predicted_mechanism']==c and _h1[u]!=c)
        fn=sum(1 for u in _h1 if _h1[u]==c and pred[u]['predicted_mechanism']!=c)
        f1s.append(f1(tp,fp,fn))
    return acc, sum(recs)/4, sum(f1s)/4

def m2(pred, judg):
    acc = st.mean(1*(pred[u]['predicted_direction'].strip().lower()==_h2[u]['direction']) for u in _h2)
    recs=[st.mean(1*(pred[u]['predicted_direction'].strip().lower()==c) for u in _h2 if _h2[u]['direction']==c) for c in ("up","down")]
    f1s=[]
    for c in ("up","down"):
        tp=sum(1 for u in _h2 if pred[u]['predicted_direction'].strip().lower()==c==_h2[u]['direction'])
        fp=sum(1 for u in _h2 if pred[u]['predicted_direction'].strip().lower()==c!=_h2[u]['direction'])
        fn=sum(1 for u,_h in _h2.items() if _h['direction']==c and pred[u]['predicted_direction'].strip().lower()!=c)
        f1s.append(f1(tp,fp,fn))
    std=sum(f1s)/2
    jp = st.mean(1*(pred[u]['predicted_direction'].strip().lower()==_h2[u]['direction'] and cok_of(judg,u)) for u in _h2)
    f1s=[]
    for c in ("up","down"):
        tp=sum(1 for u,_h in _h2.items() if _h['direction']==c and pred[u]['predicted_direction'].strip().lower()==c and cok_of(judg,u))
        fp=sum(1 for u,_h in _h2.items() if pred[u]['predicted_direction'].strip().lower()==c and not cok_of(judg,u))
        fn=sum(1 for u,_h in _h2.items() if _h['direction']==c and not (pred[u]['predicted_direction'].strip().lower()==c and cok_of(judg,u)))
        f1s.append(f1(tp,fp,fn))
    return acc, sum(recs)/2, std, jp, sum(f1s)/2

def m3(pred, judg):
    def canon(v,ent):
        c=prev.canonical_intervention(v)
        return 'inhibition' if (is_rna(ent) and c=='knockdown') else c
    classes=set()
    for _h in _h3.values():
        classes |= {prev.canonical_intervention(x) for x in json.loads(_h['accepted_intervention_types_json'])}
    acc = st.mean(1*(canon(pred[u]['predicted_intervention_type'], _h3[u]['input_perturbed_entity']) in {prev.canonical_intervention(x) for x in json.loads(_h3[u]['accepted_intervention_types_json'])}) for u,_h in _h3.items())
    recs=[]; joint=[]
    for c in sorted(classes):
        tp=fp=fn=0; tpj=fpj=fnj=0
        for uid,_h in _h3.items():
            accset={prev.canonical_intervention(x) for x in json.loads(_h3[uid]['accepted_intervention_types_json'])}
            pc=canon(pred[uid]['predicted_intervention_type'], _h3[uid]['input_perturbed_entity'])
            cok=cok_of(judg,uid)
            if pc==c:
                if c in accset: tp+=1
                else: fp+=1
                if c in accset and cok: tpj+=1
                else: fpj+=1
            else:
                if c in accset: fn+=1
                if c in accset and cok: fnj+=1
        v=f1(tp,fp,fn)
        if v is not None: recs.append(v)
        vj=f1(tpj,fpj,fnj)
        if vj is not None: joint.append(vj)
    chain = st.mean([1*cok_of(judg,u) for u in _h3])
    return acc, (sum(recs)/len(recs) if recs else 0), (sum(recs)/len(recs) if recs else 0), chain, (sum(joint)/len(joint) if joint else 0)

def tsv_paths(base, task):
    if (base/task).exists(): return base/task/f"{task}_predictions.tsv"
    return base/f"{task}_predictions.tsv"

def jud_paths(base, task):
    for pat in [str(base/task/f"{task}*judgments.tsv"), str(base/f"{task}*judgments.tsv")]:
        g = sorted(glob.glob(pat))
        if g: return g[0]
    return None

SYS = {
 "gpt":    ["runs/gpt","runs/run2/gpt","runs/run3/gpt","runs/run4/gpt"],
 "claude": ["runs/claude","runs/run2/claude","runs/run3/claude","runs/run4/claude"],
 "gemini": ["runs_gemini/official","runs_gemini/rep1","runs_gemini/rep2","runs_gemini/rep3"],
 "glm":    [f"runs_extras/glm/pass{i}" for i in (1,2,3,4)],
 "grok":   [f"runs_extras/grok/pass{i}" for i in (1,2,3,4)],
 "rbio1":  [f"runs_rbio1/pass{i}" for i in (1,2,3,4)],
 "biomni-agent": [f"runs_biomni_agent/pass{i}" for i in (1,2,3,4)],
 "biomni-notools": ["runs_biomni_notools/official","runs_biomni_notools/rep1","runs_biomni_notools/rep2","runs_biomni_notools/rep3"],
}

FINAL={}
for mk, passes in SYS.items():
    A={k:[] for k in ["t1acc","t1bal","t1mf1","t2acc","t2bal","t2mf1","t2jp","t2jf","t3acc","t3bal","t3mf1","t3cp","t3jf"]}
    n_by_task={"task1":[], "task2":[], "task3":[]}
    for b in passes:
        bb=Path(b)
        p1=rd(tsv_paths(bb,"task1")); a,b,c=m1(p1)
        A["t1acc"].append(a); A["t1bal"].append(b); A["t1mf1"].append(c); n_by_task["task1"].append(len(p1))
        p2=rd(tsv_paths(bb,"task2")); j2p=jud_paths(bb,"task2"); j2=rd(j2p) if j2p else {}
        a,b,c,jp,jf=m2(p2,j2)
        A["t2acc"].append(a); A["t2bal"].append(b); A["t2mf1"].append(c); n_by_task["task2"].append(len(p2))
        if j2:  # 链/joint 只计已判卷的轮（未判轮不计为 0）
            A["t2jp"].append(jp); A["t2jf"].append(jf)
        p3=rd(tsv_paths(bb,"task3")); j3p=jud_paths(bb,"task3"); j3=rd(j3p) if j3p else {}
        a,b,c,jp,jf=m3(p3,j3)
        A["t3acc"].append(a); A["t3bal"].append(b); A["t3mf1"].append(c); n_by_task["task3"].append(len(p3))
        if j3:
            A["t3cp"].append(jp); A["t3jf"].append(jf)
    res={k: round(st.mean(v)*100,1) for k,v in A.items()}
    res["n_t1"], res["n_t2"], res["n_t3"] = len(n_by_task["task1"]), len(n_by_task["task2"]), len(n_by_task["task3"])
    FINAL[mk]=res

json.dump(FINAL, open('runs/MASTER_FINAL_STATS.json','w'), indent=1, ensure_ascii=False)
hdr = f"{'系统':<15}{'n':>2} | {'T1acc':>6} {'T1bal':>6} {'T1mF1':>6} | {'T2acc':>6} {'T2bal':>6} {'T2mF1':>6} {'T2jP':>6} {'T2jF1':>6} | {'T3acc':>6} {'T3bal':>6} {'T3mF1':>6} {'T3链':>6} {'T3jF1':>6}"
print(hdr); print("-"*len(hdr))
KEYS = [("t1acc","t1bal","t1mf1"), ("t2acc","t2bal","t2mf1","t2jp","t2jf"),
        ("t3acc","t3bal","t3mf1","t3cp","t3jf")]
for mk, v in FINAL.items():
    cells = [f"{v.get(k,0)*100 if v.get(k,0) is not None and v.get(k,0)<=1 else v.get(k,0):>6.1f}" for group in KEYS for k in group]
    print(f"{mk:<15}{v.get('n_t1',0):>2} | " + " | ".join(cells))
print("\nclaude T3 轮数:", FINAL['claude'].get('n_t3'), "(run3 task3 两次空输出，未计入 claude T3 均值)")
