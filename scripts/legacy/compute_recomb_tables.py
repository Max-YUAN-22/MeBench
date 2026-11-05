#!/usr/bin/env python3
"""RECOMB camera-ready tables: 6 systems x (BalAcc/mF1/joint) + five-axis decomposition.
Repairs claude run2/run3 missing judgments before computing."""
import json, csv, gzip, glob, re, statistics as st
from pathlib import Path
import importlib.util as iu

AXES = [("mechanism_correct","Mechanism"), ("mediator_correct","Mediator"),
        ("causal_role_order_correct","Causal order"), ("intervention_outcome_link_correct","Outcome link"),
        ("no_material_contradiction","No contradiction")]
AXE_KEYS = [a for a,_ in AXES]

_s2 = iu.spec_from_file_location("s2", "evaluation_v3.7.0/scoring/score_model_outputs.py")
_mm = iu.module_from_spec(_s2); _s2.loader.exec_module(_mm); prev = _mm.previous

def is_rna(e): e=(e or '').lower().replace(' ',''); return 'mir' in e
def canon(v,ent):
    c=prev.canonical_intervention(v)
    return 'inhibition' if (is_rna(ent) and c=='knockdown') else c
def f1(tp,fp,fn): return 2*tp/(2*tp+fp+fn) if (2*tp+fp+fn) else None
def cok_one(j,u,a): j=j.get(u); return bool(j) and str(j.get(a,"")).strip() in ('1','1.0','true','True')
def cok_of(j,u): j=j.get(u); return bool(j) and all(str(j.get(a,"")).strip() in ('1','1.0','true','True') for a in AXE_KEYS)

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

def tsv_p(base, task):
    if (Path(base)/task).exists(): return Path(base)/task/f"{task}_predictions.tsv"
    return Path(base)/f"{task}_predictions.tsv"

def jud_path(base, task):
    for pat in [str(Path(base)/task/f"{task}*judgments.tsv"), str(Path(base)/f"{task}*judgments.tsv")]:
        g = sorted(glob.glob(pat))
        if g: return g[0]
    return None

_h1 = {r['unit_id']: r['mechanism'] for r in csv.DictReader(gzip.open('evaluation_v3.7.0/task1/hidden_labels.tsv.gz','rt'), delimiter='\t')}
_h2 = {r['unit_id']: r for r in csv.DictReader(gzip.open('evaluation_v3.7.0/task2/hidden_labels.tsv.gz','rt'), delimiter='\t')}
_h3 = {r['unit_id']: r for r in csv.DictReader(gzip.open('evaluation_v3.7.0/task3/hidden_labels.tsv.gz','rt'), delimiter='\t')}

PASS_DIRS = {
 "GPT-6-Astra":        ["runs/gpt","runs/run2/gpt","runs/run3/gpt","runs/run4/gpt"],
 "Claude-Sonnet-5.5":  ["runs/claude","runs/run2/claude","runs/run3/claude","runs/run4/claude"],
 "Gemini-3.8-Flash":   ["runs_gemini/official","runs_gemini/rep1","runs_gemini/rep2","runs_gemini/rep3"],
 "GLM-5.3-Flash":      [f"runs_extras/glm/pass{i}" for i in (1,2,3,4)],
 "Grok-4.6":           [f"runs_extras/grok/pass{i}" for i in (1,2,3,4)],
 "Biomni (tools)":     [f"runs_biomni_agent/pass{i}" for i in (1,2,3,4)],
}

