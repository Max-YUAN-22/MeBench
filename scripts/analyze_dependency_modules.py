import csv,json,collections,re,statistics,pathlib,gzip
import argparse
parser=argparse.ArgumentParser(description='Reproduce module diagnostics from frozen master tables.')
parser.add_argument('--output',type=pathlib.Path,default=pathlib.Path('family_analysis'))
args=parser.parse_args()
R=pathlib.Path(__file__).resolve().parents[1];O=args.output;O.mkdir(parents=True,exist_ok=True)
D={t:list(csv.DictReader(open(R/f'runs/MASTER_task{t}.tsv'),delimiter='\t')) for t in (1,2,3)}
AX=['mechanism_correct','mediator_correct','causal_role_order_correct','intervention_outcome_link_correct','no_material_contradiction']
S=list(dict.fromkeys(r['system'] for r in D[1]))
def write(name,rows):
 if not rows:return
 with open(O/name,'w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
def count(rows):return dict(n=len(rows),pairs=len({r['pair_id'] for r in rows}),units=len({r['unit_id'] for r in rows}),chain_pass=sum(r['chain_pass']=='1' for r in rows),causal_fail=sum(r[AX[2]]=='0' for r in rows),BHLHE40_named=sum(bool(re.search(r'BHLHE40',r['mechanism_reasoning'],re.I)) for r in rows),direction_correct=sum(r.get('dir_correct')=='1' for r in rows),accepted_type_correct=sum(r.get('type_accepted')=='1' for r in rows),mediator_pass_role_fail=sum(r[AX[1]]=='1' and r[AX[2]]=='0' for r in rows))
a={}
a['T2_overlap']=collections.Counter((r['dir_correct'],r['chain_pass']) for r in D[2]);a['T2_overlap']={str(k):v for k,v in a['T2_overlap'].items()}
for u in ['T2U_0022','T2U_0036','T2U_0037','T2U_0038','T3VP_0002','T3VP_0004']:
 t=2 if u.startswith('T2') else 3;rows=[r for r in D[t] if r['unit_id']==u];a[u]=count(rows)
 if t==3:a[u]['types']=dict(collections.Counter(r['predicted_type_canonical'] for r in rows))
 write(u+'_responses.tsv',rows)
select={
 'PPARA_activation':lambda r:r['unit_id'] in ['T2U_0036','T2U_0037','T2U_0038'],
 'BHLHE40_depletion':lambda r:r['unit_id'] in ['T2U_0039','T2U_0040','T2U_0041'],
 'TP63_TF_loss':lambda r:r['tf']=='TP63' and 'FOXK1' in r['gold_mediator'] and r['perturbed_entity']=='TP63',
 'FOXK1_loss':lambda r:r['tf']=='TP63' and 'FOXK1' in r['gold_mediator'] and r['perturbed_entity']=='FOXK1',
 'GATA1_TAL1':lambda r:'TAL1' in r['gold_mediator'],
 'ESR1_enhancer':lambda r:r['unit_id'] in ['T2U_0013','T2U_0014','T2U_0015'],
 'SRCAP_H2AZ':lambda r:'SRCAP' in r['gold_mediator'],
}
module=[]
for label,fn in select.items():
 rows=[r for r in D[2] if fn(r)];a[label]=count(rows);a[label]['systems']={s:dict(chain_pass=sum(r['chain_pass']=='1' for r in rows if r['system']==s),FOXK1_mentions=sum('FOXK1' in r['mechanism_reasoning'].upper() for r in rows if r['system']==s)) for s in S}
 module.append(dict(group=label,**count(rows)))
 write(label+'_responses.tsv',rows)
a['T3VP_0004']['Biomni']=[{k:r[k] for k in ['run','type_accepted',*AX,'chain_pass']} for r in D[3] if r['unit_id']=='T3VP_0004' and r['system']=='Biomni']
a['near_miss']={s:len({r['unit_id'] for r in D[2] if r['system']==s and sum(r[k]=='0' for k in AX)==1}) for s in S}
for s in S:
 for run in range(1,5):
  rows=[r for r in D[2] if r['system']==s and int(r['run'])==run]
  if s=='GLM-5.3-Flash':
   a[f'GLM_echo_{run}']=sum(r['predicted_direction']==r['intervention_type'] for r in rows)
   a[f'GLM_other_invalid_{run}']=sum(r['predicted_direction'] not in ['up','down',r['intervention_type']] for r in rows)
a['T1_direct_n']=sum(r['predicted_mechanism']=='direct_cis_regulatory_dna' for r in D[1]);a['T1_total']=len(D[1])
a['T1_classes']={g:dict(n=len(rows),direct=sum(r['predicted_mechanism']=='direct_cis_regulatory_dna' for r in rows),correct=sum(r['correct']=='1' for r in rows)) for g in sorted({r['gold_mechanism'] for r in D[1]}) for rows in [[r for r in D[1] if r['gold_mechanism']==g]]}
a['T2_mean_explanation_chars']={s:statistics.mean(len(r['mechanism_reasoning']) for r in D[2] if r['system']==s) for s in S}
# Strict shared failure means every one of 24 system-run records fails on that unit.
for t in (2,3):
 units=[];pairs=[]
 for u in dict.fromkeys(r['unit_id'] for r in D[t]):
  rows=[r for r in D[t] if r['unit_id']==u];assert len(rows)==24
  if all(r['chain_pass']=='0' for r in rows):
   r=rows[0];units.append(dict(task=t,unit_id=u,pair_id=r['pair_id'],tf=r['tf'],target=r['target_gene'],mechanism=r['gold_mechanism'],perturbed_entity=r.get('perturbed_entity',r.get('given_perturbed_entity')),n=24,mechanism_fail=sum(r[AX[0]]=='0' for r in rows),mediator_fail=sum(r[AX[1]]=='0' for r in rows),causal_fail=sum(r[AX[2]]=='0' for r in rows),outcome_link_fail=sum(r[AX[3]]=='0' for r in rows),evidence_fail=sum(r[AX[4]]=='0' for r in rows)))
 for pair in dict.fromkeys(r['pair_id'] for r in D[t]):
  rows=[r for r in D[t] if r['pair_id']==pair]
  if all(r['chain_pass']=='0' for r in rows):
   r=rows[0];pairs.append(dict(task=t,pair_id=pair,tf=r['tf'],target=r['target_gene'],units=len({r['unit_id'] for r in rows}),n=len(rows),gold_mediator=r['gold_mediator']))
 write(f'T{t}_all24_fail_units.tsv',units);write(f'T{t}_all_interventions_fail_pairs.tsv',pairs)
 a[f'T{t}_strict_shared_failure']={'units':len(units),'pairs_all_interventions':len(pairs),'pairs':pairs}
 # All axis discrepancies must remain flagged, not presumed biological contradictions.
 if t==2:write('T2_answer_wrong_chain_pass_review.tsv',[r for r in D[t] if r['dir_correct']=='0' and r['chain_pass']=='1'])
write('modules.tsv',module)
json.dump(a,open(O/'claim_audit.json','w'),indent=2)
print(json.dumps(a,indent=2))
