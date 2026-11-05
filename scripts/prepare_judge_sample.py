import csv,json,gzip,random,collections,hashlib
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Regenerate the stratified blinded sample; no judge invocation.')
parser.add_argument('--output',type=Path,default=Path('judge_sample_regenerated'))
args=parser.parse_args();R=Path(__file__).resolve().parents[1];O=args.output;W=O/'blind_packets';W.mkdir(parents=True,exist_ok=True)
AX=['mechanism_correct','mediator_correct','causal_role_order_correct','intervention_outcome_link_correct','no_material_contradiction']
D={t:list(csv.DictReader(open(R/f'runs/MASTER_task{t}.tsv'),delimiter='\t')) for t in (2,3)}
G={t:{r['unit_id']:json.loads(r['reasoning_ground_truth_json']) for r in csv.DictReader(gzip.open(R/f'benchmark/task{t}/hidden_labels.tsv.gz','rt'),delimiter='\t')} for t in (2,3)}
seed=20261105;rng=random.Random(seed);selected=[];strata=[]
for t in (2,3):
 for system in dict.fromkeys(r['system'] for r in D[t]):
  groups=collections.defaultdict(list)
  for r in D[t]:
   if r['system']==system:
    key=''.join(r[a] for a in AX[:3])+r['chain_pass'];groups[key].append(r)
  # Include every nonempty mechanism/mediator/role/chain pattern; allocate the rest by N_h/(n_h+1).
  alloc={k:1 for k in groups};assert len(alloc)<=10
  for _ in range(10-len(alloc)):
   eligible=[k for k in groups if alloc[k]<len(groups[k])]
   k=max(eligible,key=lambda k:(len(groups[k])/(alloc[k]+1),k));alloc[k]+=1
  for key,rows in sorted(groups.items()):
   n=alloc[key];N=len(rows);stratum=f'T{t}|{system}|{key}'
   strata.append(dict(task=t,system=system,pattern=key,N=N,n=n,inclusion_probability=n/N,weight=N/n))
   for r in rng.sample(rows,n):selected.append(dict(task=t,row=r,stratum=stratum,N=N,n=n,weight=N/n))
rng.shuffle(selected);pack=[];mapping=[]
for i,s in enumerate(selected,1):
 t=s['task'];r=s['row'];cid=f'J{i:04d}';gt=G[t][r['unit_id']]
 inp={'tf':r['tf'],'target_gene':r['target_gene']}
 if t==2:inp['perturbation']={'perturbed_entity':r['perturbed_entity'],'intervention_type':r['intervention_type']};pred={'predicted_direction':r['predicted_direction']}
 else:inp['direction']=r['given_direction'];inp['perturbed_entity']=r['given_perturbed_entity'];pred={'predicted_intervention_type':r['predicted_intervention_type']}
 pack.append(dict(case_id=cid,task=f'task{t}',model_input=inp,model_answer=pred,mechanism_reasoning=r['mechanism_reasoning'],reference={k:gt[k] for k in ['mechanism_class','mediator_type','mediator_entity','causal_topology','evidence_chain_statement','task_specific_link']}))
 mapping.append(dict(case_id=cid,task=t,system=r['system'],run=r['run'],unit_id=r['unit_id'],pair_id=r['pair_id'],stratum=s['stratum'],N=s['N'],n=s['n'],weight=s['weight'],old_axes={a:int(r[a]) for a in AX},old_chain=int(r['chain_pass'])))
text='\n'.join(json.dumps(x,ensure_ascii=False) for x in pack)+'\n';(W/'blinded_cases.jsonl').write_text(text)
for i in range(0,len(pack),20):(W/f'blind_batch_{i//20+1}.json').write_text(json.dumps(pack[i:i+20],ensure_ascii=False,indent=2))
(O/'judge_sample_mapping.json').write_text(json.dumps(mapping,indent=2));(O/'judge_sampling_strata.json').write_text(json.dumps(strata,indent=2))
protocol=dict(seed=seed,total_population=len(D[2])+len(D[3]),sample_size=len(pack),per_system_task=10,sampling='SRS without replacement within all nonempty joint strata (mechanism, mediator, causal-role, chain); deterministic allocation before sampling',allocation='one record per nonempty stratum, then greedily maximize N_h/(n_h+1)',estimator='inverse-inclusion weighted; each stratum weight N_h/n_h',blinding='case IDs and random order; evaluated system, run, old judge labels and unit IDs not shown',rubric='verbatim released five-axis reasoning guide; gold references supplied',configured_new_judge='gpt-6.1-terra',runtime='independent Codex sub-agent with no conversation-history fork; not original provider API campaign',reliability_scope='cross-model sensitivity, not biological correctness; same GPT model family for some comparisons',packet_sha256=hashlib.sha256(text.encode()).hexdigest(),status='sample prepared; awaiting actual judgments')
(O/'judge_protocol.json').write_text(json.dumps(protocol,indent=2));(W/'RUBRIC.md').write_text((R/'runs/gpt/run1/task2_reasoning_review.tsv.GUIDE.md').read_text())
print(json.dumps({'sample_size':len(pack),'strata':len(strata),'packet_bytes':len(text.encode()),'per_task':dict(collections.Counter(s['task'] for s in selected))}))
