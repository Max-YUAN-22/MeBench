> **Historical source report — superseded narrative.** For corrected ranking statistics and verified packet contents, use [the current sensitivity guide](../../docs/SENSITIVITY.md) and `../../sensitivity/reviewed/`. The archived claim of identical original/reassessment input packets is not established by the supplied evidence.

# MechanismBench v3.7.0 — Sensitivity Appendices K / L / M — Full Text Results

Generated 2026-11-05. Post-freeze layer at `test10:8/v3.7/sensitivity/`. No frozen file touched
(MASTER tables mtime 2026-10-17; frozen manifest v16 unchanged).

---

## APPENDIX K — Automated Judge Robustness and Adjudication Sensitivity

### K.1 Design
- Second judge: **gemini-3.8-flash** (never served as a judge in the frozen pipeline; frozen judges were
  GPT-6-Astra for 5 systems + Claude-Sonnet-5.5 for GPT). Rubric byte-identical to the shipped adjudicator
  prompt; each row presented with exactly the content the original judge saw (input, prediction, reasoning,
  evaluator-only gold fields); temperature 0; batch = 40 rows; one continuation call per batch when needed.
- Sample: Task 2 = 360 unit-runs (6 systems × [30 original-pass / 30 original-fail], fail stratum quota-filled
  ≥6/system per failed axis). Task 3 = full enumeration, 480 unit-runs. Seed 20261017.
- Parse coverage: T2 358/360 (99.4%); T3 480/480 (100%).

### K.2 Axis-wise agreement (agreement %, Cohen's κ, confusion counts)

**Task 2 (n = 358)**

| Axis | Agreement | κ | orig+ rate | rejudge+ rate | orig1→re0 | orig0→re1 |
|---|---|---|---|---|---|---|
| Mechanism | 97.2 | 0.942 | 59.8 | 59.8 | 5 | 5 |
| Mediator | 93.9 | 0.873 | 60.3 | 57.5 | 16 | 6 |
| Causal order | 97.2 | 0.944 | 53.1 | 52.5 | 6 | 4 |
| Outcome link | 86.6 | 0.513 | 77.9 | 90.2 | 2 | 46 |
| No contradiction | 77.9 | 0.493 | 69.3 | 66.8 | 44 | 35 |
| **Chain pass (all five)** | **96.4** | **0.927** | 50.0 | 52.5 | 2 | 11 |

**Task 3 (n = 480)**

| Axis | Agreement | κ | orig+ rate | rejudge+ rate | orig1→re0 | orig0→re1 |
|---|---|---|---|---|---|---|
| Mechanism | 94.8 | 0.862 | 77.3 | 72.5 | 24 | 1 |
| Mediator | 91.2 | 0.777 | 71.9 | 74.8 | 14 | 28 |
| Causal order | 93.5 | 0.856 | 67.1 | 64.8 | 21 | 10 |
| Outcome link | 91.9 | 0.633 | 85.0 | 89.8 | 8 | 31 |
| No contradiction | 85.2 | 0.563 | 80.0 | 76.9 | 43 | 28 |
| **Chain pass (all five)** | **89.8** | **0.783** | 60.6 | 64.2 | 16 | 33 |

κ bands (Landis–Koch): mechanism/mediator/causal-order = substantial-to-almost-perfect; outcome-link and
no-contradiction = moderate. **The two interpretive axes carry essentially all disagreement; the three
construct-matching axes are near-perfect.**

### K.3 Pass-rate difference under the replacement judge
- Task 2: chain pass 50.0% → 52.5% (Δ = **+2.5 pp**; 11 fail→pass vs 2 pass→fail).
- Task 3: chain pass 60.6% → 64.2% (Δ = **+3.5 pp**; 33 fail→pass vs 16 pass→fail).
- Both shifts small vs between-tier gaps (GLM ≈20 pp below field), same order as mid-tier spacing.

