#!/usr/bin/env python3
"""AUDIT step 1 — canonical recomputation of every metric from raw files.

Uses the exact published aggregation functions (m1/m2/m3 imported from
compute_final_stats.py) plus pooled five-axis rates, for every system x task x
run. Writes runs/AUDIT_per_run_full.json. No other source is trusted.
"""
import os, io, json, csv, gzip, glob, re, statistics as st, contextlib
from pathlib import Path

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

# import published helpers
ns = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('compute_final_stats.py', encoding='utf-8').read(), ns)
m1, m2, m3, rd = ns['m1'], ns['m2'], ns['m3'], ns['rd']
tsv_paths, jud_paths = ns['tsv_paths'], ns['jud_paths']
AXES = ns['AXES']
cok_of = ns['cok_of']
_h2, _h3 = ns['_h2'], ns['_h3']

AXE_KEYS = ["mechanism_correct","mediator_correct","causal_role_order_correct",
            "intervention_outcome_link_correct","no_material_contradiction"]

SYSTEMS = {
 "gpt":            ["runs/gpt","runs/run2/gpt","runs/run3/gpt","runs/run4/gpt"],
 "claude":         ["runs/claude","runs/run2/claude","runs/run3/claude","runs/run4/claude"],
 "gemini":         ["runs_gemini/official","runs_gemini/rep1","runs_gemini/rep2","runs_gemini/rep3"],
 "glm":            [f"runs_extras/glm/pass{i}" for i in (1,2,3,4)],
 "grok":           [f"runs_extras/grok/pass{i}" for i in (1,2,3,4)],
 "rbio1":          [f"runs_rbio1/pass{i}" for i in (1,2,3,4)],
 "biomni-agent":   [f"runs_biomni_agent/pass{i}" for i in (1,2,3,4)],
 "biomni-notools": ["runs_biomni_notools/official","runs_biomni_notools/rep1","runs_biomni_notools/rep2","runs_biomni_notools/rep3"],
}

