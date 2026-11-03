# MASTER task tables — column dictionary

One row = one (unit, system, run). Systems: GPT-6-Astra, Claude-Sonnet-5.5, Gemini-3.8-Flash, GLM-5.3-Flash, Grok-4.6, Biomni (4 runs each). These three files are the consolidated core raw data behind every analysis and every published number.

## MASTER_task1.tsv (4,104 rows = 171 units x 6 systems x 4 runs)
unit_id, pair_id, tf, target_gene          — question identifiers
gold_mechanism                             — evaluator-only gold class
predicted_mechanism                        — model's raw answer (as submitted)
correct                                    — 1 if exact match with gold

## MASTER_task2.tsv (4,632 rows = 193 units x 6 systems x 4 runs)
intervention_type, perturbed_entity        — the perturbation shown to the model
gold_mechanism / gold_mediator / gold_causal_topology / expected_direction — evaluator-only gold
predicted_direction                        — model's raw direction answer
dir_correct                                — 1 if direction matches gold
mechanism_correct, mediator_correct, causal_role_order_correct,
intervention_outcome_link_correct, no_material_contradiction — five-axis judgments (1/0)
chain_pass                                 — 1 if all five axes = 1
joint_pass                                 — dir_correct AND chain_pass
mechanism_reasoning                        — verbatim model explanation

## MASTER_task3.tsv (480 rows = 20 units x 6 systems x 4 runs)
given_direction, given_perturbed_entity    — what the model sees
gold_accepted_types                        — accepted interventions (canonical)
predicted_intervention_type                — model's raw answer
predicted_type_canonical                   — after canonical matcher (+ disclosed RNA alias)
type_accepted                              — 1 if canonical prediction in accepted set
[5 axis columns], chain_pass               — as Task 2
joint_pass                                 — type_accepted AND chain_pass
mechanism_reasoning                        — verbatim model explanation

## Conventions
- axis columns are empty only if a run lacks judgment coverage (currently none: all 4 runs adjudicated for all systems on both tasks)
- GLM T1 run 1 is the re-administered pass (original archived in 04_RUN_DATA/glm/pass1/task1_schema_deviant_2026-10-13)
- GLM T2 run 4 is the re-administered pass (original archived in 04_RUN_DATA/glm/pass4/api_failed_2026-10-12)
- scoring: as submitted; interpretable-but-non-compliant outputs score as incorrect

## Verify any published number from these files, e.g. GPT T2 joint pass:
awk -F'\t' '$13=="GPT-6-Astra"' MASTER_task2.tsv | awk -F'\t' 'NR>0{s+=$20; n++} END{printf "%.1f\n", 100*s/n}'
