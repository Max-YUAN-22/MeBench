#!/usr/bin/env python3
"""Five-axis per-system pass rates for T2/T3 + chain + joint (judged passes only)."""
import json, csv, gzip, glob, re, statistics as st
from pathlib import Path
import importlib.util as iu

AXES = [("mechanism_correct","mech"), ("mediator_correct","med"),
        ("causal_role_order_correct","ord"), ("intervention_outcome_link_correct","lnk"),
        ("no_material_contradiction","con")]
AXE_KEYS = [a for a,_ in AXES]

s2 = iu.spec_from_file_location("s2", "evaluation_v3.7.0/scoring/score_model_outputs.py")
mm = iu.module_from_spec(s2); s2.loader.exec_module(mm); prev = mm.previous
def is_rna(e): e=(e or '').lower().replace(' ',''); return 'mir' in e
def canon(v,ent):
    c=prev.canonical_intervention(v)
    return 'inhibition' if (is_rna(ent) and c=='knockdown') else c

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

def cok_all(j,u): j=j.get(u); return bool(j) and all(str(j.get(a,"")).strip() in ('1','1.0','true','True') for a in AXE_KEYS)
def cok_one(j,u,a): j=j.get(u); return bool(j) and str(j.get(a,"")).strip() in ('1','1.0','true','True')

h2 = {r['unit_id']: r for r in csv.DictReader(gzip.open('evaluation_v3.7.0/task2/hidden_labels.tsv.gz','rt'), delimiter='\t')}
h3 = {r['unit_id']: r for r in csv.DictReader(gzip.open('evaluation_v3.7.0/task3/hidden_labels.tsv.gz','rt'), delimiter='\t')}

def tsv_p(base, task):
    if (base/task).exists(): return base/task/f"{task}_predictions.tsv"
    return base/f"{task}_predictions.tsv"

def jud_p(base, task):
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
 "rbio1":  [f"runs_rbio1/pass{i}" for i in (1,2,3)],
 "biomni-agent": [f"runs_biomni_agent/pass{i}" for i in (1,2,3,4)],
 "biomni-notools": ["runs_biomni_notools/official","runs_biomni_notools/rep1","runs_biomni_notools/rep2","runs_biomni_notools/rep3"],
}
KEYS = ([f"t2_{s}" for _,s in AXES] + ["t2_chain","t2_jointp"] +
        [f"t3_{s}" for _,s in AXES] + ["t3_chain","t3_jointp","t3_acc"])

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
import time  # noqa: E402

def main():
    OUT = {}
    for mk, passes in SYS.items():
        A = {k: [] for k in KEYS}
        n2 = n3 = 0
        for b in passes:
            bb = Path(b)
            for task, J, H, P, pre in (("task2","j2",h2,"t2","task2_predictions.tsv"),
                                        ("task3","j3",h3,"t3","task3_predictions.tsv"),) if False else [
                ("task2","j2",h2,"t2","task2_predictions.tsv"),
                ("task3","j3",h3,"t3","task3_predictions.tsv")]:
                pre = "t2" if task == "task2" else "t3"
                jp = jud_p(bb, task)
                if not jp: continue
                pp = tsv_p(bb, task)
                if not Path(pp).exists(): continue
                pred = rd(pp); judg = rd(jp)
                for a, short in AXES:
                    A[f"{pre}_{short}"].append(st.mean([1*cok_one(judg,u,a) for u in H]))
                A[f"{pre}_chain"].append(st.mean([1*cok_all(judg,u) for u in H]))
                if task == "task2":
                    A["t2_jointp"].append(st.mean([1*(pred[u]['predicted_direction'].strip().lower()==h2[u]['direction'] and cok_all(judg,u)) for u in h2]))
                    n2 += 1
                else:
                    A["t3_jointp"].append(st.mean([1*(prev.canonical_intervention(pred[u]['predicted_intervention_type']) in {prev.canonical_intervention(x) for x in json.loads(h3[u]['accepted_intervention_types_json'])} and cok_all(judg,u)) for u in h3]))
                    A["t3_acc"].append(st.mean([1*(prev.canonical_intervention(pred[u]['predicted_intervention_type']) in {prev.canonical_intervention(x) for x in json.loads(h3[u]['accepted_intervention_types_json'])}) for u in h3]))
                    n3 += 1
        OUT[mk] = {k: round(st.mean(v)*100,1) for k,v in A.items() if v}
        OUT[mk]["n_t2"], OUT[mk]["n_t3"] = n2, n3
        log(f"{mk}: done")
    json.dump(OUT, open('runs/FIVE_AXIS_STATS.json','w'), indent=1)
    cols = ([f"t2_{s}" for _,s in AXES] + ["t2_chain","t2_jointp"] +
            [f"t3_{s}" for _,s in AXES] + ["t3_chain","t3_jointp","t3_acc"])
    hdr = f"{'系统':<15}{'判卷轮':>4} | " + " | ".join(f"{c:>6}" for c in cols)
    print(hdr); print("-"*len(hdr))
    for mk, v in OUT.items():
        cells = [f"{v.get(c,0):.1f}" for c in cols]
        print(f"{mk:<15}{v['n_t2']:>4} | " + " | ".join(cells))
    print("\n列说明: T2/T3 各五轴(机制/中介/顺序/连接/矛盾)通过率 → Chain=五轴全过率 → T2jP=方向对且链过 | T3jP=类型接受且链过 | T3acc=类型接受率")

if __name__ == "__main__":
    main()
