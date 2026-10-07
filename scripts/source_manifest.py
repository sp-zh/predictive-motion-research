#!/usr/bin/env python3
"""Hash source/config files without traversing credentials or build caches."""
import argparse
import hashlib
from pathlib import Path


def source_files(root):
    """Return the common manifest/export allowlist in stable path order."""
    files = []
    for directory in ['src', 'tests', 'scripts', 'config', 'tools', 'benchmarks', 'models', 'docs', 'reviews', 'cad/source', 'cad/scripts', 'analysis/scripts', 'docker', '.github', '.devcontainer']:
        path = root / directory
        if path.exists():
            files.extend(p for p in path.rglob('*') if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts)
    for name in ['README.md', 'cad/README.md', 'analysis/README.md', 'LICENSE', 'CITATION.cff', 'THIRD_PARTY_NOTICES.md', 'COORDINATION.md', '.clang-format', '.gitignore', '.dockerignore']:
        if (root / name).is_file():
            files.append(root / name)
    return sorted(set(files))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    lines = []
    for path in source_files(root):
        lines.append(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.relative_to(root).as_posix())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text('\n'.join(lines) + '\n')
    print(f'{len(lines)} source/config files recorded in {args.output}')


if __name__ == '__main__':
    main()
