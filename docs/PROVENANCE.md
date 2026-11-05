# Provenance and artifact status

Original frozen repository commit: `d282d75516d5a77a4bca5680037956354828369c`.

## Preserved experimental layer

`FROZEN_ARTIFACTS.sha256` is the subset of the original manifest covering `evaluation_v3.7.0/`, `prompts/`, `runs/`, `results/`, `scoring_amendment/` and `examples/`. All 636 files are retained byte-for-byte at the same paths. Four repeated administrations of six systems yield 9,216 consolidated responses. The original main table is preserved.

`MANIFEST.original.sha256` records the full earlier snapshot. Some documentation and script locations have intentionally changed, so running it directly against the updated layout is not the current integrity check. `MANIFEST.sha256` covers the updated repository package; `scripts/verify_integrity.py` verifies both the package and frozen subset.

## Derived layer

Portable audits recompute the published table and inspect original predictions/axis calls. Mechanism-module analyses trace examples to their biological sources without changing labels. Post-freeze adjudication and bootstrap results are separately archived; they do not overwrite primary scores.

The author supplied an additional sensitivity folder with sample design, 21 Gemini packet batches, raw replies, parsed calls and L/M scripts/outputs. `sensitivity/IMPORT_PROVENANCE.json` preserves original file hashes. The copied relay runner has no embedded credential fallback or fixed endpoint. No model calls were made while auditing that supplied folder. Independently recomputed metrics and correction notes are under `sensitivity/reviewed/`.

The earlier independent-agent pilot is preserved in `analysis/robustness/`, including its actual runtime/configuration, sampling, packets and raw calls. Its interface differs from the Gemini reassessment; their differing results are not an isolated model-identity effect.

## Current and historical documents

- Current manuscript: `paper/manuscript/main.pdf` and source.
- Current standalone supplement: `paper/supplement/MeBench_appendices_A-M.pdf`.
- Current appendix-to-data mapping: `docs/SUPPLEMENT_INDEX.md` and `analysis/supplement_catalogue.tsv`.
- Historical HTML under `paper/supplement/`, original aggregate outputs and `scripts/legacy/` are retained as archives. Some use earlier metrics or conventions; use the current scoring and sensitivity guides for interpretation.
- Chinese local editing/audit notes under `docs/review/` describe the author-review history and may refer to earlier paths or publication status.

Artifact consistency, reproducible statistics and biologically valid annotations are different checks. The package has not completed blinded expert validation of all mechanism-chain judgments, an exhaustive literature survey or controlled training experiments. Relay model identity is recorded as configured, not independently verified against a provider checkpoint.