RESULT = {}
for mk, passes in SYSTEMS.items():
    rec = {"runs": []}
    axes_t2 = {a: [0, 0] for a in AXE_KEYS}   # pooled [pass, judged]
    axes_t3 = {a: [0, 0] for a in AXE_KEYS}
    for i, b in enumerate(passes, 1):
        bb = Path(b)
        r = {"run": i, "dir": b}
        # T1
        p1 = rd(tsv_paths(bb, "task1")); a, bal, mf = m1(p1)
        r["t1"] = {"acc": round(a*100,1), "bal": round(bal*100,1), "mf1": round(mf*100,1), "n": len(p1)}
        # T2
        p2 = rd(tsv_paths(bb, "task2")); j2p = jud_paths(bb, "task2"); j2 = rd(j2p) if j2p else {}
        a2, b2, c2, jp2, jf2 = m2(p2, j2)
        r["t2"] = {"dir_acc": round(a2*100,1), "dir_bal": round(b2*100,1), "dir_mf1": round(c2*100,1),
                   "judged": bool(j2), "n_judged_rows": len(j2)}
        if j2:
            r["t2"]["chain_pass"] = round(st.mean([1*cok_of(j2,u) for u in _h2])*100,1)
            r["t2"]["joint_pass"] = round(jp2*100,1)
            r["t2"]["joint_f1"] = round(jf2*100,1)
            # balanced joint (same as compute_recomb_tables t2_bj)
            bj = st.mean([st.mean([1*(p2[u]['predicted_direction'].strip().lower()==_h2[u]['direction'] and cok_of(j2,u)) for u in _h2 if _h2[u]['direction']==c]) for c in ("up","down")])
            r["t2"]["bal_joint"] = round(bj*100,1)
            for a_ in AXE_KEYS:
                axes_t2[a_][0] += sum(1 for u in _h2 if str(j2.get(u,{}).get(a_,"")).strip() in ('1','1.0','true','True'))
                axes_t2[a_][1] += len(j2)
        # T3
        p3 = rd(tsv_paths(bb, "task3")); j3p = jud_paths(bb, "task3"); j3 = rd(j3p) if j3p else {}
        a3, b3, c3, jp3, jf3 = m3(p3, j3)
        r["t3"] = {"type_acc": round(a3*100,1), "type_bal": round(b3*100,1), "type_mf1": round(c3*100,1),
                   "judged": bool(j3), "n_judged_rows": len(j3)}
        if j3:
            r["t3"]["chain_pass"] = round(jp3*100,1)   # m3's 4th return = chain pass
            r["t3"]["joint_f1"] = round(jf3*100,1)
            for a_ in AXE_KEYS:
                axes_t3[a_][0] += sum(1 for u in _h3 if str(j3.get(u,{}).get(a_,"")).strip() in ('1','1.0','true','True'))
                axes_t3[a_][1] += len(j3)
        rec["runs"].append(r)
    # aggregates (published convention: chain metrics only over judged runs)
    agg = {}
    for met in ("acc","bal","mf1"): agg[f"t1_{met}"] = round(st.mean([r["t1"][met] for r in rec["runs"]]),1)
    for met in ("dir_acc","dir_bal","dir_mf1"): agg[f"t2_{met}"] = round(st.mean([r["t2"][met] for r in rec["runs"]]),1)
    for met in ("type_acc","type_bal","type_mf1"): agg[f"t3_{met}"] = round(st.mean([r["t3"][met] for r in rec["runs"]]),1)
    j2r = [r["t2"] for r in rec["runs"] if r["t2"]["judged"]]
    j3r = [r["t3"] for r in rec["runs"] if r["t3"]["judged"]]
    agg["t2_n_judged"] = len(j2r)
    agg["t3_n_judged"] = len(j3r)
    for met in ("chain_pass","joint_pass","joint_f1","bal_joint"):
        if j2r and met in j2r[0]:
            agg[f"t2_{met}"] = round(st.mean([r[met] for r in j2r]),1)
    for met in ("chain_pass","joint_f1"):
        if j3r and met in j3r[0]:
            agg[f"t3_{met}"] = round(st.mean([r[met] for r in j3r]),1)
    agg["axes_t2"] = {a: round(p/t*100,1) if t else None for a,(p,t) in axes_t2.items()}
    agg["axes_t3"] = {a: round(p/t*100,1) if t else None for a,(p,t) in axes_t3.items()}
    rec["aggregate"] = agg
    RESULT[mk] = rec

json.dump(RESULT, open('runs/AUDIT_per_run_full.json','w'), indent=1)

# -------- print master tables --------
KEYMAP = {"mechanism_correct":"mech","mediator_correct":"med","causal_role_order_correct":"causal_order",
          "intervention_outcome_link_correct":"outcome","no_material_contradiction":"no_contra"}
print("="*100)
print("MASTER AUDIT — aggregate (published conventions; chain over judged runs only)")
print("="*100)
hdr = f"{'sys':<15}|{'T1 acc':>7}{'bal':>6}{'mF1':>6}|{'T2 dir':>7}{'chain':>7}{'jP':>6}{'jF1':>6}{'n':>3}|{'T3 type':>8}{'chain':>7}{'jF1':>6}{'n':>3}"
print(hdr); print("-"*len(hdr))
for mk, rec in RESULT.items():
    a = rec["aggregate"]
    print(f"{mk:<15}|{a['t1_acc']:>7}{a['t1_bal']:>6}{a['t1_mf1']:>6}|"
          f"{a['t2_dir_acc']:>7}{a.get('t2_chain_pass','-'):>7}{a.get('t2_joint_pass','-'):>6}{a.get('t2_joint_f1','-'):>6}{a['t2_n_judged']:>3}|"
          f"{a['t3_type_acc']:>8}{a.get('t3_chain_pass','-'):>7}{a.get('t3_joint_f1','-'):>6}{a['t3_n_judged']:>3}")
print()
print("Five-axis pooled pass rates (T2 / T3), judged runs only:")
for mk, rec in RESULT.items():
    a = rec["aggregate"]
    def fmt(ax):
        return " ".join(f"{KEYMAP[k]}={v:.1f}" if v is not None else f"{KEYMAP[k]}=NA" for k,v in ax.items())
    print(f"  {mk:<15} T2: {fmt(a['axes_t2'])}")
    print(f"  {'':<15} T3: {fmt(a['axes_t3'])}")
