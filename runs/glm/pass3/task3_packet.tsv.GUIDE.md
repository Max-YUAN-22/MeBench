# v3.5.1 task3 reasoning-chain adjudication guide

This packet is evaluator-only. Never provide it to the tested model.

For every row, fill each of the five fields with `1` or `0`:

1. `mechanism_correct`: the reasoning uses the ground-truth mechanism, not merely a compatible generic statement.
2. `mediator_correct`: it identifies the ground-truth key mediator. For direct-cis cases, an accurate target-linked cis-element type is sufficient; exact coordinates are not required. For chromatin, combinatorial-TF, and regulatory-RNA cases, the named mediator must match the hidden annotation or an unambiguous synonym.
3. `causal_role_order_correct`: the mediator is assigned the correct role and causal order/topology. Mere keyword co-occurrence fails.
4. `intervention_outcome_link_correct`: the explanation connects the supplied/inferred intervention to the target direction without reversing the effect logic.
5. `no_material_contradiction`: no statement contradicts the hidden chain, accepted perturbation, or direction.

Full-chain correctness requires all five fields to equal `1`. A bare mechanism name, a definition of a mechanism, or a restatement of the input must fail at least the mediator, causal-role/order, and intervention-outcome axes. Use `adjudicator_notes` for borderline cases.
