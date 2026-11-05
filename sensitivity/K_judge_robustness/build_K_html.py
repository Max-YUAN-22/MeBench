#!/usr/bin/env python3
"""Render APPENDIX_K_judge_robustness.html from K_METRICS.json."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
S = json.load(open(OUT / "K_METRICS.json"))
D = json.load(open(HERE / "sample_design.json"))
AXES = [("mechanism_correct", "Mechanism"), ("mediator_correct", "Mediator"),
        ("causal_role_order_correct", "Causal order"),
        ("intervention_outcome_link_correct", "Outcome link"),
        ("no_material_contradiction", "No contradiction")]

CSS = """<html><head><meta charset="utf-8"><title>Appendix K — Automated Judge Robustness and Adjudication Sensitivity</title><style>
body{font-family:'Times New Roman',serif;font-size:11pt;max-width:720px;margin:36px auto;color:#111;line-height:1.6;}
h1{font-size:13pt;} h2{font-size:11.5pt;margin:22px 0 6px;} h3{font-size:11pt;margin:14px 0 4px;color:#222;font-style:italic;}
p{margin:8px 0;text-align:justify;}
table{border-collapse:collapse;margin:12px auto;width:100%;}
th,td{border:1px solid #bbb;padding:4px 7px;font-size:9.5pt;text-align:center;}
th{background:#f2f2f2;} td:first-child{text-align:left;}
.fn{font-size:8.5pt;color:#555;margin:5px 0;line-height:1.4;text-align:left;}
code{font-family:Menlo,monospace;font-size:8.5pt;background:#f6f6f2;padding:0 3px;}
</style></head><body>"""

AX_SHORT = {k: v for k, v in AXES}

def axis_table(task):
    t = S[task]["axes"]
    rows = "".join(
        f"<tr><td>{AX_SHORT[ax]}</td><td>{t[ax]['n']}</td><td>{t[ax]['agreement']}</td>"
        f"<td>{t[ax]['kappa']}</td><td>{t[ax]['orig_pos_rate']}</td><td>{t[ax]['new_pos_rate']}</td>"
        f"<td>{t[ax]['orig1_new0']}</td><td>{t[ax]['orig0_new1']}</td></tr>"
        for ax, _ in AXES)
    c = S[task]["chain"]
    rows += (f"<tr><td><b>Chain pass (all five)</b></td><td>{c['n_valid']}</td><td><b>{c['agreement']}</b></td>"
             f"<td><b>{c['kappa']}</b></td><td>{c['orig_pass_rate']}</td><td>{c['new_pass_rate']}</td>"
             f"<td>{c['pass_to_fail']}</td><td>{c['fail_to_pass']}</td></tr>")
    return rows

def sys_rows(task, with_rank):
    per = S[task]["per_system"]
    rk = S[task]["ranking"]
    order_n = {s: i + 1 for i, s in enumerate(rk["order_rejudge"])}
    order_o = {s: i + 1 for i, s in enumerate(rk["order_original_judge"])}
    head_rank = "<th>Rank (orig → re)</th>" if with_rank else ""
    body = ""
    for s in per:
        rank_cell = (f"<td>{order_o[s]} → {order_n[s]}</td>" if with_rank else "")
        body += (f"<tr><td>{s}</td><td>{per[s]['n']}</td><td>{per[s]['orig_pass']}</td>"
                 f"<td>{per[s]['new_pass']}</td><td>{round(per[s]['new_pass']-per[s]['orig_pass'],1)}</td>"
                 f"<td>{per[s]['fail_to_pass']}</td><td>{per[s]['pass_to_fail']}</td>{rank_cell}</tr>")
    head = ("<tr><th>System</th><th>n</th><th>Orig pass (%)</th><th>Rejudge pass (%)</th>"
            "<th>Δ (pp)</th><th>fail→pass</th><th>pass→fail</th>" + head_rank + "</tr>")
    return head + body

def band(k):
    if k is None: return ""
    a = abs(k)
    return ("almost perfect" if a >= .81 else "substantial" if a >= .61 else
            "moderate" if a >= .41 else "fair" if a >= .21 else "slight" if a >= 0 else "poor")

t2, t3 = S["task2"], S["task3"]
sp2, sp3 = t2["self_preference"], t3["self_preference"]
rk3 = t3["ranking"]
gem_fr, oth_fr = sp2["gemini_fail_rows"], sp2["other_fail_rows"]
gem_fr3, oth_fr3 = sp3["gemini_fail_rows"], sp3["other_fail_rows"]

html = CSS + f"""
<h1>Appendix K — Automated Judge Robustness and Adjudication Sensitivity</h1>
<p><b>Status.</b> Post-freeze sensitivity addendum. No frozen value, judgment file, or main-table number is
modified. This appendix re-adjudicates a fixed, seed-disclosed sample of the frozen reasoning chains with a
second automated judge and reports how much the five-axis calls — and anything downstream of them — move.</p>

<h2>K.1 Design</h2>
<p><b>Sample.</b> Task 2: {t2['n_sampled']} unit-runs, stratified by system (6 × 60) and by original chain
outcome (30 pass / 30 fail per system), with the fail stratum quota-filled to guarantee coverage of each failed
axis. Task 3: full enumeration of all {t3['n_sampled']} unit-runs. Sampling seed {D['seed']}; the full sample
list is frozen in <code>sample_design.json</code>. Parsed coverage under the second judge:
Task 2 {t2['parse_coverage']}% ({t2['n_parsed']}/{t2['n_sampled']}), Task 3 {t3['parse_coverage']}%.</p>
<p><b>Second judge.</b> {S['judge']} — a system that never served as a judge anywhere in the frozen pipeline
(the frozen judges were GPT-6-Astra for five systems and Claude-Sonnet-5.5 for GPT-6-Astra). The adjudicator
instructions are byte-identical to the shipped rubric, and each sampled row is presented with the same content
the original judge saw (input, prediction, reasoning, evaluator-only construction fields). Row keys are
<code>unit_id@system@run</code> composites; temperature 0.</p>
<p><b>Scope caveat (important).</b> This experiment quantifies <i>sensitivity to the choice of automated
judge</i>. It cannot establish which judge's calls are biologically correct: the five adjudication axes have no
gold standard beyond the evaluator-only construction fields shown to both judges. Agreement here is a property
of the pair of judges, not a validation of either. The blinded human adjudication of the frozen judgments
(Appendix B.5) remains the open validation step for correctness.</p>

<h2>K.2 Axis-wise agreement</h2>
<p>Disagreement is strongly structured: the three construct-matching axes (mechanism, mediator, causal order)
agree at 92–97% with near-perfect κ on both tasks, while the two interpretive axes (outcome link,
no-material-contradiction) carry essentially all of the disagreement.</p>
<h3>Table K1 | Task 2 — per-axis agreement, Cohen's κ, and confusion (n = {t2['n_parsed']})</h3>
<table><tr><th>Axis</th><th>n</th><th>Agreement (%)</th><th>Cohen's κ</th><th>Orig + rate (%)</th>
<th>Rejudge + rate (%)</th><th>orig 1 → re 0</th><th>orig 0 → re 1</th></tr>
{axis_table('task2')}</table>
<p class="fn">κ bands (Landis–Koch): mechanism {band(t2['axes']['mechanism_correct']['kappa'])};
mediator {band(t2['axes']['mediator_correct']['kappa'])}; causal order {band(t2['axes']['causal_role_order_correct']['kappa'])};
outcome link {band(t2['axes']['intervention_outcome_link_correct']['kappa'])};
no-contradiction {band(t2['axes']['no_material_contradiction']['kappa'])};
chain gate {band(t2['chain']['kappa'])}. Confusion columns are row counts.</p>

<h3>Table K2 | Task 3 — per-axis agreement, Cohen's κ, and confusion (n = {t3['n_parsed']})</h3>
<table><tr><th>Axis</th><th>n</th><th>Agreement (%)</th><th>Cohen's κ</th><th>Orig + rate (%)</th>
<th>Rejudge + rate (%)</th><th>orig 1 → re 0</th><th>orig 0 → re 1</th></tr>
{axis_table('task3')}</table>

<h2>K.3 Pass-rate difference under the second judge</h2>
<p>On the identical sample, the five-axis chain pass rate moves from
{t2['chain']['orig_pass_rate']}% → {t2['chain']['new_pass_rate']}% on Task 2
(Δ = {t2['chain']['delta']} pp; {t2['chain']['fail_to_pass']} fail→pass vs
{t2['chain']['pass_to_fail']} pass→fail) and from
{t3['chain']['orig_pass_rate']}% → {t3['chain']['new_pass_rate']}% on Task 3
(Δ = {t3['chain']['delta']} pp; {t3['chain']['fail_to_pass']} fail→pass vs
{t3['chain']['pass_to_fail']} pass→fail). Both shifts are small relative to the between-tier system gaps that
carry the paper's claims (e.g. GLM-5.3-Flash sits ≈20 pp below the field), but are the same order of magnitude
as the spacing inside the mid-field tier — so judge choice adds uncertainty exactly where Appendix M already
shows the ordering is not resolved by pair resampling.</p>

<h2>K.4 Model ranking stability</h2>
<p><b>A design constraint first.</b> The Task 2 sample is balanced by construction — every system contributes
exactly 30 original passes and 30 original fails — so per-system chain-pass <i>levels</i> on this sample are
pinned at ≈50% regardless of judge, and <b>the Task 2 sample cannot support any ranking claim</b>. Ranking
stability is therefore assessed (i) on the Task 3 full enumeration, where levels are unmanipulated, and
(ii) at the population level in Appendix M (pair-level bootstrap).</p>
<h3>Table K3 | Task 2 — per-system chain pass on the identical sample (levels pinned by design; deltas only)</h3>
<table>{sys_rows('task2', with_rank=False)}</table>
<p class="fn">Δ columns are informative (judge leniency per system); the pass-rate levels are not.</p>
<h3>Table K4 | Task 3 (full enumeration, 480 unit-runs) — per-system chain pass under both judges</h3>
<table>{sys_rows('task3', with_rank=True)}</table>
<p class="fn">Kendall τ between orderings = {rk3['kendall_tau']}. The bottom system (Biomni) is unchanged; the
top-two adjacency (GPT-6-Astra / Gemini-3.8-Flash, ≈3.7 pp apart) inverts under the second judge. With 80 rows
per system this adjacency is not resolved by the enumeration — consistent with Appendix M, which shows the
population-level ordering has strong support for GPT-6-Astra first (P ≈ 99.9% over pair resamples) and no
reliable ordering inside the mid-field tier.</p>

<h2>K.5 Self-preference check</h2>
<p>The second judge ({S['judge']}) is itself one of the six evaluated systems (its frozen outputs were judged by
GPT-6-Astra, never by itself). If the replacement judge favored its own answers, fail→pass flipping would
concentrate on Gemini-origin rows.</p>
<table>
<tr><th>Row group</th><th>Fail rows (T2)</th><th>fail→pass (T2)</th><th>Flip rate (T2)</th>
<th>Fail rows (T3)</th><th>fail→pass (T3)</th><th>Flip rate (T3)</th></tr>
<tr><td>Gemini-origin rows</td><td>{gem_fr}</td><td>{sp2['gemini_f2p']}</td>
    <td><b>{round(100 * sp2['gemini_f2p'] / gem_fr, 1)}%</b></td>
    <td>{gem_fr3}</td><td>{sp3['gemini_f2p']}</td>
    <td><b>{round(100 * sp3['gemini_f2p'] / gem_fr3, 1)}%</b></td></tr>
<tr><td>Other systems' rows</td><td>{oth_fr}</td><td>{sp2['other_f2p']}</td>
    <td>{round(100 * sp2['other_f2p'] / oth_fr, 1)}%</td>
    <td>{oth_fr3}</td><td>{sp3['other_f2p']}</td>
    <td>{round(100 * sp3['other_f2p'] / oth_fr3, 1)}%</td></tr>
</table>
<p>There <b>is</b> a self-preference signal: on Task 2, {sp2['gemini_f2p']} of the {t2['chain']['fail_to_pass']}
fail→pass flips ({round(100 * sp2['gemini_f2p'] / t2['chain']['fail_to_pass'])}%) fall on Gemini-origin rows,
whose flip rate ({round(100 * sp2['gemini_f2p'] / gem_fr, 1)}%) is far above the other systems'
({round(100 * sp2['other_f2p'] / oth_fr, 1)}%); the pattern repeats, attenuated, on Task 3
({round(100 * sp3['gemini_f2p'] / gem_fr3, 1)}% vs {round(100 * sp3['other_f2p'] / oth_fr3, 1)}%).
Per-axis mean agreement is also slightly higher on Gemini-origin rows
(T2 {sp2['axis_agreement_gemini_rows']}% vs {sp2['axis_agreement_other_rows']}%;
T3 {sp3['axis_agreement_gemini_rows']}% vs {sp3['axis_agreement_other_rows']}%).
This is direct evidence that automated judges are not exchangeable, and it is the empirical justification for
two frozen-pipeline choices: the original design used <i>cross-family</i> judging (a model never judged its own
outputs), and chain values remain preliminary pending blinded human adjudication.</p>

<h2>K.6 Summary</h2>
<p>(i) The construct-matching axes (mechanism, mediator, causal order) are robust to the choice of automated
judge: 92–97% agreement, κ 0.77–0.94 on both tasks; disagreement concentrates in the two interpretive axes
(outcome link, no-contradiction). (ii) Aggregate chain-pass rates shift by {abs(t2['chain']['delta'])} pp (T2)
and {abs(t3['chain']['delta'])} pp (T3) under the replacement judge — small against between-tier gaps, but
comparable to mid-tier spacing, reinforcing the tier (rather than ranking) reading of the mid-field from
Appendix M. (iii) The Task 3 enumeration reproduces the bottom rank and leaves only the top-two adjacency
unresolved. (iv) A judge self-preference signal is detectable and is disclosed. (v) Per the scope caveat in
K.1, these results establish sensitivity to judge choice, not correctness of any judge; the blinded human
adjudication remains the open validation step.</p>
</body></html>"""

(OUT / "APPENDIX_K_judge_robustness.html").write_text(html, encoding="utf-8")
print("WROTE", OUT / "APPENDIX_K_judge_robustness.html")
