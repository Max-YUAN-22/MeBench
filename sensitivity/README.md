# Sensitivity analyses: Appendices K–M

This directory contains the archived Gemini reassessment, accepted-set analysis, and secondary pair-level bootstrap. The [current supplement](../paper/supplement/MeBench_appendices_A-M.pdf) and [sensitivity guide](../docs/SENSITIVITY.md) specify the reported methods and corrected statistics.

| Analysis | Archived evidence | Current results |
|---|---|---|
| K: automated judge sensitivity | `K_judge_robustness/packets/`, `judgments/`, and `sample_design.json` | `reviewed/team_judge_audit.json` and accompanying TSVs |
| L: Task 3 accepted sets | `L_accepted_set/` | `../analysis/robustness/task3_accepted_sets_by_unit.tsv` and `task3_matching_by_record.tsv` |
| M: secondary equal-pair bootstrap | `M_pair_bootstrap/` | `reviewed/M_CORRECTED_RANKING.json` |

The primary unit-weighted pair/source bootstrap and the earlier independent-agent judge pilot are in `../analysis/robustness/`. Their metrics and input packets differ from the analyses here; see the sensitivity guide before comparing them.

## Reproduce from the repository root

```bash
python3 scripts/audit_team_sensitivity.py --root . --source sensitivity --output build/judge_gemini
python3 scripts/analyze_task3_accepted_sets.py --output build/accepted_sets
python3 scripts/compute_M_corrected.py --root . --output build/bootstrap_pair_equal
```

The bootstrap requires the numerical environment in the [reproduction guide](../docs/REPRODUCIBILITY.md). These commands replay archived evidence and make no model API calls. Original collection scripts inside the analysis subdirectories depend on the original workspace; use the commands above for supported reproduction.

## Interpretation and archived reports

Task 2 has 360 sampled responses, of which 358 parsed; Task 3 includes all 480 responses. Packet identifiers expose system identity, and the archived packets do not establish identical inputs to the original judge. Agreement measures adjudication sensitivity, not biological correctness. Four model runs are repeated protocol administrations, not four biological replicates.

The original `*/outputs/` reports and `../archive/sensitivity/ALL_RESULTS_TEXT.md` preserve supplied narratives and include superseded ranking calculations and packet descriptions. Use `reviewed/` and the current sensitivity guide for corrected results. Raw packets, raw replies, parsed judgments, and the earlier pilot are retained, including discrepant findings. `IMPORT_PROVENANCE.json` records the imported source hashes; documentation and the environment-configured runner have subsequently been revised.
