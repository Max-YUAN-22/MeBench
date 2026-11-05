# Reproducing MeBench

All supported commands below use archived data and make no model calls. They do not change the frozen runs or judgments. Python 3.12+ is needed for the pinned numerical environment; the core audit uses only the standard library.

## Whole analysis

```bash
python3 scripts/verify_integrity.py
python3 scripts/reproduce_all.py --core-only
python3 -m pip install -r requirements.txt
python3 scripts/reproduce_all.py --figures
```

Outputs go to `build/reproduction/`, including individual logs and `reproduction_report.json`. Numerical intervals use the exact seeds, number of draws and estimands documented in [SENSITIVITY.md](SENSITIVITY.md). BLAS/platform differences can affect only final floating-point digits; displayed values and archived input identities are checked independently.

## Individual analyses

| Analysis | Command |
|---|---|
| Record audit and 36 main-table cells | `python3 scripts/reproduce_release.py --output build/release` |
| Mechanism modules and strict shared failures | `python3 scripts/analyze_dependency_modules.py --output build/modules` |
| Task 3 accepted sets | `python3 scripts/analyze_task3_accepted_sets.py --output build/accepted_sets` |
| Earlier independent-agent pilot, replay archived judgments | `python3 scripts/analyze_judge_robustness.py --output build/judge_pilot` |
| Larger Gemini reassessment, audit original/raw/parsed calls | `python3 scripts/audit_team_sensitivity.py --root . --source sensitivity --output build/judge_gemini` |
| Primary Task 2 pair/source bootstrap | `python3 scripts/cluster_bootstrap.py --output build/bootstrap_primary` |
| Corrected equal-pair chain/joint sensitivity | `python3 scripts/compute_M_corrected.py --root . --output build/bootstrap_pair_equal` |
| Regenerate pilot sampling packet, without judging | `python3 scripts/prepare_judge_sample.py --output build/pilot_sample` |

The pilot replay defaults to `analysis/robustness/`. The Gemini audit reads `sensitivity/K_judge_robustness/`; original packet IDs disclose system identity. The original author packet builder expects the author workspace and is archived for provenance, not a supported fresh-run entry point. The optional relay runner requires explicit environment configuration and is not called by any supported reproduction command.

## Manuscript

The complete paper is `paper/manuscript/main.pdf`; source is `paper/manuscript/main.tex`. With a LaTeX distribution containing the listed packages:

```bash
cd paper/manuscript
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

The current PDF uses a separate title/abstract page numbered 1, ten main-text pages numbered 2–11, references 12–13 and supplementary pages S1–S16. Historical `paper/figs/` files are retained; the current source uses its own `figs/` directory.

## Scoring new predictions

Use the released scorer documented in `evaluation_v3.7.0/README.md`. Keep evaluator-only reference fields out of model inputs. Applying the separate RNA amendment and obtaining new five-axis judgments are distinct steps; running the answer scorer alone does not reproduce full-chain or joint metrics.

## Manifests

`python3 scripts/verify_integrity.py` checks both the current package and the immutable experimental subset. Maintainers can use `python3 scripts/generate_manifest.py` after an intentional repository change; it verifies frozen artifacts before updating the current manifest. Generated `build/` outputs, local environments, credentials and caches are excluded.