### K.4 Model ranking stability
**Design constraint (disclosed):** the T2 sample is balanced by construction (30/30 per system), so per-system
levels are pinned at ~50% and **the T2 sample cannot support any ranking claim**. Ranking assessed on T3 only.

Task 2 — per-system deltas on the identical sample (levels pinned; deltas informative only):

| System | n | orig pass | rejudge pass | Δ (pp) | f2p | p2f |
|---|---|---|---|---|---|---|
| GPT-6-Astra | 60 | 50.0 | 48.3 | −1.7 | 0 | 1 |
| Claude-Sonnet-5.5 | 59 | 50.8 | 52.5 | +1.7 | 1 | 0 |
| Gemini-3.8-Flash | 60 | 50.0 | 61.7 | **+11.7** | 7 | 0 |
| GLM-5.3-Flash | 60 | 50.0 | 50.0 | 0.0 | 0 | 0 |
| Grok-4.6 | 59 | 49.2 | 50.8 | +1.6 | 1 | 0 |
| Biomni | 60 | 50.0 | 51.7 | +1.7 | 2 | 1 |

Task 3 (full enumeration, 80 rows/system) — levels meaningful:

| System | orig pass | rejudge pass | Δ (pp) | f2p | p2f | Rank orig → re |
|---|---|---|---|---|---|---|
| GPT-6-Astra | 72.5 | 67.5 | −5.0 | 1 | 5 | 1 → 2 |
| Gemini-3.8-Flash | 68.8 | 72.5 | +3.7 | 6 | 3 | 2 → 1 |
| Grok-4.6 | 66.2 | 66.2 | 0.0 | 3 | 3 | 3 → 4 |
| Claude-Sonnet-5.5 | 56.2 | 62.5 | +6.2 | 6 | 1 | 4 → 5 |
| GLM-5.3-Flash | 56.2 | 67.5 | +11.2 | 9 | 0 | 5 → 3 |
| Biomni | 43.8 | 48.8 | +5.0 | 8 | 4 | 6 → 6 |

Kendall τ = 0.333. Bottom rank stable (Biomni); top-two adjacency (GPT/Gemini, 3.7 pp apart) inverts.
Population-level ordering is addressed in Appendix M (P(GPT first) = 99.95% under pair resampling).

### K.5 Self-preference check (Gemini judge on Gemini-origin rows)

| Group | Fail rows (T2) | f2p (T2) | Flip rate (T2) | Fail rows (T3) | f2p (T3) | Flip rate (T3) |
|---|---|---|---|---|---|---|
| Gemini-origin rows | 30 | **7** | **23.3%** | 25 | 6 | 24.0% |
| Other systems' rows | 149 | 4 | 2.7% | 164 | 27 | 16.5% |

- T2: 7 of the 11 fail→pass flips (64%) fall on Gemini-origin rows; flip rate 23.3% vs 2.7% for others.
- T3: same direction, attenuated (24.0% vs 16.5%); Gemini-origin rows also show slightly higher axis agreement
  (T3 93.5% vs 90.9%; T2 89.0% vs 90.9%).
- **Interpretation: automated judges are not exchangeable.** Empirical justification for the frozen pipeline's
  cross-family judging (no model judged its own outputs) and for keeping chain values preliminary pending
  blinded human adjudication.

### K.6 Summary
(i) Construct-matching axes robust to judge choice (κ 0.78–0.94); disagreement concentrates in the interpretive
axes. (ii) Chain-pass shifts of +2.5/+3.5 pp — small vs system gaps, comparable to mid-tier spacing → reinforces
"tier, not ranking" reading of the mid-field. (iii) Bottom rank reproduced; only the top-two adjacency unresolved.
(iv) Judge self-preference signal present and disclosed. (v) Measures judge-choice sensitivity, NOT correctness;
blinded human adjudication remains the open validation step.

---

## APPENDIX L — Identifiability and Accepted-Set Analysis for Task 3