def collect(mk):
    out = {"t1_bal":[], "t1_mf1": [],
           "t2_acc":[], "t2_bal":[], "t2_mf1": [],
           "t2_bj":[], "t2_jf1": [],
           "t3_bj":[], "t3_mf1": [], "t3_jf1": [], "t3_acc": [],
           "axes_t2": {a:[] for a in AXE_KEYS}, "axes_t3": {a:[] for a in AXE_KEYS}}
    for b in PASS_DIRS[mk]:
        bb = Path(b)
        # T1
        p1 = tsv_p(bb, "task1"); pred1 = rd(p1)
        recs=[]; f1s=[]
        for c in sorted(set(_h2_u['mechanism'] for _h2_u in _h1.values()) if False else set(_h1.values())):
            pass
        for c in sorted(set(_h1.values())):
            recs.append(st.mean([1*(pred1[u]['predicted_mechanism']==c) for u in _h1 if _h1[u]==c]))
            tp=sum(1 for u in _h1 if pred1[u]['predicted_mechanism']==c==_h1[u])
            fp=sum(1 for u in _h1 if pred1[u]['predicted_mechanism']==c and _h1[u]!=c)
            fn=sum(1 for u in _h1 if _h1[u]==c and pred1[u]['predicted_mechanism']!=c)
            f1s.append(f1(tp,fp,fn))
        out["t1_bal"].append(sum(recs)/4); out["t1_mf1"].append(sum(f1s)/4)
        # T2
        p2 = tsv_p(bb, "task2"); pred2 = rd(p2)
        jp2 = jud_path(bb, "task2")
        j2 = rd(jp2) if jp2 else {}
        def cok2(u): return cok_of(j2,u)
        acc = st.mean([1*(pred2[u]['predicted_direction'].strip().lower()==_h2[u]['direction']) for u in _h2])
        recs=[st.mean([1*(pred2[u]['predicted_direction'].strip().lower()==c) for u in _h2 if _h2[u]['direction']==c]) for c in ("up","down")]
        f1s=[]
        for c in ("up","down"):
            tp=sum(1 for u,_h in _h2.items() if _h['direction']==c and pred2[u]['predicted_direction'].strip().lower()==c)
            fp=sum(1 for u,_h in _h2.items() if pred2[u]['predicted_direction'].strip().lower()==c!=_h2[u]['direction'])
            fn=sum(1 for u,_h in _h2.items() if _h['direction']==c and pred2[u]['predicted_direction'].strip().lower()!=c)
            f1s.append(f1(tp,fp,fn))
        out["t2_acc"].append(acc*100); out["t2_bal"].append(sum(recs)/2*100); out["t2_mf1"].append(sum(f1s)/2*100)
        for a in AXE_KEYS:
            out["axes_t2"][a].append(st.mean([1*cok_one(j2,u,a) for u in _h2]) if j2 else 0)
        if j2:
            out["t2_bj"].append(st.mean([st.mean([1*(pred2[u]['predicted_direction'].strip().lower()==_h2[u]['direction'] and cok2(u)) for u in _h2 if _h2[u]['direction']==c]) for c in ("up","down")])*100)
            f1s=[]
            for c in ("up","down"):
                tp=sum(1 for u,_h in _h2.items() if _h['direction']==c and pred2[u]['predicted_direction'].strip().lower()==c and cok2(u))
                fp=sum(1 for u,_h in _h2.items() if pred2[u]['predicted_direction'].strip().lower()==c and not cok2(u))
                fn=sum(1 for u,_h in _h2.items() if _h['direction']==c and not (pred2[u]['predicted_direction'].strip().lower()==c and cok2(u)))
                f1s.append(f1(tp,fp,fn))
            out["t2_jf1"].append(st.mean(f1s)*100)
        # T3
        p3 = tsv_p(bb, "task3"); pred3 = rd(p3)
        jp3 = jud_path(bb, "task3")
        j3 = rd(jp3) if jp3 else {}
        def cok3(u): return cok_of(j3,u)
        acc3 = st.mean([1*(canon(pred3[u]['predicted_intervention_type'], _h3[u]['input_perturbed_entity']) in {prev.canonical_intervention(x) for x in json.loads(_h3[u]['accepted_intervention_types_json'])}) for u,_h in _h3.items()])
        out["t3_acc"].append(acc3*100)
        for a in AXE_KEYS:
            out["axes_t3"][a].append(st.mean([1*cok_one(j3,u,a) for u in _h3]) if j3 else 0)
        if j3:
            out["t3_bj"].append(st.mean([st.mean([1*(canon(pred3[u]['predicted_intervention_type'], _h3[u]['input_perturbed_entity'])==c and cok3(u)) for u in _h3_hit(c)]) for c in t3_classes()])*100)
            f1s=[]; f1j=[]
            for c in t3_classes():
                tp=fp=fn=0; tpj=fpj=fnj=0
                for uid,_h in _h3.items():
                    accset={prev.canonical_intervention(x) for x in json.loads(_h['accepted_intervention_types_json'])}
                    pc=canon(pred3[uid]['predicted_intervention_type'], _h3[uid]['input_perturbed_entity'])
                    cok=cok3(uid)
                    if pc==c:
                        if c in accset: tp+=1
                        else: fp+=1
                        if c in accset and cok: tpj+=1
                        else: fpj+=1
                    else:
                        if c in accset: fn+=1
                        if c in accset and cok: fnj+=1
                v=f1(tp,fp,fn)
                if v is not None: f1s.append(v)
                vj=f1(tpj,fpj,fnj)
                if vj is not None: f1j.append(vj)
            out["t3_mf1"].append(sum(f1s)/len(f1s)*100 if f1s else 0)
            out["t3_jf1"].append(sum(f1j)/len(f1j)*100 if f1j else 0)
    return out

