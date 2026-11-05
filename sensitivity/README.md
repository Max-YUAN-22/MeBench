> Author-supplied archive, locally audited. The original narratives and HTML retain supplied statistics; use `reviewed/` and `REVIEW_NOTES_ZH.md` for corrected ranking metrics and protocol limitations. No model calls were made during review. The relay runner has been sanitized to environment-only configuration. The archived packet builder expects the original author workspace and is not a portable entry point for this package.

# Sensitivity appendices (post-freeze, non-frozen layer)

This directory holds three **post-freeze sensitivity addenda** requested for the paper. They are
**not part of the frozen v3.7.0 release** (manifest version 16, 2026-10-17): no frozen file,
judgment, or main-table value is modified. Every script here is read-only with respect to
`evaluation_v3.7.0/`, `prompt_v3.7.0/`, `runs/` (frozen manifest), and `RELEASE_v3.7.0/`.

| Appendix | Question | Method | Key outputs |
|---|---|---|---|
| **K** — Automated Judge Robustness and Adjudication Sensitivity | How much do the five-axis adjudication calls move under a different automated judge? | Stratified re-adjudication: T2 360 unit-runs (6 systems × 30 pass / 30 fail, quota-filled per failed axis), T3 all 480. Second judge `gemini-3.8-flash` (never a judge in the frozen pipeline), byte-identical rubric, seed 20261017. | `K_judge_robustness/outputs/APPENDIX_K_judge_robustness.html` |
| **L** — Identifiability and Accepted-Set Analysis for Task 3 | What does the Task 3 answer space actually accept? | Pure local recomputation from the shipped accepted-intervention sets: cardinality, exact vs accepted-set accuracy, identifiability map. No model calls, no new labels. | `L_accepted_set/outputs/APPENDIX_L_accepted_set.html` |
| **M** — Pair-Level Statistical Robustness | What is the uncertainty when resampling at the right level (pairs, not runs)? | Pair-level cluster bootstrap, B = 10,000, seed 20261017; GPT−Claude paired differences; ranking stability; study-level bootstrap with concentration disclosure (GSE266489 = 99/168 pairs). | `M_pair_bootstrap/outputs/APPENDIX_M_pair_robustness.html` |

## Standing caveats (repeated inside each appendix)

1. **K measures judge-choice sensitivity, not correctness.** The five adjudication axes have no gold
   standard beyond the evaluator-only construction fields; blinded human adjudication remains the
   open validation step for the frozen chain values.
2. **The 4 runs per system are technical repeats**, not independent biological replicates. Nowhere in
   K/M are runs resampled as if they were independent experiments; M's resampling unit is the TF–gene
   pair (and, separately, the source study).
3. **T3 is a 20-unit targeted diagnostic subset** (9 pairs); its CIs are wide by construction.

## Reproduce

```bash
cd L_accepted_set   && python3 compute_L.py
cd M_pair_bootstrap && python3 compute_M.py && python3 build_M_html.py
cd K_judge_robustness && python3 build_K_sample_and_packets.py \
                       && python3 run_K_rejudge.py \
                       && python3 compute_K_metrics.py && python3 build_K_html.py
```

K re-judging costs ~21 relay calls (batch = 40 rows). `sample_design.json` freezes the sample
before any model call; `packets/*_manifest.json` records the original judge's axes for each row.
