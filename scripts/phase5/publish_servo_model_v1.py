#!/usr/bin/env python3
"""Publish an immutable failed servo-model unit with verified input closure."""
import hashlib
import json
import tarfile
from pathlib import Path

p = Path('/home/codextransfer/predictive_motion')
base = p / 'results/phase5/development/servo-model-v1'
sha = lambda f: hashlib.sha256(Path(f).read_bytes()).hexdigest()
freeze = json.loads((p / 'results/phase5/development/servo-identification-v1-validation/frozen.json').read_text())
cache = Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/identity-cache')
closure = []
for name, h in freeze['files'].items():
    blob = cache / h
    if not blob.is_file() or sha(blob) != h:
        raise ValueError('missing/corrupt input cache ' + name)
    closure.append({'original_path': name, 'sha256': h, 'bytes': blob.stat().st_size})
with (base / 'verified_input_closure.json').open('x') as out:
    out.write(json.dumps({'inputs': len(closure), 'missing': [], 'verified_storage': str(cache), 'files': closure}, indent=2)+'\n')
items = {}
source = ['PHASE5_WRITER_STATE_20261007.json', 'scripts/phase5/servo_model_v1.py', 'scripts/phase5/servo_model_v1_test.py',
          'scripts/phase5/run_servo_validation_v1.py', 'scripts/phase5/plot_servo_model_v1.py', 'scripts/phase5/publish_servo_model_v1.py',
          'tools/phase5_adapter/servo_identification.cpp', 'config/phase5_development/servo_identification.yaml',
          'reviews/phase_5_servo_model_v1_executor_review.md']
for name in source:
    items['project/' + name] = p / name
for directory in [base, p/'results/phase5/development/servo-identification-v1-training', p/'results/phase5/development/servo-identification-v1-validation']:
    for f in directory.rglob('*'):
        if f.is_file():
            items['project/' + str(f.relative_to(p))] = f
for phase in ['training', 'validation']:
    directory = Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-identification-v1-'+phase)
    for f in directory.rglob('*'):
        if f.is_file():
            items['raw/' + phase + '/' + str(f.relative_to(directory))] = f
manifest = {name: {'sha256': sha(f), 'bytes': f.stat().st_size} for name, f in items.items()}
with (base / 'CHECKPOINT_FILE_MANIFEST.json').open('x') as out:
    out.write(json.dumps(manifest, indent=2)+'\n')
items['project/' + str((base/'CHECKPOINT_FILE_MANIFEST.json').relative_to(p))] = base/'CHECKPOINT_FILE_MANIFEST.json'
small = {name: manifest['project/'+name] for name in source}
small.update({str(f.relative_to(p)): {'sha256': sha(f), 'bytes': f.stat().st_size} for f in [base/'model.json', base/'training_report.json', base/'heldout-validation/validation_report.json', base/'figures/phase5_servo_model_v1_failed.png', base/'figures/phase5_servo_model_v1_failed.json', base/'figures/visual_inspection.json']})
with (base/'BACKUP_SOURCE_MANIFEST.json').open('x') as out:
    out.write(json.dumps(small, indent=2)+'\n')
items['project/' + str((base/'BACKUP_SOURCE_MANIFEST.json').relative_to(p))] = base/'BACKUP_SOURCE_MANIFEST.json'
dest = Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/servo-model-v1-20261007')
dest.mkdir(exist_ok=False)
part = dest/'servo-model-v1-failed.tar.gz.part'
with tarfile.open(part, 'w:gz') as archive:
    for name, f in sorted(items.items()):
        archive.add(f, arcname=name, recursive=False)
archive_file = dest/'servo-model-v1-failed.tar.gz'
part.rename(archive_file)
with tarfile.open(archive_file) as archive:
    members = archive.getmembers()
    if len(members) != len(items):
        raise ValueError('archive member count')
    for member in members:
        if not member.isfile() or member.name not in items:
            raise ValueError('unexpected member')
        if hashlib.sha256(archive.extractfile(member).read()).hexdigest() != sha(items[member.name]):
            raise ValueError('archive member mismatch ' + member.name)
ready = {'archive': str(archive_file), 'sha256': sha(archive_file), 'bytes': archive_file.stat().st_size,
         'members': len(items), 'archive_members_verified': True, 'input_cache_verified_on_dell': len(closure),
         'mac_copy_verified': False, 'scope': 'failed model v1 unit; no Phase5 acceptance',
         'source_manifest': str(base/'BACKUP_SOURCE_MANIFEST.json'), 'source_manifest_sha256': sha(base/'BACKUP_SOURCE_MANIFEST.json')}
with (dest/'READY.json.part').open('x') as out:
    out.write(json.dumps(ready, indent=2)+'\n')
(dest/'READY.json.part').rename(dest/'READY.json')
print(json.dumps(ready, indent=2))
