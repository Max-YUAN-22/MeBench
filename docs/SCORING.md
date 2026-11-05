# Scoring definitions and interpretation

## Answer, chain and joint correctness

Task 1 evaluates mechanism labels. Task 2 evaluates a response direction; Task 3 evaluates an intervention label against the accepted set after the disclosed matching operations.

Five binary explanation axes record mechanism, mediator, causal role/order, intervention–outcome link and absence of material contradiction. `chain_pass` is their product. `joint_pass` requires both an accepted task answer and a passing chain. The portable audit checks both identities against every consolidated record.

The released primary Task 2/3 table contains **joint balanced accuracy and protocol-specific joint F1**, not answer-only accuracy/F1. The simple joint pass rate is a separate quantity.

## Exact implementation-specific F1

For each class, let `z` indicate reference membership, `p` indicate a prediction of that class, and `C` indicate chain pass.

- Task 2 uses `TP = sum(z*p*C)`, `FN = sum(z*(1-p*C))`, and `FP = sum(p*(1-C))`.
- Task 3 uses `TP = sum(z*p*C)`, `FP = sum(p*(1-z*C))`, and `FN = sum(z*C*(1-p))`.

Class F1 is `2*TP/(2*TP+FP+FN)`; the released implementation skips zero-denominator classes per run. These definitions differ from conventional answer-only macro-F1. The revision preserves the published values and exposes the convention. `scripts/reproduce_release.py` recomputes all 36 main-table cells.

## Task 3 matching

1. Literal matching requires the submitted string to equal an accepted raw label.
2. Canonical matching applies the released synonym whitelist.
3. The disclosed RNA amendment maps canonical knockdown to inhibition when the perturbed entity contains `mir` under the implementation's normalization.

The amendment is separate from the frozen scorer. It is narrower than a rule for all regulatory RNA. All 480 amended acceptance values are reproduced by `scripts/analyze_task3_accepted_sets.py`. Nineteen units have one accepted canonical label and one has two; none of the archived answers is uniquely rescued by the second label.

## Validation boundary

The original and new automated calls are inspectable but are not independently validated biological truth. Neither cross-model agreement nor artifact consistency replaces blinded expert adjudication. Formatting mismatches, reference-method recovery, compatibility with an endpoint and mechanism validity are distinct error dimensions. Current limitations and sensitivity analyses preserve these distinctions.
