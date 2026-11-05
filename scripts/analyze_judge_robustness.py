import json,csv,collections,hashlib,shutil,math
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Recompute judge sensitivity from archived independent judgments; does not invoke a new judge.')
parser.add_argument('--archive',type=Path,default=Path(__file__).resolve().parents[1]/'analysis/robustness')
parser.add_argument('--output',type=Path,default=Path('judge_metrics_output'))
args=parser.parse_args();W=args.archive;O=args.output;O.mkdir(parents=True,exist_ok=True)
AX=['mechanism_correct','mediator_correct','causal_role_order_correct','intervention_outcome_link_correct','no_material_contradiction'];M=json.load(open(W/'judge_sample_mapping.json'));mapping={r['case_id']:r for r in M};new={}
for b in range(1,7):
 p=W/f'judge_raw_batch_{b}.json';rows=json.load(open(p));assert len(rows)==20
 for r in rows:
  assert r['case_id'] not in new and r['case_id'] in mapping
  assert all(type(r[a]) is int and r[a] in [0,1] for a in AX),r
  assert r.get('adjudicator_notes','').strip()
  new[r['case_id']]=r
assert set(new)==set(mapping)
R=[]
for m in M:
 n=new[m['case_id']];r={k:m[k] for k in ['case_id','task','system','run','unit_id','pair_id','stratum','weight']};r['old_chain']=m['old_chain'];r['new_chain']=int(all(n[a] for a in AX));r['adjudicator_notes']=n['adjudicator_notes']
 for a in AX:r['old_'+a]=m['old_axes'][a];r['new_'+a]=n[a]
 R.append(r)
def write(name,rows):
 with open(O/name,'w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
write('judge_reassessment_by_record.tsv',R)
def agreement(rows,axes,weighted):
 c=collections.defaultdict(float)
 for r in rows:
  for a in axes:c[(r['old_'+a],r['new_'+a])]+=r['weight'] if weighted else 1
 N=sum(c.values());po=(c[(0,0)]+c[(1,1)])/N;pold=(c[(1,0)]+c[(1,1)])/N;pnew=(c[(0,1)]+c[(1,1)])/N;pe=pold*pnew+(1-pold)*(1-pnew)
 return dict(agreement=po,kappa=(po-pe)/(1-pe) if abs(1-pe)>1e-12 else None,old_pass_rate=pold,new_pass_rate=pnew,pass_rate_delta=pnew-pold,weight_sum=N,old0_new0=c[(0,0)],old0_new1=c[(0,1)],old1_new0=c[(1,0)],old1_new1=c[(1,1)])
metrics=[];systems=[];stability=[]
for task in (2,3):
 rows=[r for r in R if r['task']==task]
 for axis in AX+['chain','pooled_axes']:
  for weighted in [False,True]:metrics.append(dict(task=task,axis=axis,weighted=weighted,n_cases=len(rows),**agreement(rows,AX if axis=='pooled_axes' else [axis],weighted)))
 # Check calibrated full-chain prevalence against all released records.
 pop=list(csv.DictReader(open(Path(__file__).resolve().parents[1]/f'runs/MASTER_task{task}.tsv'),delimiter='\t'))
 for s in dict.fromkeys(r['system'] for r in rows):
  rs=[r for r in rows if r['system']==s];g=agreement(rs,['chain'],True);known=sum(int(r['chain_pass']) for r in pop if r['system']==s)/sum(r['system']==s for r in pop);assert abs(known-g['old_pass_rate'])<1e-12
  systems.append(dict(task=task,system=s,n=len(rs),**g))
 vals=[r for r in systems if r['task']==task]
 def ranks(key):
  vs=[r[key] for r in vals];return [1+sum(v>x+1e-12 for v in vs)+.5*(sum(abs(v-x)<=1e-12 for v in vs)-1) for x in vs]
 ro,rn=ranks('old_pass_rate'),ranks('new_pass_rate')
 def corr(a,b):
  aa=[x-sum(a)/len(a) for x in a];bb=[x-sum(b)/len(b) for x in b];den=math.sqrt(sum(x*x for x in aa)*sum(x*x for x in bb));return sum(x*y for x,y in zip(aa,bb))/den if den else None
 for r,o,n in zip(vals,ro,rn):r['old_rank']=o;r['new_rank']=n
 stability.append(dict(task=task,metric='full_chain_pass_rate',Spearman=corr(ro,rn),old_order=[r['system'] for r in sorted(vals,key=lambda x:-x['old_pass_rate'])],new_point_order=[r['system'] for r in sorted(vals,key=lambda x:-x['new_pass_rate'])],interpretation='Exploratory IPW point rankings from only ten cases per system/task; not validated full-dataset reranking.'))
write('judge_agreement_metrics.tsv',metrics);write('judge_system_pass_rate_changes.tsv',systems)
protocol=json.load(open(W/'judge_protocol.json'));protocol.update(status='completed',completed_cases=len(new),judgment_batches=6,execution_date_client='2026-11-05',rubric_sha256=hashlib.sha256((W/'judge_rubric.md').read_bytes()).hexdigest());(O/'judge_protocol.json').write_text(json.dumps(protocol,indent=2))
# Publish the complete blinded packet and verbatim independent judgments after evaluation.
shutil.copy2(W/'judge_blinded_cases.jsonl',O/'judge_blinded_cases.jsonl');shutil.copy2(W/'judge_rubric.md',O/'judge_rubric.md')
for b in range(1,7):shutil.copy2(W/f'judge_raw_batch_{b}.json',O/f'judge_raw_batch_{b}.json')
result=dict(protocol=protocol,metrics=metrics,system_changes=systems,ranking_stability=stability);(O/'judge_robustness_analysis.json').write_text(json.dumps(result,indent=2))
print(json.dumps(dict(primary=[r for r in metrics if r['weighted'] and r['axis'] in ['chain','pooled_axes']],system_changes=systems,rank_stability=stability),indent=2))
