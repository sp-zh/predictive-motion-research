"""Verify or restore the exact102-file source tree from immutable V18/V19 and V20 overlays.

--check only reads and hashes source bytes. Materialization requires a fresh
absolute output directory. This utility never builds, runs a Model or starts a
controller, and it leaves both source versions unchanged.
"""
from pathlib import Path
import argparse,hashlib,json,os

def source_files(here):
 manifest=json.loads((here/'EFFECTIVE_SOURCE_MANIFEST.json').read_text());assert manifest['schema']=='PHASE5_V20_EFFECTIVE_SOURCE_OVERLAY_V1'
 rows=manifest['files'];assert len(rows)==manifest['file_count']==102;seen=set();total=0
 for row in rows:
  name=row['name'];assert Path(name).name==name and name not in seen and name not in ['.','..']and '\x00'not in name;seen.add(name)
  kind=row['storage'];assert kind in ['BASE_V18','BASE_V19','V20_OVERLAY'];root={'BASE_V18':here.parent/'phase5_controlled_stop_session_v18','BASE_V19':here.parent/'phase5_controlled_stop_session_v19','V20_OVERLAY':here}[kind]
  p=root/name;assert p.is_file()and not p.is_symlink()and p.stat().st_size==row['bytes']<=2*1024**2
  data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'];total+=len(data);assert total<=4*1024**2
  yield name,data
 assert total==manifest['total_bytes']

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');ap.add_argument('destination',type=Path,nargs='?');args=ap.parse_args();assert args.check!=(args.destination is not None),'choose --check or a fresh destination'
 here=Path(__file__).resolve().parent
 # Finish verification before creating any output. The bounded source is <4MiB.
 rows=list(source_files(here))
 if args.check:print(json.dumps({'verified_files':len(rows),'bytes':sum(len(b)for _,b in rows),'mode':'read_only_check'}));return
 d=args.destination;assert d.is_absolute()and d.parent.resolve()==d.parent and d.parent.is_dir()and not d.exists()and not d.is_symlink();d.mkdir(mode=0o700)
 for name,data in rows:
  fd=os.open(d/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 print(json.dumps({'materialized_files':len(rows),'bytes':sum(len(b)for _,b in rows),'destination':str(d),'build_or_native_invocations':0}))
if __name__=='__main__':main()
