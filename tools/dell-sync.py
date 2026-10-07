#!/usr/bin/env python3
"""Push/pull a data directory over the USB4 SSH link, then verify SHA-256."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
SSH = str(ROOT / 'tools/dell-ssh.sh')
REMOTE_ROOT = '/mnt/d/CodexTransfer'
RESERVE = 10 * 1024 ** 3
REMOTE_CODE = '''
import hashlib,json,pathlib,shutil,sys
root=pathlib.Path(sys.argv[1])
action=sys.argv[2]
if action=='space':
    root.mkdir(parents=True,exist_ok=True)
    print(shutil.disk_usage(root).free)
elif action=='hash':
    out={}
    for p in sorted(root.rglob('*')):
        if '.rsync-partial' in p.relative_to(root).parts: continue
        if p.is_symlink(): raise RuntimeError('Symlinks require separate handling')
        if p.is_file():
            h=hashlib.sha256()
            with p.open('rb') as f:
                while b:=f.read(8*1024*1024): h.update(b)
            out[p.relative_to(root).as_posix()]={'bytes':p.stat().st_size,'sha256':h.hexdigest()}
    print(json.dumps(out))
'''


def remote(path, action):
    command = 'python3 -c ' + shlex.quote(REMOTE_CODE) + ' ' + shlex.quote(path) + ' ' + action
    return subprocess.check_output([SSH, 'DellTransfer', command], text=True)


def local_hash(root):
    out = {}
    for path in sorted(root.rglob('*')):
        if '.rsync-partial' in path.relative_to(root).parts:
            continue
        if path.is_symlink():
            raise ValueError('Symlinks require separate handling')
        if path.is_file():
            before = path.stat()
            h = hashlib.sha256()
            with path.open('rb') as stream:
                while block := stream.read(8 * 1024 * 1024):
                    h.update(block)
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError('Source changed while hashing')
            out[path.relative_to(root).as_posix()] = {'bytes': after.st_size, 'sha256': h.hexdigest()}
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('direction', choices=['push', 'pull'])
    parser.add_argument('local_directory', type=Path)
    parser.add_argument('remote_subdirectory', help='Relative name under inbox (push) or outbox (pull)')
    args = parser.parse_args()
    subdir = PurePosixPath(args.remote_subdirectory)
    if subdir.is_absolute() or '..' in subdir.parts or not subdir.parts:
        parser.error('remote_subdirectory must be a nonempty relative path without ..')
    # Keep the rsync remote shell argument unambiguous on both rsync implementations.
    if any(not (c.isascii() and (c.isalnum() or c in '/_.-')) for c in str(subdir)):
        parser.error('remote_subdirectory may contain ASCII letters, digits, /, _, . and -')
    path = args.local_directory.resolve()
    remote_path = REMOTE_ROOT + ('/inbox/' if args.direction == 'push' else '/outbox/') + str(subdir)
    if args.direction == 'push':
        if not path.is_dir():
            parser.error('local_directory must exist')
        expected = local_hash(path)
        available = int(remote(remote_path, 'space').strip())
    else:
        expected = json.loads(remote(remote_path, 'hash'))
        if not expected:
            parser.error('remote source has no ordinary files')
        path.mkdir(parents=True, exist_ok=True)
        available = shutil.disk_usage(path).free
    required = sum(v['bytes'] for v in expected.values()) + RESERVE
    if available < required:
        raise ValueError(f'Capacity check failed: need {required} bytes including 10 GiB reserve; have {available}')
    local_spec = str(path) + '/'
    remote_spec = 'DellTransfer:' + remote_path + '/'
    source, target = (local_spec, remote_spec) if args.direction == 'push' else (remote_spec, local_spec)
    # DrvFS/NTFS may reject POSIX timestamp changes for the dedicated account.
    # Compare content instead; do not request timestamp/owner/permission changes.
    subprocess.run(['/usr/bin/rsync', '-r', '--checksum', '--partial-dir=.rsync-partial', '--progress', '--stats', '-e', SSH, '--', source, target], check=True)
    actual = json.loads(remote(remote_path, 'hash')) if args.direction == 'push' else local_hash(path)
    mismatches = [name for name, item in expected.items() if actual.get(name) != item]
    if mismatches:
        raise ValueError('SHA-256 mismatch or missing file: ' + ', '.join(mismatches[:10]))
    manifest = ROOT / 'transfer/manifests' / (args.direction + '-' + str(subdir).replace('/', '_') + '.json')
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({'direction': args.direction, 'remote': remote_path, 'verified': expected}, indent=2) + '\n')
    print(f'Verified {len(expected)} files. SHA-256 manifest: {manifest}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'Transfer stopped: {exc}', file=sys.stderr)
        sys.exit(1)
