import csv,json,collections,statistics,pathlib,importlib.util,re
import argparse
parser=argparse.ArgumentParser(description='Audit archived predictions and judges and recompute the six-system release.')
parser.add_argument('--output',type=pathlib.Path,default=pathlib.Path('audit_output'))
args=parser.parse_args()
R=pathlib.Path(__file__).resolve().parents[1]; O=args.output; O.mkdir(parents=True,exist_ok=True)
AX=['mechanism_correct','mediator_correct','causal_role_order_correct','intervention_outcome_link_correct','no_material_contradiction']
def read(p):
 return list(csv.DictReader(open(p),delimiter='\t'))
D={t:read(R/f'runs/MASTER_task{t}.tsv') for t in (1,2,3)}
systems=list(dict.fromkeys(r['system'] for r in D[1]))
errors=[]
for t,rows in D.items():
 assert len(rows)=={1:4104,2:4632,3:480}[t]
 assert len({(r['system'],r['run'],r['unit_id']) for r in rows})==len(rows)
 if t>1:
  for r in rows:
   assert int(r['chain_pass'])==int(all(r[a]=='1' for a in AX))
   assert int(r['joint_pass'])==int(r['chain_pass'])*int(r['dir_correct' if t==2 else 'type_accepted'])
# Verify all master predictions/axes against archived per-run records, handling wrapped prose.
def rd(p):
 lines=p.read_text().splitlines(); head=lines[0].split('\t'); out={}
 for line in lines[1:]:
  v=line.split('\t')
  if v[0].startswith(('T1U_','T2U_','T3VP_')): out[v[0]]=dict(zip(head,v))
 return out
names=dict(zip(systems,['gpt','claude','gemini','glm','grok','biomni_agent']))
verified=0
for s in systems:
 for n in range(1,5):
  sub=('run'+str(n)) if names[s] in ('gpt','claude') else (('official' if n==1 else 'rep'+str(n)) if names[s]=='gemini' else 'pass'+str(n))
  b=R/'runs'/names[s]/sub
  for t in (1,2,3):
   bp=b/f'task{t}' if (b/f'task{t}').is_dir() else b
   pred=rd(bp/f'task{t}_predictions.tsv')
   jp=sorted(bp.glob(f'task{t}*judgments.tsv'))
   jud=rd(jp[0]) if jp else {}
   key={1:'predicted_mechanism',2:'predicted_direction',3:'predicted_intervention_type'}[t]
   for r in [r for r in D[t] if r['system']==s and int(r['run'])==n]:
    u=r['unit_id']
    if r[key]!=pred[u].get(key): errors.append([s,n,t,u,key])
    if t>1:
     for a in AX:
      if str(r[a])!=str(jud.get(u,{}).get(a)): errors.append([s,n,t,u,a])
    verified+=1
