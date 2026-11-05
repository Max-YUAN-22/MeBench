# MeBench

**Benchmarking biological mechanism reasoning in language models through TF-to-gene regulation.**

MeBench evaluates whether a model identifies experimentally supported regulatory dependencies and uses the relevant components and functional roles to explain perturbation responses. It combines mechanism classification, forward perturbation reasoning and inverse intervention reasoning.

[Paper](paper/manuscript/main.pdf) · [Supplement (A–M)](paper/supplement/MeBench_appendices_A-M.pdf) · [Data and results index](docs/SUPPLEMENT_INDEX.md) · [Reproduction guide](docs/REPRODUCIBILITY.md)

## Benchmark and released records

| Task | Evaluation target | Units | Distinct TF–gene pairs | Archived responses |
|---|---|---:|---:|---:|
| 1 | Mechanism classification | 171 | 171 | 4,104 |
| 2 | Forward direction and mechanistic explanation | 193 | 168 | 4,632 |
| 3 | Inverse intervention and mechanistic explanation | 20 | 9 | 480 |

Six systems were evaluated in four recorded runs. Runs are repeated administrations of the protocol, not independent biological replicates. Biomni has tool access; the other five systems use closed-book prompts.

The experimental inputs, reference annotations, original predictions, original judgments and published primary results are preserved. Post-freeze analyses are separate derived artifacts. The release includes evaluator-only references for inspection; those fields must remain withheld when administering the corresponding benchmark task.

## Quick start

Use Python 3.12 or newer for the complete analysis environment.

```bash
git clone https://github.com/Max-YUAN-22/MeBench.git
cd MeBench
python3 scripts/verify_integrity.py
python3 scripts/reproduce_all.py --core-only
```

The core command requires only the Python standard library. It checks all 9,216 archived records, recomputes the 36 main-table values, and reproduces module, accepted-set and archived judge analyses. It makes **no model API calls**.

For bootstrap analyses and supplementary figures:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/reproduce_all.py --figures
```

Logs and a machine-readable report are written to `build/reproduction/`. [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) documents each individual entry point and manuscript compilation.

## Repository layout

| Path | Contents |
|---|---|
| [`benchmark/`](benchmark/) | Frozen task inputs, evaluator-only labels/metadata, scorer and templates |
| [`prompts/`](prompts/) | Released model prompts and prompt checksums |
| [`runs/`](runs/) | Original responses, predictions, judgments and three consolidated MASTER tables |
| [`results/`](results/) | Published primary values and archived aggregate statistics |
| [`scoring_amendment/`](scoring_amendment/) | Separately disclosed RNA matching amendment |
| [`analysis/release_audit/`](analysis/release_audit/) | Recomputed record audit, main table and diagnostic summaries |
| [`analysis/mechanism_modules/`](analysis/mechanism_modules/) | Module-level records, contrasts, shared failures and adjudication flags |
| [`analysis/robustness/`](analysis/robustness/) | Independent-agent pilot, Task 3 accepted sets and primary cluster bootstrap arrays/tables |
| [`sensitivity/`](sensitivity/) | Author-supplied Gemini reassessment and pair-equal analyses, with raw packets and reviewed corrections |
| [`paper/manuscript/`](paper/manuscript/) | Current LaTeX source, figures, bibliography and complete PDF |
| [`paper/supplement/`](paper/supplement/) | Standalone supplementary PDF; underlying records are indexed in docs/SUPPLEMENT_INDEX.md |
| [`scripts/`](scripts/) | Supported reproduction scripts; original workspace-dependent scripts are in `scripts/legacy/` |
| [`docs/`](docs/) | Data, scoring, provenance, supplement mapping and release notes |

The [data and results index](docs/SUPPLEMENT_INDEX.md) maps every appendix to its underlying records. Historical supplementary reports are kept separately in [`archive/supplement/`](archive/supplement/).

## Interpretation and validation boundaries

- Mechanism references describe specific experimental contexts. The compressed task inputs do not establish universal regulatory mechanisms or unique inverse interventions.
- Task 2/3 headline scores are **joint** answer-and-chain metrics. Their protocol-specific F1 implementations differ from ordinary answer-only macro-F1; exact definitions are in [SCORING.md](docs/SCORING.md).
- All authors discussed the results, and author spot checks covered all five scoring dimensions. Chain judgments remain subject to independent blinded validation; automated agreement measures judge/protocol sensitivity, not biological correctness.
- Task 3 is a targeted 20-unit subset. Only one unit has two annotated accepted labels; singleton sets do not prove unique biological identifiability.
- Source studies are concentrated. Cluster intervals condition on the frozen labels, judgments and observed runs; small rank differences require care.

The [sensitivity guide](docs/SENSITIVITY.md) distinguishes the larger Gemini reassessment, the smaller independent-agent pilot, primary unit-weighted joint BAcc and secondary equal-pair chain/joint pass rates.

## Integrity and provenance

`MANIFEST.sha256` covers this repository snapshot. `FROZEN_ARTIFACTS.sha256` checks 636 unchanged original files against the original release. `MANIFEST.original.sha256` retains the full historical manifest; some documentation and script paths have since changed, so it is a provenance record rather than the current package verifier.

See [provenance](docs/PROVENANCE.md) for the original snapshot and [change history](CHANGELOG.md) for subsequent analyses.

## Citation and licenses

Citation metadata and the complete author list are in [CITATION.cff](CITATION.cff). No publication DOI is assigned in this package.

Code is licensed under [MIT](LICENSE). Benchmark data and annotations are licensed under [CC BY 4.0](DATA_LICENSE.md). Third-party publication content remains subject to its original rights.
