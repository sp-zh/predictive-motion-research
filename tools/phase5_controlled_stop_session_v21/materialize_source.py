"""Verify or restore the exact104 source files compiled for the causal-prefix unit.
--check is read-only. Restoration needs a fresh absolute directory and does not
build or run any QP, Model, controller or pure test. The flat runtime README is
historical source content; see this overlay README for the current result.
"""
from pathlib import Path
import argparse,base64,hashlib,json,os

def source_files(here):
 data=json.loads((here/'EFFECTIVE_SOURCE104_CAPSULE.json').read_text())
 rows=data['runtime_source'];assert data['file_count']==len(rows)==104
 total=0
 for name,row in rows.items():
  assert Path(name).name==name and name not in ['.','..'] and '\x00' not in name
  raw=base64.b64decode(row['base64'],validate=True)
  assert len(raw)==row['bytes']<=2*1024**2 and hashlib.sha256(raw).hexdigest()==row['sha256']
  total+=len(raw);assert total<=4*1024**2
  yield name,raw

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--check',action='store_true')
 parser.add_argument('destination',type=Path,nargs='?')
 args=parser.parse_args();assert args.check!=(args.destination is not None)
 rows=list(source_files(Path(__file__).resolve().parent))
 if args.check:
  print(json.dumps({'verified_files':len(rows),'bytes':sum(len(raw) for _,raw in rows),'read_only':True}));return
 dest=args.destination
 assert dest.is_absolute() and dest.parent.is_dir() and dest.parent.resolve()==dest.parent and not dest.exists() and not dest.is_symlink()
 dest.mkdir(mode=0o700)
 for name,raw in rows:
  fd=os.open(dest/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,'wb') as target:
   target.write(raw);target.flush();os.fsync(target.fileno())
 print(json.dumps({'restored_files':len(rows),'destination':str(dest),'native_entries':0}))
if __name__=='__main__':main()