assert not errors,errors[:10]
def writecsv(name,rows):
 with open(O/name,'w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
def pct(rows,k):return 100*sum(int(r[k]) for r in rows)/len(rows)
summary=[]
for t in (2,3):
 for s in systems:
  rows=[r for r in D[t] if r['system']==s]; c='dir_correct' if t==2 else 'type_accepted'; good=[r for r in rows if r[c]=='1']
  summary.append(dict(task=t,system=s,n=len(rows),answer=pct(rows,c),chain=pct(rows,'chain_pass'),joint=pct(rows,'joint_pass'),correct_answer_chain_fail=sum(r['chain_pass']=='0' for r in good),correct_answer_n=len(good),conditional_fail=100*sum(r['chain_pass']=='0' for r in good)/len(good),**{a:pct(rows,a) for a in AX}))
writecsv('diagnostic_metrics.tsv',summary)
strata=[]
for t in (2,3):
 for m in dict.fromkeys(r['gold_mechanism'] for r in D[t]):
  rows=[r for r in D[t] if r['gold_mechanism']==m]; good=[r for r in rows if r['dir_correct' if t==2 else 'type_accepted']=='1']
  strata.append(dict(task=t,mechanism=m,pairs=len({r['pair_id'] for r in rows}),units=len({r['unit_id'] for r in rows}),judgments=len(rows),chain_fail=sum(r['chain_pass']=='0' for r in rows),mediator_pass=pct(rows,'mediator_correct'),causal_pass=pct(rows,'causal_role_order_correct'),mediator_pass_causal_fail=sum(r['mediator_correct']=='1' and r['causal_role_order_correct']=='0' for r in rows),answer_correct_chain_fail=sum(r['chain_pass']=='0' for r in good),answer_correct=len(good)))
writecsv('mechanism_strata.tsv',strata)
modules=[]
for label,term in [('PPARA--BHLHE40','BHLHE40'),('SRCAP/H2A.Z','SRCAP'),('GATA1--TAL1','TAL1'),('TP63--FOXK1','FOXK1')]:
 rows=[r for r in D[2] if term.lower() in r['gold_mediator'].lower()]
 modules.append(dict(module=label,pairs=len({r['pair_id'] for r in rows}),units=len({r['unit_id'] for r in rows}),judgments=len(rows),causal_fail=sum(r[AX[2]]=='0' for r in rows),chain_fail=sum(r['chain_pass']=='0' for r in rows),mediator_pass_causal_fail=sum(r[AX[1]]=='1' and r[AX[2]]=='0' for r in rows)))
writecsv('module_failures.tsv',modules)
sens=[]
for s in systems:
 rows=[r for r in D[2] if r['system']==s]; clean=[r for r in rows if r['unit_id'] not in ['T2U_0013','T2U_0014','T2U_0015']]
 bypair=collections.defaultdict(list)
 for r in rows:bypair[r['pair_id']].append(r)
 sens.append(dict(system=s,original_chain=pct(rows,'chain_pass'),exclude_ESR1_chain=pct(clean,'chain_pass'),pair_weighted_chain=statistics.mean(pct(v,'chain_pass') for v in bypair.values())))
writecsv('sensitivity.tsv',sens)
json.dump(dict(master_rows_verified_against_archived_predictions_and_axes=verified,errors=errors,summary=summary,strata=strata,modules=modules,sensitivity=sens),open(O/'independent_audit.json','w'),indent=2)
print(json.dumps({'verified':verified,'modules':modules,'summary':[{k:v for k,v in x.items() if k in ('task','system','answer','chain','joint','conditional_fail')} for x in summary]},indent=2))
spec=importlib.util.spec_from_file_location('sc',R/'benchmark/scoring/score_model_outputs.py')
sc=importlib.util.module_from_spec(spec);spec.loader.exec_module(sc)
canon=sc.previous.canonical_intervention
for r in D[3]:
 r['gold_accepted_types']=';'.join(canon(x) for x in r['gold_accepted_types'].split(';'))
# Recompute all 36 main-table cells, retaining the published joint-F1 convention.
main=[]; diffs=[]
def avg(xs):return sum(xs)/len(xs)
def f1(tp,fp,fn):return 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0
pub=json.load(open(R/'results/main_results.json'))
for s in systems:
 vals=collections.defaultdict(list)
 for run in range(1,5):
  for t in (1,2,3):
   rows=[r for r in D[t] if r['system']==s and int(r['run'])==run]
   gold='gold_mechanism' if t==1 else ('expected_direction' if t==2 else 'gold_accepted_types')
   pk={1:'predicted_mechanism',2:'predicted_direction',3:'predicted_type_canonical'}[t]
   cls=sorted({c for r in rows for c in (r[gold].split('|') if t==3 else [r[gold]])})
   if t==3:
    # This master uses semicolon-joined accepted sets; inspect separator from actual annotations.
    cls=sorted({c for r in rows for c in re.split(r'[|;]',r[gold])})
   rec=[]; fs=[]
   for c in cls:
    z=lambda r:c in re.split(r'[|;]',r[gold]) if t==3 else r[gold]==c
    p=lambda r:r[pk].strip().lower()==c.lower()
    chain=lambda r:True if t==1 else r['chain_pass']=='1'
    rec.append(sum(z(r) and p(r) and chain(r) for r in rows)/sum(z(r) for r in rows))
    tp=sum(z(r) and p(r) and chain(r) for r in rows)
    fp=sum(p(r) and ((not z(r)) if t==1 else ((not chain(r)) if t==2 else (not(z(r) and chain(r))))) for r in rows)
    fn=sum((z(r) and not p(r)) if t==1 else ((z(r) and not(p(r) and chain(r))) if t==2 else (z(r) and chain(r) and not p(r))) for r in rows)
    
    if t!=3 or 2*tp+fp+fn: fs.append(f1(tp,fp,fn))
   vals[f'T{t}_'+('BalAcc' if t==1 else 'BalJointAcc')].append(avg(rec)*100)
   vals[f'T{t}_'+('mF1' if t==1 else 'JointF1')].append(avg(fs)*100)
 row={'system':s,**{k:avg(v) for k,v in vals.items()}}
 main.append(row)
 p=pub['Biomni (tools)' if s=='Biomni' else s]
 for k,v in row.items():
  if k!='system' and abs(v-p[k])>0.11:diffs.append(dict(system=s,metric=k,recomputed=v,published=p[k]))
writecsv('main_table_recomputed.tsv',main)
json.dump(diffs,open(O/'main_table_discrepancies.json','w'),indent=2)
print('Main-table discrepancies:',diffs)

assert not diffs, "Main-table discrepancies found; inspect main_table_discrepancies.json"
