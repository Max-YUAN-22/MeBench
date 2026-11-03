# Claude Science prompt — v3.7.0 task3

## Mandatory closed-book and no-tools rules

- Do not access the internet, browse, search literature or databases, use retrieval, plugins, APIs, code execution, external files, or any other tools.
- Do not use remembered papers, pair-specific published findings, database records, benchmark labels, or recalled experimental outcomes.
- If you recognize a pair or experiment, disregard the recalled result.
- Use only this prompt, the supplied input fields, and general biological reasoning not tied to a remembered source.

The benchmark distinguishes four mechanisms:

- `direct_cis_regulatory_dna`: the TF acts through a target-linked cis-regulatory DNA element.
- `chromatin_mediated_regulation`: the TF-target effect requires a chromatin state or chromatin regulator.
- `combinatorial_tf_regulation`: the TF-target effect requires a partner transcription factor.
- `regulatory_rna_mediated_indirect_regulation`: the TF-target effect is relayed through an intermediate regulatory RNA.

## Task

Each unit supplies `tf`, `target_gene`, a known target-expression `direction`, and a deliberately vague `perturbation` containing only `perturbed_entity`. The exact intervention type and experimental implementation are hidden.

Predict how the supplied entity was perturbed in `predicted_intervention_type`. Then give a concise natural-language `mechanism_reasoning` explanation that identifies the mechanism and key mediator, assigns the mediator the correct causal role/order, and connects the supplied entity plus inferred intervention to the supplied target direction.

The evaluator uses a fixed intervention-type synonym whitelist, but the biological meaning must agree with an accepted intervention for the supplied entity. A unit passes the primary score only when the inferred intervention type is accepted and the complete five-axis mechanism chain is correct. Direction and perturbed entity are inputs and are not predicted.

Do not ask for hidden labels, controls, contexts, evidence, sources, or curator notes. Do not reveal private chain-of-thought; provide only the requested concise causal reasoning summary.

Return only tab-separated text with exactly this header:

```text
unit_id	predicted_intervention_type	mechanism_reasoning
```

Copy every `unit_id` exactly and include every unit exactly once. Keep reasoning on one line without tabs or line breaks. Do not add citations, confidence scores, Markdown tables, code fences, or extra columns.
