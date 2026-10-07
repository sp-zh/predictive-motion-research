#!/usr/bin/env python3
"""Copy regular files to a mounted share, resume safely, and verify SHA-256."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

BLOCK = 8 * 1024 * 1024


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(BLOCK):
            h.update(block)
    return h.hexdigest()


def snapshot(path):
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns


def copy_one(source, target, reserve):
    initial = snapshot(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + '.codex-part')
    if target.is_symlink() or partial.is_symlink():
        raise ValueError('Refusing a symbolic-link destination')
    if target.exists():
        expected = digest(source)
        if snapshot(source) != initial:
            raise ValueError('Source changed while hashing')
        if target.stat().st_size == initial[0] and digest(target) == expected:
            print(f'Already verified: {target}', flush=True)
            return {'file': str(target), 'bytes': initial[0], 'sha256': expected}
        raise ValueError(f'Destination exists with different content: {target}')
    offset = partial.stat().st_size if partial.exists() else 0
    if offset > initial[0]:
        raise ValueError(f'Partial file larger than source: {partial}')
    available = shutil.disk_usage(target.parent).free
    needed = initial[0] - offset + reserve
    if available < needed:
        raise ValueError(f'Insufficient space: need {needed} bytes including reserve; have {available}')
    h = hashlib.sha256()
    started = time.monotonic()
    with source.open('rb') as reader:
        if offset:
            with partial.open('rb') as previous:
                remaining = offset
                while remaining:
                    block = reader.read(min(BLOCK, remaining))
                    if not block:
                        raise ValueError('Source truncated during resume verification')
                    if block != previous.read(len(block)):
                        raise ValueError(f'Partial content differs; retained for inspection: {partial}')
                    h.update(block)
                    remaining -= len(block)
            print(f'Resuming at {offset} bytes: {target}', flush=True)
        with partial.open('ab') as writer:
            total = offset
            reported = time.monotonic()
            while block := reader.read(BLOCK):
                writer.write(block)
                h.update(block)
                total += len(block)
                now = time.monotonic()
                if now - reported >= 1:
                    print(f'{target.name}: {total}/{initial[0]} bytes', flush=True)
                    reported = now
            writer.flush()
            os.fsync(writer.fileno())
    expected = h.hexdigest()
    if snapshot(source) != initial or total != initial[0]:
        raise ValueError('Source changed during transfer; partial file retained')
    if digest(partial) != expected:
        raise ValueError('Destination SHA-256 mismatch; partial file retained')
    # Never overwrite an existing destination, even if another writer created it.
    if target.exists():
        raise ValueError('Destination appeared during transfer; partial file retained')
    partial.rename(target)
    elapsed = time.monotonic() - started
    print(f'Verified: {target} ({elapsed:.2f}s including hash verification)', flush=True)
    return {'file': str(target), 'bytes': initial[0], 'sha256': expected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path, help='Existing mounted-share directory, or local directory')
    parser.add_argument('--reserve-gib', type=float, default=10)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    if args.reserve_gib < 0:
        parser.error('reserve must be nonnegative')
    source = args.source.absolute()
    destination = args.destination.absolute()
    if source.is_symlink() or not source.exists():
        parser.error('source must be an existing regular file or directory, not a symlink')
    if source.is_dir() and (destination == source or source in destination.parents):
        parser.error('destination must be outside the source directory')
    if not destination.is_dir():
        parser.error('destination must already exist; confirm the share is mounted first')
    jobs = [(source, destination / source.name)] if source.is_file() else []
    if source.is_dir():
        for path in sorted(source.rglob('*')):
            if path.is_symlink():
                parser.error(f'symlinks need separate handling: {path}')
            if path.is_file():
                jobs.append((path, destination / path.relative_to(source)))
    results = []
    for origin, target in jobs:
        results.append(copy_one(origin, target, int(args.reserve_gib * 1024 ** 3)))
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps({'verified': results}, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(results)} files verified. Manifest: {args.manifest}', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f'Transfer stopped: {exc}', file=sys.stderr)
        sys.exit(1)
