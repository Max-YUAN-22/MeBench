import csv,gzip,json,importlib.util,collections
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Recompute Task 3 literal, canonical and amended accepted-set diagnostics.')
parser.add_argument('--output',type=Path,default=Path('robustness_output'))
args=parser.parse_args()
R=Path(__file__).resolve().parents[1];O=args.output;O.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('s37',R/'evaluation_v3.7.0/scoring/score_model_outputs.py');sc=importlib.util.module_from_spec(spec);spec.loader.exec_module(sc)
canon=sc.previous.canonical_intervention;norm=sc.core.normalize
with gzip.open(R/'evaluation_v3.7.0/task3/hidden_labels.tsv.gz','rt') as f:G={r['unit_id']:r for r in csv.DictReader(f,delimiter='\t')}
D=list(csv.DictReader(open(R/'runs/MASTER_task3.tsv'),delimiter='\t'));systems=list(dict.fromkeys(r['system'] for r in D))
def write(name,rows):
 with open(O/name,'w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
unitinfo=[]
for u,g in G.items():
 a=json.loads(g['accepted_intervention_types_json']);ca=sorted({canon(x) for x in a})
 unitinfo.append(dict(unit_id=u,pair_id=g['pair_id'],tf=json.loads(g['reasoning_ground_truth_json'])['tf'],target=json.loads(g['reasoning_ground_truth_json'])['target_gene'],perturbed_entity=g['input_perturbed_entity'],given_direction=g['direction'],raw_cardinality=len(set(a)),canonical_cardinality=len(ca),raw_labels=';'.join(a),canonical_labels=';'.join(ca)))
write('task3_accepted_sets_by_unit.tsv',unitinfo)
scored=[]
for r in D:
 g=G[r['unit_id']];a=json.loads(g['accepted_intervention_types_json']);ca={canon(x) for x in a};p=r['predicted_intervention_type'];pc=canon(p)
 amended='inhibition' if 'mir' in g['input_perturbed_entity'].lower().replace(' ','') and pc=='knockdown' else pc
 x=dict(system=r['system'],run=r['run'],unit_id=r['unit_id'],pair_id=r['pair_id'],cardinality=len(a),prediction=p,canonical_prediction=pc,amended_prediction=amended,
 literal_set=int(p in a),case_punctuation_normalized_set=int(norm(p) in {norm(x) for x in a}),canonical_set=int(pc in ca),amended_set=int(amended in ca),canonical_first_label=int(pc==canon(a[0])),amended_first_label=int(amended==canon(a[0])),chain_pass=int(r['chain_pass']))
 assert x['amended_set']==int(r['type_accepted'])
 scored.append(x)
write('task3_matching_by_record.tsv',scored)
summary=[]
metrics=['literal_set','case_punctuation_normalized_set','canonical_set','amended_set','canonical_first_label','amended_first_label']
for system in systems:
 for card in ['all',1,2]:
  rows=[r for r in scored if r['system']==system and (card=='all' or r['cardinality']==card)]
  summary.append(dict(system=system,cardinality=card,records=len(rows),units=len({r['unit_id'] for r in rows}),**{k:100*sum(r[k] for r in rows)/len(rows) for k in metrics},set_extension_rescued=sum(r['amended_set']-r['amended_first_label'] for r in rows),alias_rescued=sum(r['canonical_set']-r['case_punctuation_normalized_set'] for r in rows),RNA_amendment_rescued=sum(r['amended_set']-r['canonical_set'] for r in rows)))
write('task3_accepted_set_metrics.tsv',summary)
# Unchanged supplied input must be distinguished from a hypothetical outcome-only input.
inputgroups=collections.defaultdict(list)
for u,g in G.items():
 gt=json.loads(g['reasoning_ground_truth_json']);key=(gt['tf'].casefold(),gt['target_gene'].casefold(),g['direction'],g['input_perturbed_entity'].casefold());inputgroups[key].append(u)
conflicts=[]
for k,units in inputgroups.items():
 if len(units)>1:conflicts.append(dict(input=k,units=units,accepted_sets=[json.loads(G[u]['accepted_intervention_types_json']) for u in units]))
result=dict(n_units=len(G),n_pairs=len({r['pair_id'] for r in G.values()}),raw_cardinality=dict(collections.Counter(len(json.loads(r['accepted_intervention_types_json'])) for r in G.values())),canonical_cardinality=dict(collections.Counter(len({canon(x) for x in json.loads(r['accepted_intervention_types_json'])}) for r in G.values())),multi_accepted_units=[r for r in unitinfo if r['canonical_cardinality']>1],identical_supplied_input_groups=conflicts,matching_definitions={'literal_set':'case-sensitive raw prediction equals any literal accepted label','case_punctuation_normalized_set':'released base normalize on prediction and all accepted labels, no semantic alias','canonical_set':'released curated synonym whitelist on prediction and all accepted labels','amended_set':'canonical set plus published entity-conditional RNA knockdown-to-inhibition amendment','first_label_metrics':'sensitivity illustration using the first listed reference, not an authoritative unique gold label'},summary=summary,scope='Annotated accepted-set multiplicity is not exhaustive biological identifiability; singleton sets do not establish unique inverse mappings.')
(O/'task3_accepted_set_analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
