# Post-freeze sensitivity analyses

All primary predictions, original judgments and published table values remain unchanged. The current manuscript's K–M analyses use the following separate evidence sources and estimands.

## K: automated adjudication

**Author-supplied Gemini reassessment:** configured `gemini-3.8-flash` through relay serving, temperature 0, batch size 40, seed 20261017. Task 2 samples 30 originally passing and 30 failing responses per system, with failure-axis quotas: 360 designed, 358 parsed. Task 3 enumerates all 480 responses. Full-chain agreement is 96.4%/89.8%, kappa 0.927/0.783. Task 2's +2.5 percentage-point pass change describes its enriched sample; Task 3's full-task change is +3.5 points.

Original axis manifests match the frozen MASTER tables and all 838 valid new calls match archived raw outputs. Composite IDs expose the evaluated system; original inputs and answers are not separate explicit packet columns. Exact original serving-prompt identity and provider checkpoint cannot be independently established from the bundle. Corrected Task 3 Kendall tau-b is 0.643, evaluated on aligned system scores with ties. GPT and GLM tie under the new judge. System-associated fail-to-pass differences are descriptive and do not establish causal self-preference.

Raw packets and outputs are in `sensitivity/K_judge_robustness/`. Use `sensitivity/reviewed/team_judge_audit.json` and associated TSVs for reviewed metrics. The two missing Task 2 rows are listed there and are excluded, not imputed as failures.

**Earlier independent-agent pilot:** 120 responses, 60/task, ten/system/task, seed 20261105; 73 joint mechanism/mediator/role/chain strata with known inverse-inclusion weights. A configured `gpt-6.1-terra` independent agent received identity-masked packets with explicit inputs, predictions and richer task-specific references. Weighted chain agreement is 91.0%/59.9%, kappa 0.772/0.284. Small sampled strata limit variance estimation. All 60 Task 3 pilot cases occur in the Gemini enumeration, but packet differences confound a pure judge-model comparison. The complete pilot is retained in `analysis/robustness/`, including raw calls, sampling weights, mapping, rubric and hashes.

These studies probe protocol sensitivity, not biological correctness or replacement rankings.

## L: accepted sets and identifiability

The 20 units include 19 singleton accepted sets and one two-label set, `T3VP_0003` (TWIST1–HOXD10, miR-10b/up; inhibition or sponge inhibition). Across 480 responses, semantic aliases rescue 100 literal mismatches and the disclosed RNA amendment rescues a further 42. The second accepted label rescues no additional answer. Four responses per system in the two-label stratum belong to one biological unit.

There are 14 entity/direction combinations with consistent annotated sets in this finite collection. That lookup structure does not prove a general biological inverse law, and singleton sets do not exhaust compatible interventions. Current complete exports are `analysis/robustness/task3_accepted_sets_by_unit.tsv` and `task3_matching_by_record.tsv`.

## M: cluster bootstrap

| Analysis | Estimand | Draws / seed | Source |
|---|---|---|---|
| Primary pair bootstrap | Published unit-weighted Task 2 joint balanced accuracy | 20,000 / 20261105 | `analysis/robustness/` |
| Primary source-component bootstrap | Same joint BAcc; nonoverlapping source components | 20,000 / 20261106 | `analysis/robustness/` |
| Secondary pair bootstrap | Equal mean of per-pair chain/joint pass rates | 10,000 / 20261017 | `sensitivity/reviewed/M_CORRECTED_RANKING.json` |

Each sampled pair retains all its intervention units and four observed runs. All six systems use identical resampled clusters for paired comparisons. Primary intervals use NumPy percentile quantiles; the supplied secondary implementation retains its ordered empirical percentile convention. The source analysis resolves DOI/PMCID aliases and joins papers connected by shared pairs: 36 papers form 31 components. The supplied deterministic GSE/DOI primary-source grouping yields the same pair partition on these data. One component contributes 99/168 pairs.

Primary GPT–Claude joint-BAcc difference: +4.06 pp, pair 95% CI [0.19, 8.61], source-component CI [-1.36, 14.32]. Secondary equal-pair chain/joint differences: +3.1/+2.6 pp with intervals [1.2, 5.2]/[0.9, 4.6]. The estimands differ and should not be interchanged.

Reviewed secondary ranking statistics use aligned scores, explicit tie rules and direct pairwise inversions even when another system lies between the two. Strict ordering recurs in 52.76%/48.46% of chain/joint draws; Grok/Gemini invert in 28.70%/40.82%. Original supplied HTML/JSON remain archived and include superseded ranking calculations. All pass-rate point estimates and intervals are unchanged by the rank correction.

Intervals condition on fixed reference labels, archived judges and observed runs. First-place/positive-difference frequencies are descriptive bootstrap frequencies, not posterior probabilities or reported hypothesis-test p-values. No biological replication or human validation is added by resampling.
