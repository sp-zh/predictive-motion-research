#!/usr/bin/env python3
"""Publish an immutable, deterministic source-only archive with SHA-256 identity.

Use this on the authoritative checkout after its phase gate. An archive is a
source snapshot, not evidence that a fresh environment built or ran it.
"""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile

from source_manifest import source_files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='New publication directory; existing paths are refused')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    output = args.output.resolve()
    # Refuse overwrite: an exported identity must never change beneath a reader.
    output.mkdir(parents=True, exist_ok=False)
    snapshot = []
    for path in source_files(root):
        data = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        snapshot.append((relative, data, 0o755 if path.stat().st_mode & 0o111 else 0o644))
    manifest = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n'
                       for name, data, _ in snapshot).encode()
    partial = output / 'source.tar.gz.part'
    with partial.open('wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w', format=tarfile.PAX_FORMAT) as archive:
                for name, data, mode in snapshot + [('SOURCE.sha256', manifest, 0o644)]:
                    info = tarfile.TarInfo('predictive_motion/' + name)
                    info.size = len(data)
                    info.mode = mode
                    info.mtime = 0
                    archive.addfile(info, io.BytesIO(data))
        raw.flush()
        os.fsync(raw.fileno())
    digest = hashlib.sha256(partial.read_bytes()).hexdigest()
    archive_path = output / 'source.tar.gz'
    partial.rename(archive_path)
    (output / 'source.tar.gz.sha256').write_text(digest + '  source.tar.gz\n')
    (output / 'SOURCE.sha256').write_bytes(manifest)
    metadata = {
        'scope': 'source/config snapshot; clean-build and benchmark execution not implied',
        'archive_sha256': digest,
        'archive_bytes': archive_path.stat().st_size,
        'source_file_count': len(snapshot),
        'source_manifest_sha256': hashlib.sha256(manifest).hexdigest(),
        'excluded': ['credentials', 'build/install/vendor caches', 'raw experiment results',
                     'generated CAD STEP/mesh/model files', 'transfer payloads'],
    }
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    # A receiver must wait for READY before reading any publication file.
    (output / 'READY').write_text(digest + '\n')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
