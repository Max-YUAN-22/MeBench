from pathlib import Path
import argparse,csv,json,collections,math,gzip,re,hashlib
p=argparse.ArgumentParser(description='Independently audit archived author-supplied sensitivity data without model calls.');p.add_argument('--root',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--pilot',type=Path);a=p.parse_args();R=a.root;S=a.source;O=a.output;O.mkdir(parents=True,exist_ok=True)
AX=['mechanism_correct','mediator_correct','causal_role_order_correct','intervention_outcome_link_correct','no_material_contradiction'];SYSTEMS=['GPT-6-Astra','Claude-Sonnet-5.5','Gemini-3.8-Flash','GLM-5.3-Flash','Grok-4.6','Biomni']
def write(fn,rs):
 with open(O/fn,'w') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter='\t');w.writeheader();w.writerows(rs)
def metric(old,new):
 n=len(old);agree=sum(x==y for x,y in zip(old,new))/n;po=sum(old)/n;pn=sum(new)/n;pe=po*pn+(1-po)*(1-pn)
 return dict(n=n,agreement=agree,kappa=(agree-pe)/(1-pe) if pe<1 else None,old_pass=po,new_pass=pn,delta=pn-po,fail_to_pass=sum(x==0 and y==1 for x,y in zip(old,new)),pass_to_fail=sum(x==1 and y==0 for x,y in zip(old,new)))
def tau_b(x,y):
 c=d=tx=ty=0
 for i in range(len(x)):
  for j in range(i):
   dx=(x[i]>x[j])-(x[i]<x[j]);dy=(y[i]>y[j])-(y[i]<y[j])
   if dx and dy:
    if dx==dy:c+=1
    else:d+=1
   elif dx:ty+=1
   elif dy:tx+=1
 den=math.sqrt((c+d+tx)*(c+d+ty));return (c-d)/den if den else None