No new labels; shipped accepted sets A_i; published scoring path (canonical matcher + disclosed RNA alias).

### L.1 Accepted-set cardinality
- 20 units / 9 bidirectional pairs. Canonical |A_i| = 1 for **19 units**; |A_i| = 2 for **1 unit**:
  **T3VP_0003** (PAIR_TWIST1_HOXD10, miR-10b, direction up) accepts {inhibition, sponge_inhibition}.
  For this unit the inverse mapping is genuinely one-to-many.

### L.2 Exact vs accepted-set accuracy (%, pooled 480 unit-runs)
- Pooled: exact 36.0 vs accepted-set 65.6 → rescue gap 29.6 pp
  (rescued 142 unit-runs = 42 RNA-alias + 100 other-whitelist-synonym).
- Chain pass is identical under both layers by construction (60.6%); only joint moves (49.4%).

Per system (exact / accepted-set / rescue gap / joint pass):

| System | Exact | Accepted | Gap | Joint |
|---|---|---|---|---|
| GPT-6-Astra | 35.0 | 70.0 | +35.0 | 58.8 |
| Claude-Sonnet-5.5 | 30.0 | 45.0 | +15.0 | 35.0 |
| Gemini-3.8-Flash | 30.0 | 63.8 | +33.8 | 56.2 |
| GLM-5.3-Flash | 41.2 | 63.8 | +22.6 | 51.2 |
| Grok-4.6 | 25.0 | 60.0 | +35.0 | 53.8 |
| Biomni (tools) | 55.0 | 91.2 | +36.2 | 41.2 |

### L.3 Stratified by canonical cardinality

| Stratum | n (unit-runs) | Exact | Accepted | Chain | Joint |
|---|---|---|---|---|---|
| \|A_i\| = 1 (19 units) | 456 | 35.5 | 64.3 | 59.0 | 47.4 |
| \|A_i\| = 2 (T3VP_0003) | 24 | 45.8 | 91.7 | 91.7 | 87.5 |

The single multi-answer unit is essentially non-discriminative (91.7% acceptance); the strict one-to-one readout
is the |A_i| = 1 stratum.

### L.4 Identifiability map: (entity, direction) → accepted canonical set (14 combos, no conflicts)

| Entity (direction) | Units | Accepted canonical union |
|---|---|---|
| bhlhe40 (down) | T3VP_0002, 0018, 0020 | knockdown |
| miR-10b (down) | T3VP_0014 | overexpression |
| miR-10b (up) | T3VP_0003 | inhibition, sponge_inhibition |
| miR-181b (down) | T3VP_0001 | overexpression |
| miR-181b (up) | T3VP_0011 | inhibition |
| miR-210 (down) | T3VP_0010, 0019 | overexpression |
| miR-210 (up) | T3VP_0013, 0016 | inhibition |
| miR-451 (down) | T3VP_0017 | overexpression |
| miR-451 (up) | T3VP_0015 | genetic_knockout |
| NOTCH1 (down) | T3VP_0006 | knockdown |
| NOTCH1; TGF-beta/SMAD3 (up) | T3VP_0009 | combined_ligand_stimulation |
| PPARA (up) | T3VP_0004, 0005, 0012 | agonist_activation |
| SMAD3 (down) | T3VP_0007 | knockdown |
| SMAD4 (down) | T3VP_0008 | knockdown |

Every (entity, direction) maps to a single accepted canonical set → **no unit is unidentifiable from the visible
input given the labels**. Residual non-identifiability is method-level within an accepted class (siRNA vs shRNA
vs knockout; agonist vs overexpression) — already disclosed in Appendix B.6.

### L.5 Largest exact-vs-accepted gaps per unit (pooled 4 runs)

