"""Verify current-package and frozen-experiment SHA-256 manifests."""
import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def verify(root, manifest):
    failures = []
    count = 0
    for line in manifest.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        name = name.lstrip('*').removeprefix('./')
        path = root / name
        if not path.is_file():
            failures.append(f'Missing: {name}')
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            failures.append(f'Hash mismatch: {name}')
        count += 1
    if failures:
        raise SystemExit('\n'.join(failures))
    return count

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--frozen-only', action='store_true')
    args = parser.parse_args()
    manifests = ['FROZEN_ARTIFACTS.sha256'] if args.frozen_only else ['MANIFEST.sha256', 'FROZEN_ARTIFACTS.sha256']
    for name in manifests:
        count = verify(args.root, args.root / name)
        print(f'{name}: {count} files verified')

if __name__ == '__main__':
    main()