allrows=[];summary={};checks={};missing=[];protocol={};axisrows=[];rankrows=[]
for t in (2,3):
 master=list(csv.DictReader(open(R/f'runs/MASTER_task{t}.tsv'),delimiter='\t'));M={f"{r['unit_id']}@{r['system']}@run{r['run']}":r for r in master}
 manifest=json.load(open(S/f'K_judge_robustness/packets/task{t}_manifest.json'));assert len(manifest)==len({r['key'] for r in manifest})
 new={};raw_validated=0;packets={};rubrics=set();parse_missing=[]
 for f in sorted((S/'K_judge_robustness/packets').glob(f'task{t}_rejudge_batch*.txt')):
  txt=f.read_text();prefix,body=txt.split('\n\nunit_id\t',1);rubrics.add(prefix);lines=('unit_id\t'+body).splitlines();header=lines[0].split('\t')
  for line in lines[1:]:
   values=line.split('\t');assert len(values)==len(header),(f.name,len(values));packets[values[0]]=dict(zip(header,values))
  stem=f.stem;raw=(S/'K_judge_robustness/judgments'/f'{stem}_raw.txt').read_text();continuation=S/'K_judge_robustness/judgments'/f'{stem}_raw.continuation_raw.txt'
  if continuation.exists():raw+='\n'+continuation.read_text()
  rawrows={}
  for line in raw.splitlines():
   vs=line.strip().split('\t')
   if len(vs)>=6 and '@' in vs[0] and all(v in ['0','1'] for v in vs[1:6]):rawrows[vs[0]]=list(map(int,vs[1:6]))
  parsed=list(csv.DictReader(open(S/'K_judge_robustness/judgments'/f'{stem}_judgments.tsv'),delimiter='\t'))
  for r in parsed:
   key=r['unit_id'];assert key not in new,key;vs=[r[x] for x in AX];assert all(v in ['0','1'] for v in vs);v=list(map(int,vs));assert rawrows[key]==v,key;new[key]=v;raw_validated+=1
 assert set(new)<=set(packets)=={m['key'] for m in manifest};assert len(rubrics)==1
 for m in manifest:
  key=m['key'];r=M[key];assert all(int(r[x])==m['orig_axes'][x] for x in AX);assert int(r['chain_pass'])==m['orig_chain_pass']
  if key not in new:missing.append(dict(task=t,key=key,old_chain=int(r['chain_pass'])));continue
  v=new[key];row=dict(task=t,key=key,system=r['system'],run=r['run'],unit_id=r['unit_id'],pair_id=r['pair_id'],old_chain=int(r['chain_pass']),new_chain=int(all(v)))
  for x,n in zip(AX,v):row['old_'+x]=int(r[x]);row['new_'+x]=n
  allrows.append(row)
 rs=[r for r in allrows if r['task']==t];metrics={}
 for x in AX+['chain']:
  metrics[x]=metric([r['old_'+x] for r in rs],[r['new_'+x] for r in rs]);axisrows.append(dict(task=t,axis=x,**metrics[x]))
 changes=[]
 for s in SYSTEMS:
  rr=[r for r in rs if r['system']==s];changes.append(dict(task=t,system=s,**metric([r['old_chain'] for r in rr],[r['new_chain'] for r in rr])))
 def ranks(vs):return [1+sum(v>x+1e-12 for v in vs)+.5*(sum(abs(v-x)<1e-12 for v in vs)-1) for x in vs]
 old=[r['old_pass'] for r in changes];nex=[r['new_pass'] for r in changes]
 for r,ro,rn in zip(changes,ranks(old),ranks(nex)):r.update(old_rank=ro,new_rank=rn);rankrows.append(r)
 subsets={}
 for sset,label in [({'Gemini-3.8-Flash'},'Gemini'),(set(SYSTEMS)-{'Gemini-3.8-Flash'},'Others')]:
  rr=[r for r in rs if r['system'] in sset];nf=sum(r['old_chain']==0 for r in rr);f2p=sum(r['old_chain']==0 and r['new_chain']==1 for r in rr);subsets[label]=dict(n=len(rr),original_failures=nf,fail_to_pass=f2p,f2p_rate=f2p/nf)
 summary[str(t)]={'sampled':len(manifest),'parsed':len(rs),'metrics':metrics,'systems':changes,'kendall_tau_b':tau_b(old,nex) if t==3 else None,'self_preference_descriptive':subsets}
 protocol[str(t)]={'rubric_sha256':hashlib.sha256(next(iter(rubrics)).encode()).hexdigest(),'packet_columns':list(next(iter(packets.values())).keys()),'system_identity_visible_in_keys':True,'old_axes_visible':False,'full_model_input_and_separate_prediction_fields_present':False,'raw_rows_validated':raw_validated}
 checks[f'task{t}_all_manifest_axes_match_master']=True;checks[f'task{t}_all_parsed_axes_match_raw']=True
# Compare two judges on exactly the earlier pilot cases, still under different information packets.
pilot=a.pilot or R/'analysis/robustness/judge_reassessment_by_record.tsv'
if not pilot.exists():raise FileNotFoundError('Provide --pilot with the archived pilot reassessment TSV.')
comparison=[]
for r in csv.DictReader(open(pilot),delimiter='\t'):
 key=f"{r['unit_id']}@{r['system']}@run{r['run']}";team=next((x for x in allrows if x['task']==int(r['task']) and x['key']==key),None)
 if team:comparison.append(dict(task=r['task'],pilot_case_id=r['case_id'],key=key,original_chain=team['old_chain'],pilot_chain=int(r['new_chain']),gemini_chain=team['new_chain']))
write('gemini_reassessment_by_record.tsv',allrows);write('gemini_agreement_metrics.tsv',axisrows);write('gemini_system_changes.tsv',rankrows);write('cross_protocol_overlap.tsv',comparison)
result=dict(protocol=protocol,tasks=summary,missing=missing,checks=checks,cross_protocol_overlap={'n':len(comparison),'by_task':dict(collections.Counter(r['task'] for r in comparison))},scope='Archived relay reassessment; identifiers disclose system; different packet information from prior independent pilot. No fresh API calls or human adjudication.');(O/'team_judge_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({'summary':{t:dict(sampled=v['sampled'],parsed=v['parsed'],chain=v['metrics']['chain'],kendall_tau_b=v['kendall_tau_b']) for t,v in summary.items()},'missing':missing,'overlap':result['cross_protocol_overlap']},indent=2))