| Unit | Entity (dir) | \|A_i\| | Exact | Accepted | Gap |
|---|---|---|---|---|---|
| T3VP_0007 | SMAD3 (down) | 1 | 0.0 | 95.8 | 95.8 |
| T3VP_0008 | SMAD4 (down) | 1 | 0.0 | 95.8 | 95.8 |
| T3VP_0006 | NOTCH1 (down) | 1 | 0.0 | 91.7 | 91.7 |
| T3VP_0003 | miR-10b (up) | 2 | 45.8 | 91.7 | 45.8 |
| T3VP_0011 | miR-181b (up) | 1 | 50.0 | 95.8 | 45.8 |
| T3VP_0013 | miR-210 (up) | 1 | 50.0 | 95.8 | 45.8 |
| T3VP_0016 | miR-210 (up) | 1 | 54.2 | 91.7 | 37.5 |
| T3VP_0018 | BHLHE40 (down) | 1 | 0.0 | 37.5 | 37.5 |

Reading: T3VP_0006–0008 (0% exact → ~92–96% accepted) are pure whitelist-wording cases ("shRNA knockdown" vs
gold string); T3VP_0018 keeps a 37.5% ceiling even after canonicalization (real method confusion, e.g. knockout
vs knockdown wording). RNA-alias-rescued unit IDs: T3VP_0003, 0011, 0013, 0016.

---

## APPENDIX M — Pair-Level Statistical Robustness (Task 2)

Design: resampling unit = TF–gene pair (168 pairs; all units × all 4 runs of a pair move together). The 4 runs
are technical repeats of one protocol (temperature 0, relay serving not bit-deterministic) and are **never**
treated as independent biological replicates. B = 10,000, seed 20261017, percentile CIs.

### M.1 Points and 95% CIs

Chain pass (published pooled vs pair-weighted point / CI / width):

| System | Pooled (unit-run) | Pair-weighted point | 95% CI | Width |
|---|---|---|---|---|
| GPT-6-Astra | 84.7 | 86.9 | [82.2, 91.2] | 9.0 |
| Claude-Sonnet-5.5 | 79.4 | 83.9 | [79.0, 88.4] | 9.4 |
| Gemini-3.8-Flash | 79.0 | 82.2 | [77.7, 86.4] | 8.7 |
| GLM-5.3-Flash | 62.0 | 66.3 | [61.1, 71.2] | 10.1 |
| Grok-4.6 | 79.5 | 82.9 | [77.8, 87.7] | 9.9 |
| Biomni | 76.2 | 80.1 | [74.8, 85.0] | 10.3 |

Joint pass:

| System | Pooled | Pair-weighted point | 95% CI | Width |
|---|---|---|---|---|
| GPT-6-Astra | 84.2 | 86.3 | [81.5, 90.7] | 9.2 |
| Claude-Sonnet-5.5 | 79.3 | 83.7 | [78.9, 88.3] | 9.5 |
| Gemini-3.8-Flash | 78.9 | 82.0 | [77.5, 86.3] | 8.8 |
| GLM-5.3-Flash | 61.9 | 66.1 | [60.9, 71.1] | 10.2 |
| Grok-4.6 | 79.0 | 82.4 | [77.1, 87.2] | 10.1 |
| Biomni | 75.8 | 79.6 | [74.2, 84.6] | 10.4 |

All CIs span ≈9–10.5 pp; mid-field intervals overlap; GPT's lower bound and GLM's upper bound do not overlap.

### M.2 GPT − Claude, paired by pair (same resampled set per replicate)

| Metric | Point (pp) | 95% CI | P(diff > 0) |
|---|---|---|---|
| Chain pass | +3.1 | [+1.2, +5.2] | 0.9994 |
| Joint pass | +2.6 | [+0.9, +4.6] | 0.9986 |

### M.3 Ranking stability (chain pass; joint pass in parentheses)

- Observed pair-weighted ordering: GPT > Claude > Grok > Gemini > Biomni > GLM (same for joint).
- P(full ordering reproduced) = 53.5% (joint 48.8%); P(GPT first) = **99.95%** (joint 99.88%);
  mean Kendall τ = 0.749 (joint 0.756).

