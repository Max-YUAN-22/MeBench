# TF–gene mechanism benchmark v3.7.0

Task 1 and Task 2 are unchanged from v3.6.1. Task 3 now contains 20 entity-conditioned units over nine bidirectional pairs.

Task 3 input is TF + target + supplied direction + vague perturbation entity. The intervention type and exact experimental implementation are hidden. The model outputs only the predicted intervention type and natural-language mechanism reasoning. Synonym normalization remains whitelist-based, and full correctness requires both an accepted intervention type for the supplied entity and a complete five-axis mechanism chain.

Hidden labels and exact source perturbations remain evaluator-only.
