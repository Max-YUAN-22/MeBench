"""Regenerate the package manifest after verifying immutable experimental files."""
import hashlib
from pathlib import Path
from verify_integrity import verify

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', '.venv', 'venv', 'build', '__pycache__', '.ipynb_checkpoints'}
SKIP_SUFFIXES = {'.pyc', '.pyo', '.aux', '.log', '.out', '.blg', '.fls', '.gz.tmp'}

def main():
    verify(ROOT, ROOT / 'FROZEN_ARTIFACTS.sha256')
    records = []
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if not path.is_file() or any(x in SKIP_DIRS for x in rel.parts):
            continue
        if str(rel) == 'MANIFEST.sha256' or path.name == '.DS_Store' or path.suffix in SKIP_SUFFIXES:
            continue
        records.append(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + rel.as_posix())
    (ROOT / 'MANIFEST.sha256').write_text('\n'.join(records) + '\n', encoding='utf-8')
    print(f'Wrote MANIFEST.sha256 for {len(records)} files')

if __name__ == '__main__':
    main()
