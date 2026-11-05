"""Reproduce archived release audits and sensitivity analyses without model calls."""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/reproduction')
    parser.add_argument('--core-only', action='store_true', help='Standard-library audits, modules, accepted sets and both archived judge analyses only.')
    parser.add_argument('--figures', action='store_true', help='Also regenerate the three supplementary figure assets.')
    args = parser.parse_args()
    if args.core_only and args.figures:
        parser.error('--figures requires the full analysis; omit --core-only')
    if (not args.core_only or args.figures) and importlib.util.find_spec('numpy') is None:
        raise SystemExit('Install requirements.txt, or use --core-only for the standard-library checks.')
    if args.figures and importlib.util.find_spec('matplotlib') is None:
        raise SystemExit('Figure reproduction requires requirements.txt.')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    commands = [
        ('integrity', ['verify_integrity.py']),
        ('release', ['reproduce_release.py', '--output', str(out / 'release')]),
        ('modules', ['analyze_dependency_modules.py', '--output', str(out / 'modules')]),
        ('accepted_sets', ['analyze_task3_accepted_sets.py', '--output', str(out / 'accepted_sets')]),
        ('judge_pilot', ['analyze_judge_robustness.py', '--output', str(out / 'judge_pilot')]),
        ('judge_gemini', ['audit_team_sensitivity.py', '--root', str(ROOT), '--source', str(ROOT / 'sensitivity'), '--output', str(out / 'judge_gemini')]),
    ]
    if not args.core_only:
        commands += [
            ('bootstrap_primary', ['cluster_bootstrap.py', '--output', str(out / 'bootstrap_primary')]),
            ('bootstrap_pair_equal', ['compute_M_corrected.py', '--root', str(ROOT), '--output', str(out / 'bootstrap_pair_equal')]),
        ]
    if args.figures:
        commands += [
            ('figures_modules', ['render_revision_figures.py', '--audit', str(out / 'release/independent_audit.json'), '--modules', str(out / 'modules/claim_audit.json'), '--output', str(out / 'figures')]),
            ('figure_intervals', ['render_cluster_figure.py', '--analysis', str(out / 'bootstrap_primary/cluster_bootstrap_analysis.json'), '--output', str(out / 'figures')]),
        ]
    completed = []
    for label, command in commands:
        path = ROOT / 'scripts' / command[0]
        print(f'Running {label}...', flush=True)
        with (out / f'{label}.log').open('w', encoding='utf-8') as log:
            result = subprocess.run([sys.executable, str(path), *command[1:]], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise SystemExit(f'{label} failed; inspect {out / (label + ".log")}')
        completed.append(label)
    audit = json.loads((out / 'release/independent_audit.json').read_text())
    differences = json.loads((out / 'release/main_table_discrepancies.json').read_text())
    assert audit['master_rows_verified_against_archived_predictions_and_axes'] == 9216
    assert not differences, differences
    report = dict(status='passed', completed=completed, original_records_verified=9216, main_table_discrepancies=differences, model_API_calls=0, biological_or_human_validation=False)
    (out / 'reproduction_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Passed {len(completed)} stages; 9,216 records checked; 36 main-table cells reproduced. No model calls.')
    print(f'Report: {out / "reproduction_report.json"}')

if __name__ == '__main__':
    main()