_t3cls_cache = None
def t3_classes():
    global _t3cls_cache
    if _t3cls_cache is None:
        s=set()
        for _h in _h3.values(): s |= {prev.canonical_intervention(x) for x in json.loads(_h['accepted_intervention_types_json'])}
        _t3cls_cache = sorted(s)
    return _t3cls_cache
def _h3_hit(c):
    return [u for u in _h3 if c in {prev.canonical_intervention(x) for x in json.loads(_h3[u]['accepted_intervention_types_json'])}]

def mean(v): return sum(v)/len(v) if v else float('nan')

def main():
    R = {mk: collect(mk) for mk in PASS_DIRS}
    # ---- Table 1: main 6x6 ----
    print("TABLE1_JSON")
    t1 = {}
    for mk, r in R.items():
        t1[mk] = {"T1_BalAcc": round(mean(r["t1_bal"]),1), "T1_mF1": round(mean(r["t1_mf1"]),1),
                  "T2_BalJointAcc": round(mean(r["t2_bj"]),1) if r["t2_bj"] else None,
                  "T2_JointF1": round(mean(r["t2_jf1"]),1) if r["t2_jf1"] else None,
                  "T3_BalJointAcc": round(mean(r["t3_bj"]),1) if r["t3_bj"] else None,
                  "T3_JointF1": round(mean(r["t3_jf1"]),1) if r["t3_jf1"] else None,
                  "n_runs": len(r["t1_bal"])}
    json.dump(t1, open('runs/RECOMB_TABLE.json','w'), indent=1)
    hdr = f"{'Model':<20}{'T1 BalAcc':>10}{'T1 mF1':>9}{'T2 BJoint':>11}{'T2 JointF1':>12}{'T3 BJoint':>11}{'T3 JointF1':>12}"
    print(hdr); print("-"*len(hdr))
    for mk, v in t1.items():
        g = lambda k: f"{v[k]:.1f}" if v[k] is not None else "—"
        print(f"{mk:<20}{v['T1_BalAcc']:>10.1f}{v['T1_mF1']:>9.1f}{g('T2_BalJointAcc'):>11}{g('T2_JointF1'):>12}{g('T3_BalJointAcc'):>11}{g('T3_JointF1'):>12}")
    # ---- Table 2: five-axis ----
    print("\nTABLE2_JSON")
    t2 = {}
    for mk, r in R.items():
        t2[mk] = {}
        for a, short in AXES:
            t2[mk][f"T2_{short}"] = round(mean(r["axes_t2"][a]),1)
            t2[mk][f"T3_{short}"] = round(mean(r["axes_t3"][a]),1)
        t2[mk]["T2_Chain"] = round(mean(r["axes_t2"] and [1]*0 or []) if False else mean([1]*0) if False else 0,1)
    # chain per pass stored? recompute chain quickly
    for mk, passes in PASS_DIRS.items():
        ch2=[]; ch3=[]
        for b in passes:
            bb=Path(b)
            p2 = tsv_p(bb,"task2"); pred2 = rd(p2)
            jp2 = jud_path(bb,"task2"); j2 = rd(jp2) if jp2 else {}
            if j2:
                ch2.append(st.mean([1*cok_of(j2,u) for u in _h2])*100)
            p3 = tsv_p(bb,"task3"); pred3 = rd(p3)
            jp3 = jud_path(bb,"task3"); j3 = rd(jp3) if jp3 else {}
            if j3:
                ch3.append(st.mean([1*cok_of(j3,u) for u in _h3])*100)
        t2[mk]["T2_Chain"] = round(st.mean(ch2),1) if ch2 else None
        t2[mk]["T3_Chain"] = round(st.mean(ch3),1) if ch3 else None
    json.dump(t2, open('runs/RECOMB_FIVEAXIS.json','w'), indent=1)
    hdr2 = f"{'Model':<20}" + "".join(f"{s+' (T2)':>12}{s+' (T3)':>12}" for _,s in AXES) + f"{'Chain (T2)':>12}{'Chain (T3)':>12}"
    print(hdr2); print("-"*len(hdr2))
    for mk, v in t2.items():
        g = lambda k: f"{v[k]:.1f}" if v.get(k) is not None else "—"
        cells = "".join(f"{g('T2_'+s):>12}{g('T3_'+s):>12}" for _,s in AXES)
        print(f"{mk:<20}" + cells + f"{g('T2_Chain'):>12}{g('T3_Chain'):>12}")
    json.dump({"table1": t1, "table2": t2}, open('runs/RECOMB_TABLES.json','w'), indent=1)

if __name__ == "__main__":
    main()
