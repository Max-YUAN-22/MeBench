# Data and schema guide

## Frozen inputs and references

The three task bundles are under `benchmark/task1/`, `task2/` and `task3/`. Task inputs, hidden reference labels and evaluator metadata are separate files. Reference files are included in the public release for inspection and reproduction, not for presentation to the evaluated model. Files ending in `.tsv.gz` are gzip-compressed TSV.

Mechanism references require functional evidence supporting the regulatory relationship; intervention units also require compatible experimental context and an unambiguous response contrast. Binding or expression association alone is insufficient under these admission rules. The collection is curated, not an exhaustive survey of all eligible literature.

## Consolidated responses

| File | Records | Unique units | Distinct pairs |
|---|---:|---:|---:|
| `runs/MASTER_task1.tsv` | 4,104 | 171 | 171 |
| `runs/MASTER_task2.tsv` | 4,632 | 193 | 168 |
| `runs/MASTER_task3.tsv` | 480 | 20 | 9 |

A response record is identified by task, system, run and unit ID. Multiple intervention units can belong to one TF–gene pair. Four runs per system are repeated model administrations. Unit counts, response counts, pair counts and study counts should not be interchanged.

The full column definitions are in [`runs/MASTER_data_dictionary.md`](../runs/MASTER_data_dictionary.md). Per-run predictions, raw responses, adjudication packets and original judgments remain under `runs/`. Some archived prose fields are wrapped across lines; use the maintained audit readers or a TSV-aware parser rather than counting raw text lines.

## Provenance

Evaluator metadata contain source identifiers, source locations, contexts, perturbations, controls and experimental readouts. Use these records to trace a reference mechanism to its publication. Original provenance inventories are under `analysis/`. The source-cluster assignments used in the current bootstrap are in `analysis/robustness/study_components.tsv`.

## Derived supplementary data

The [supplement index](SUPPLEMENT_INDEX.md) maps every current Appendix A–M to the underlying records, derived tables and reproduction scripts. Current mechanism-module exports are in `analysis/mechanism_modules/`; the accepted-set comparisons include all 20 units and all 480 responses. Historical supplementary HTML is preserved in `paper/supplement/` and can use earlier conventions.
