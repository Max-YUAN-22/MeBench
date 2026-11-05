import csv,gzip,json,re,collections
from pathlib import Path
import numpy as np
import argparse
parser=argparse.ArgumentParser(description='Recompute paired Task 2 cluster bootstrap intervals and rankings.')
parser.add_argument('--output',type=Path,default=Path('robustness_output'))
args=parser.parse_args()
R=Path(__file__).resolve().parents[1];O=args.output;O.mkdir(parents=True,exist_ok=True)
B=20000;SEED=20261105
D=list(csv.DictReader(open(R/'runs/MASTER_task2.tsv'),delimiter='\t'));S=list(dict.fromkeys(r['system'] for r in D));P=sorted({r['pair_id'] for r in D});assert len(P)==168
# Resolve DOI/PMCID aliases for each primary paper, then merge shared source papers and pairs.
with gzip.open(R/'benchmark/task2/evaluator_metadata.tsv.gz','rt') as f:M=list(csv.DictReader(f,delimiter='\t'))
parent={}
def find(x):
 parent.setdefault(x,x)
 if parent[x]!=x:parent[x]=find(parent[x])
 return parent[x]
def union(a,b):parent[find(b)]=find(a)
byunit={};by_pair=collections.defaultdict(set)
for r in M:
 records=[]
 for x in json.loads(r['sources_json']):
  ids=[];pmc=re.search(r'PMC\d+',x.get('source_url',''));doi=re.search(r'10\.\d{4,9}/[^;\s]+',x.get('citation_or_accession',''))
  if pmc:ids.append('pmc:'+pmc.group())
  if doi:ids.append('doi:'+doi.group().lower().rstrip('.,'))
  assert ids,(r['unit_id'],x)
  for i in ids:find(i);union(ids[0],i)
  records.append(ids)
 byunit[r['unit_id']]=records
 # Do not merge different primary studies until aliases are resolved.
resolved_papers=len({find(x) for x in parent})
for r in M:
 ids=[x for rec in byunit[r['unit_id']] for x in rec];by_pair[r['pair_id']].update(ids)
for pair,ids in by_pair.items():
 ids=sorted(ids)
 for i in ids:union(ids[0],i)
components=collections.defaultdict(list)
for pair,ids in by_pair.items():components[find(sorted(ids)[0])].append(pair)
component_pairs=[sorted(x) for x in components.values()];component_pairs.sort(key=lambda x:x[0]);pair_component={p:f'SC{i+1:02d}' for i,g in enumerate(component_pairs) for p in g}
source_rows=[]
for i,pairs in enumerate(component_pairs):
 rows=[r for r in M if r['pair_id'] in pairs];ids=sorted({x for p in pairs for x in by_pair[p]})
 source_rows.append(dict(component=f'SC{i+1:02d}',pairs=len(pairs),units=len(rows),source_identifiers=';'.join(ids),pair_ids=';'.join(pairs)))