Adjacent-inversion probabilities:

| Inversion | Chain | Joint |
|---|---|---|
| Claude above GPT | 0.05% | 0.12% |
| Grok above Claude | 9.6% | 3.2% |
| Gemini above Grok | **22.6%** | **34.3%** |
| Biomni above Gemini | 10.5% | 7.7% |

Reading: extremes stable; **Grok/Gemini/Biomni mid-tier ordering is not resolved** (22–34% adjacent flips) —
describe as one tier, not a ranking.

### M.4 Study-level bootstrap (chain pass)

- Mapping rule: primary = lexicographically first identifier among the pair's sources (GSE else DOI).
- **31 studies / 168 pairs.** Top: GSE266489 = 99 pairs (58.9%!), GSE45822 = 10, GSE274688 = 7, GSE293567 = 4.
- **Concentration disclosure:** one study (GSE266489, the ZNF143 collection) carries 59% of pairs → tiny
  effective study sample, wide asymmetric CIs; reported for completeness, not as primary uncertainty.

| System | Point | 95% CI (study bootstrap) |
|---|---|---|
| GPT-6-Astra | 86.9 | [55.2, 96.7] |
| Claude-Sonnet-5.5 | 83.9 | [49.5, 95.1] |
| Gemini-3.8-Flash | 82.2 | [55.1, 90.6] |
| GLM-5.3-Flash | 66.3 | [25.5, 80.7] |
| Grok-4.6 | 82.9 | [44.9, 95.2] |
| Biomni | 80.1 | [39.5, 93.6] |

Same concentration documented from the label side in Appendix D.6 (ZNF143 = 99/193 units; chain pass 97.0% on
ZNF143 vs 55.5% elsewhere). Future versions should rebalance toward more independent studies.

### M.5 Summary
(i) ≈±5 pp pair-level uncertainty on every per-system rate. (ii) Tier boundaries robust: GPT above the field,
GLM below; four-system middle tier unordered. (iii) Study-level uncertainty dominated by one source collection —
disclosed, not hidden. (iv) Runs = protocol repeatability only, never biological replicates.

---

## Standing caveats (inside each appendix)
1. K measures judge-choice sensitivity, not correctness; blinded human adjudication remains open.
2. 4 runs = technical repeats; resampling is clustered at pair (and study) level only.
3. Task 3 = 20-unit targeted diagnostic subset (9 pairs); CIs wide by construction (±20 pp).

## Files & reproduction
```
sensitivity/
├── README.md                          # layer overview + repro
├── ALL_RESULTS_TEXT.md                # this document
├── K_judge_robustness/
│   ├── sample_design.json             # frozen sample (seed 20261017) + strata marginals
│   ├── packets/                       # 21 rejudge packets + manifests w/ original axes
│   ├── judgments/                     # raw Gemini outputs + parsed judgment TSVs (verbatim archived)
│   ├── outputs/K_METRICS.json, APPENDIX_K_judge_robustness.html
│   └── build_K_sample_and_packets.py / run_K_rejudge.py / compute_K_metrics.py / build_K_html.py
├── L_accepted_set/  compute_L.py → outputs/{L_ACCEPTED_SET.json, APPENDIX_L_accepted_set.html}
└── M_pair_bootstrap/ compute_M.py + build_M_html.py → outputs/{M_PAIR_BOOTSTRAP.json, APPENDIX_M_pair_robustness.html}

cd L_accepted_set   && python3 compute_L.py
cd M_pair_bootstrap && python3 compute_M.py && python3 build_M_html.py
cd K_judge_robustness && python3 build_K_sample_and_packets.py && python3 run_K_rejudge.py \
                       && python3 compute_K_metrics.py && python3 build_K_html.py
```
K cost: ~21 relay calls (batch = 40 rows, gemini-3.8-flash).
