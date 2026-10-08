#!/usr/bin/env python3
"""Read-only live/cache/archive closure for a pinned augmented checkpoint.

No physics/model/plant execution. Archive membership is read in stream order.
"""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,tarfile,datetime

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('freeze','archive','output'):p.add_argument('--'+key,type=Path,required=True)
    for key in ('freeze-sha','archive-sha'):p.add_argument('--'+key,required=True)
    for key in ('files','members','payloads'):p.add_argument('--'+key,type=int,required=True)
    args=p.parse_args();assert not args.output.exists();source=Path(__file__);source_bytes=source.read_bytes()
    assert sha(args.freeze)==args.freeze_sha and sha(args.archive)==args.archive_sha
    entries=json.loads(args.freeze.read_text())['files'];assert len(entries)==args.files
    total=0
    for e in entries:
        for key in ('path','immutable_copy'):
            f=Path(e[key]);assert f.stat().st_size==e['bytes'] and sha(f)==e['sha256'],str(f)
        total+=e['bytes']
    hashes={};manifest=None
    with tarfile.open(args.archive,'r|gz') as t:
        for member in t:
            parts=PurePosixPath(member.name).parts
            assert member.isfile() and not member.name.startswith('/') and '..' not in parts and member.name not in hashes
            body=t.extractfile(member).read();assert len(body)==member.size
            hashes[member.name]={'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}
            if member.name.endswith('/CHECKPOINT_FILE_MANIFEST.json'):
                assert manifest is None;manifest=json.loads(body)
    assert len(hashes)==args.members and type(manifest) is dict and len(manifest)==args.payloads
    for name,e in manifest.items():assert hashes[name]==e,name
    for e in entries:assert hashes['immutable_dependencies/'+e['sha256']]=={'sha256':e['sha256'],'bytes':e['bytes']}
    assert sha(args.freeze)==args.freeze_sha and sha(args.archive)==args.archive_sha and source.read_bytes()==source_bytes
    report={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':hashlib.sha256(source_bytes).hexdigest(),'freeze_sha256':args.freeze_sha,'archive_sha256':args.archive_sha,'live_and_immutable_Dell_files_verified':len(entries),'input_bytes':total,'regular_members_verified':len(hashes),'all_archive_payloads_verified':len(manifest),'all_embedded_immutable_inputs_verified':len(entries),'scope':__doc__,'phase5':'NOT_ACCEPTED'}
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
