# Claude Science prompt — v3.7.0 task2

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

Each unit supplies `tf`, `target_gene`, and a deliberately minimal `perturbation` containing only `perturbed_entity` and a coarse `intervention_type`.

The four coarse intervention types are `loss_or_reduction`, `gain_or_activation`, `regulatory_site_perturbation`, and `functional_variant`. The exact experimental method, dose, time, route, reagent, guide and context are intentionally unavailable. Do not invent them.

Predict target-expression `up` or `down`. In `mechanism_reasoning`, give a concise natural-language causal explanation using only the coarse perturbation information: identify the mechanism and key intermediate, assign its correct causal role/order, and connect the coarse perturbation to the target direction. Ordinary prose is required; a bare mechanism name or generic definition is insufficient.

A unit passes the primary score only when both direction and the full ground-truth mechanism chain are correct.

Do not ask for hidden labels, controls, contexts, evidence, sources, or curator notes. Do not reveal private chain-of-thought; provide only the requested concise causal reasoning summary.

Return only tab-separated text with exactly this header:

```text
unit_id	predicted_direction	mechanism_reasoning
```

Copy every `unit_id` exactly and include every unit exactly once. Keep reasoning on one line without tabs or line breaks. Do not add citations, confidence scores, Markdown tables, code fences, or extra columns.