def write(name,rows):
 with open(O/name,'w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
write('study_components.tsv',source_rows)
results={};cirows=[];rankrows=[];diffrows=[]
for kind,clusters in [('pair',[[p] for p in P]),('study_component',component_pairs)]:
 n=len(clusters);den=np.zeros(n);up=np.zeros(n);down=np.zeros(n);num={k:np.zeros((n,len(S))) for k in ['answer','chain','joint','joint_up','joint_down']}
 for i,pairs in enumerate(clusters):
  for j,s in enumerate(S):
   rows=[r for r in D if r['pair_id'] in pairs and r['system']==s];assert len(rows)>0
   if j==0:den[i]=len(rows);up[i]=sum(r['expected_direction']=='up' for r in rows);down[i]=sum(r['expected_direction']=='down' for r in rows)
   num['answer'][i,j]=sum(int(r['dir_correct']) for r in rows);num['chain'][i,j]=sum(int(r['chain_pass']) for r in rows);num['joint'][i,j]=sum(int(r['joint_pass']) for r in rows)
   num['joint_up'][i,j]=sum(int(r['joint_pass']) for r in rows if r['expected_direction']=='up');num['joint_down'][i,j]=sum(int(r['joint_pass']) for r in rows if r['expected_direction']=='down')
 rng=np.random.default_rng(SEED+(0 if kind=='pair' else 1));W=rng.multinomial(n,np.full(n,1/n),size=B)
 d=W@den;u=W@up;v=W@down;valid=(u>0)&(v>0)
 boot={k:100*(W@num[k])/d[:,None] for k in ['answer','chain','joint']}
 bja=np.full((B,len(S)),np.nan);bja[valid]=50*((W[valid]@num['joint_up'])/u[valid,None]+(W[valid]@num['joint_down'])/v[valid,None]);boot['balanced_joint']=bja
 point={k:100*num[k].sum(0)/den.sum() for k in ['answer','chain','joint']};point['balanced_joint']=50*(num['joint_up'].sum(0)/up.sum()+num['joint_down'].sum(0)/down.sum())
 if kind=='pair':
  for key in ['answer','chain','joint']:
   boot['pair_equal_'+key]=100*(W@(num[key]/den[:,None]))/n;point['pair_equal_'+key]=100*(num[key]/den[:,None]).mean(0)
 for key,vals in boot.items():
  ok=np.isfinite(vals).all(1)
  for j,s in enumerate(S):
   lo,hi=np.quantile(vals[ok,j],[.025,.975]);cirows.append(dict(cluster=kind,metric=key,system=s,estimate=float(point[key][j]),lo=float(lo),hi=float(hi),replicates=B,valid_replicates=int(ok.sum()),n_clusters=n))
  g=S.index('GPT-6-Astra');c=S.index('Claude-Sonnet-5.5');delta=vals[ok,g]-vals[ok,c];lo,hi=np.quantile(delta,[.025,.975]);diffrows.append(dict(cluster=kind,metric=key,contrast='GPT-6-Astra minus Claude-Sonnet-5.5',estimate=float(point[key][g]-point[key][c]),lo=float(lo),hi=float(hi),positive_fraction=float((delta>1e-12).mean()),zero_fraction=float((abs(delta)<=1e-12).mean()),valid_replicates=int(ok.sum())))
 for key in ['balanced_joint','chain','joint']:
  vals=boot[key];vals=vals[np.isfinite(vals).all(1)];ranks=np.empty_like(vals)
  for j in range(len(S)):ranks[:,j]=1+(vals>vals[:,j,None]+1e-12).sum(1)+.5*((abs(vals-vals[:,j,None])<=1e-12).sum(1)-1)
  maxs=vals.max(1);ties=abs(vals-maxs[:,None])<=1e-12;credit=ties/ties.sum(1)[:,None]
  for j,s in enumerate(S):rankrows.append(dict(cluster=kind,metric=key,system=s,mean_rank=float(ranks[:,j].mean()),rank1_frequency=float(credit[:,j].mean()),rank1_inclusive_frequency=float(ties[:,j].mean()),rank_lo=float(np.quantile(ranks[:,j],.025)),rank_hi=float(np.quantile(ranks[:,j],.975))))
  if key=='balanced_joint':
   order=np.argsort(-point[key]);strict=((vals[:,order[:-1]]-vals[:,order[1:]])>1e-12).all(1)
   pairwise=[[float((vals[:,i]>vals[:,j]+1e-12).mean()+.5*(abs(vals[:,i]-vals[:,j])<=1e-12).mean()) for j in range(len(S))] for i in range(len(S))]
   results[kind]=dict(n_clusters=n,valid_bja_replicates=len(vals),total_replicates=B,published_strict_order_retention=float(strict.mean()),pairwise_win_fraction=pairwise,system_order=S)
 # Preserve all replicate estimates for independent checks and alternative intervals.
 np.savez_compressed(O/f'bootstrap_{kind}_replicates.npz',**boot)
write('cluster_bootstrap_ci.tsv',cirows);write('GPT_Claude_paired_differences.tsv',diffrows);write('bootstrap_rank_stability.tsv',rankrows)
results.update(seed=SEED,replicates=B,task='Task 2',n_pairs=len(P),primary_papers_after_identifier_resolution=resolved_papers,n_study_components=len(component_pairs),study_component_method='Resolve DOI/PMCID aliases, then merge papers linked by any shared pair; resample these nonoverlapping components.',largest_component=max(source_rows,key=lambda x:x['units']),runs_policy='All four runs and all units within a sampled cluster are retained together. No run-level biological replication is assumed.',interval='95% percentile; fixed released judgments and observed runs',metric_definitions={'balanced_joint':'unit-weighted joint recall averaged equally over up/down; matches published Task 2 BJA','pair_equal_chain':'within-pair average across units/runs, then equal weight per pair; a secondary different estimand'},ci=cirows,differences=diffrows,ranks=rankrows)
(O/'cluster_bootstrap_analysis.json').write_text(json.dumps(results,indent=2));print(json.dumps({k:v for k,v in results.items() if k not in ['ci','ranks','differences']},indent=2));print('Primary GPT-Claude difference:',[r for r in diffrows if r['metric']=='balanced_joint'])
