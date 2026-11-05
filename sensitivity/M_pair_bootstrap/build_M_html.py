#!/usr/bin/env python3
"""Render APPENDIX_M_pair_robustness.html from M_PAIR_BOOTSTRAP.json."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "outputs"
S = json.load(open(OUT / "M_PAIR_BOOTSTRAP.json"))
SYSTEMS = ["GPT-6-Astra", "Claude-Sonnet-5.5", "Gemini-3.8-Flash",
           "GLM-5.3-Flash", "Grok-4.6", "Biomni"]

CSS = """<html><head><meta charset="utf-8"><title>Appendix M — Pair-Level Statistical Robustness</title><style>
body{font-family:'Times New Roman',serif;font-size:11pt;max-width:720px;margin:36px auto;color:#111;line-height:1.6;}
h1{font-size:13pt;} h2{font-size:11.5pt;margin:22px 0 6px;} h3{font-size:11pt;margin:14px 0 4px;color:#222;font-style:italic;}
p{margin:8px 0;text-align:justify;}
table{border-collapse:collapse;margin:12px auto;width:100%;}
th,td{border:1px solid #bbb;padding:4px 7px;font-size:9.5pt;text-align:center;}
th{background:#f2f2f2;} td:first-child{text-align:left;}
.fn{font-size:8.5pt;color:#555;margin:5px 0;line-height:1.4;text-align:left;}
code{font-family:Menlo,monospace;font-size:8.5pt;background:#f6f6f2;padding:0 3px;}
</style></head><body>"""

def boot_table(m, label):
    rows = ""
    for s in SYSTEMS:
        b = S["bootstrap"][m][s]
        pooled = S["published_pooled_unitrun"][f"{s}|{m}"]
        rows += (f"<tr><td>{s}</td><td>{pooled}</td><td>{b['point']}</td>"
                 f"<td>[{b['ci95'][0]}, {b['ci95'][1]}]</td><td>{b['width']}</td></tr>")
    return (f"<h3>Table M{1 if m == 'chain' else 2} | {label}: pass rate, pair-level cluster bootstrap "
            f"95% CI (%, seed {S['seed']}, B = {S['B']})</h3>"
            f"<table><tr><th>System</th><th>Published pooled (unit-run)</th><th>Pair-weighted point</th>"
            f"<th>95% CI (pair bootstrap)</th><th>CI width</th></tr>{rows}</table>")

g = S["gpt_minus_claude"]; rc = S["ranking"]["chain"]
flips = "".join(f"<tr><td>{k}</td><td>{round(100 * v, 1)}%</td></tr>"
                for k, v in rc["adjacent_flip_prob"].items())
study_rows = "".join(
    f"<tr><td>{s}</td><td>{S['study_level']['chain_bootstrap'][s]['point']}</td>"
    f"<td>[{S['study_level']['chain_bootstrap'][s]['ci95'][0]}, {S['study_level']['chain_bootstrap'][s]['ci95'][1]}]</td></tr>"
    for s in SYSTEMS)
top_studies = "; ".join(f"{d['study']} ({d['pairs']} pairs)" for d in S["study_level"]["pairs_per_study_top"][:3])

html = CSS + f"""
<h1>Appendix M — Pair-Level Statistical Robustness (Task 2)</h1>
<p><b>Status.</b> Post-freeze statistical addendum. No frozen value is modified; this appendix quantifies how the
Task 2 chain and joint pass rates behave when uncertainty is quantified at the correct level of the design.</p>

<h2>M.0 What is and is not a replicate here</h2>
<p>The 4 runs per system are <b>technical repeats of a single administration protocol</b> (temperature 0, prompts
byte-identical, serving through relay endpoints is not bit-deterministic). They quantify serving-level run-to-run
variability and are pooled as such in the main tables. They are <b>not independent biological replicates</b>, and
nowhere in this appendix are runs resampled as if they were independent experiments. The resampling unit is the
TF–gene pair: all units and all runs belonging to a pair move together in every bootstrap replicate. Task 2
contains {S['n_pairs']} pairs over {S['n_unit_runs']} unit-runs (6 systems × 4 runs).</p>

<h2>M.1 Bootstrap confidence intervals over the 168 pairs</h2>
<p>Estimator per system: the unweighted mean over pairs of the per-pair pass rate (a pair's rate averages its
1–2 units × 4 runs). Pair-weighted points sit 2–4.5 pp above the published unit-run-pooled values because the
latter weight the multi-unit pairs (and the 99-pair ZNF143 collection) by their unit-run counts.
B = {S['B']}; percentile CIs; seed {S['seed']} disclosed for exact reproduction.</p>
{boot_table('chain', 'Chain pass (all five adjudication axes)')}
{boot_table('joint', 'Joint pass (direction correct AND chain pass)')}
<p class="fn">Reading: every per-system 95% CI spans ≈9–10.5 pp. Systems in the middle of the field
(Claude-Sonnet-5.5, Grok-4.6, Gemini-3.8-Flash, Biomni) have overlapping intervals; GPT-6-Astra's lower bound and
GLM-5.3-Flash's upper bound do not overlap.</p>

<h2>M.2 GPT-6-Astra vs Claude-Sonnet-5.5, paired by pair</h2>
<p>The difference is computed within each replicate on the same resampled pair set (paired by construction).</p>
<table>
<tr><th>Metric</th><th>Point (pp)</th><th>95% CI</th><th>P(diff &gt; 0)</th></tr>
<tr><td>Chain pass</td><td>{g['chain']['point']}</td><td>[{g['chain']['ci95'][0]}, {g['chain']['ci95'][1]}]</td><td>{g['chain']['p_diff_gt_0']}</td></tr>
<tr><td>Joint pass</td><td>{g['joint']['point']}</td><td>[{g['joint']['ci95'][0]}, {g['joint']['ci95'][1]}]</td><td>{g['joint']['p_diff_gt_0']}</td></tr>
</table>
<p>At pair level, GPT-6-Astra's chain advantage over Claude-Sonnet-5.5 is positive in
{round(100 * g['chain']['p_diff_gt_0'], 1)}% of replicates with a CI excluding zero, so the headline pairing
(GPT first) is robust; the size of the gap (≈3 pp) is small relative to the CI widths in M.1.</p>

<h2>M.3 Ranking stability</h2>
<p>Per replicate the six systems are ranked by pair-weighted chain pass. Over B = {S['B']} replicates:</p>
<table>
<tr><th>Quantity</th><th>Value</th></tr>
<tr><td>Observed point ordering (pair-weighted)</td><td>{' &gt; '.join(rc['published_order'])}</td></tr>
<tr><td>Probability the full ordering is reproduced</td><td>{round(100 * rc['p_reproduce_published'], 1)}%</td></tr>
<tr><td>P(GPT-6-Astra ranked first)</td><td>{round(100 * rc['p_gpt_first'], 1)}%</td></tr>
<tr><td>Mean Kendall τ vs the observed ordering</td><td>{rc['mean_kendall_tau_vs_published']}</td></tr>
</table>
<h3>Table M3 | Probability of each published-adjacent inversion (chain pass)</h3>
<table><tr><th>Inversion (relative to the point ordering)</th><th>Frequency</th></tr>{flips}</table>
<p class="fn">Reading: the extremes are stable — GPT-6-Astra is first and GLM-5.3-Flash last in the overwhelming
majority of replicates. The middle of the ordering (Claude-Sonnet-5.5 / Grok-4.6 / Gemini-3.8-Flash / Biomni,
spanning ≈80–84% pair-weighted) is not reliably ordered by this benchmark and should be described as a tier
rather than a ranking.</p>

<h2>M.4 Study-level bootstrap</h2>
<p>Pairs were mapped to their primary source study from the evaluator-only provenance inventory
(GSE accession, else DOI; rule: {S['study_level']['mapping_rule']}). This yields
{S['study_level']['n_studies']} studies over {S['n_pairs']} pairs — dominated by {top_studies}.</p>
<p><b>Concentration disclosure.</b> One study (GSE266489, the ZNF143 collection) contributes
<b>99 of {S['n_pairs']} pairs (58.9%)</b>. Study-level resampling therefore has a small effective sample: the CIs
below are wide, asymmetric, and mostly reflect the uncertainty of that single collection. They are reported for
completeness, not as the primary uncertainty statement.</p>
<h3>Table M4 | Chain pass under study-level cluster bootstrap (31 studies)</h3>
<table><tr><th>System</th><th>Point (%)</th><th>95% CI (study bootstrap)</th></tr>{study_rows}</table>
<p class="fn">Interpretation: the benchmark's pair diversity — and therefore its strongest current evidence —
is concentrated in one large, internally homogeneous collection of easy (direct-cis, ZNF143) pairs. This is the
same concentration documented from the label side in Appendix D.6 (ZNF143 = 99/193 units; chain pass 97.0% on
ZNF143 vs 55.5% elsewhere). Future benchmark versions should rebalance toward more independent studies.</p>

<h2>M.5 Summary</h2>
<p>(i) All per-system pass rates carry ≈±5 pp pair-level uncertainty; claims should not be made at finer
resolution. (ii) The two tier boundaries — GPT-6-Astra above the field, GLM-5.3-Flash below it — are robust;
the four-system middle tier is not ordered by this benchmark. (iii) Study-level uncertainty is dominated by a
single source collection and is disclosed rather than hidden. (iv) The four runs per system quantify protocol
repeatability only and are never treated as biological replicates.</p>
</body></html>"""

(OUT / "APPENDIX_M_pair_robustness.html").write_text(html, encoding="utf-8")
print("WROTE", OUT / "APPENDIX_M_pair_robustness.html")
