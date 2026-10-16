from pathlib import Path
import sys,os,json,hashlib,tarfile,time
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write_bytes,bounded_write
import importlib.util
spec=importlib.util.spec_from_file_location('strict','/Users/uot/Documents/ChatGPT/ros/tools/cold_storage_verification_v1/strict_codec_reader.py');strict=importlib.util.module_from_spec(spec);spec.loader.exec_module(strict)
O=Path('/private/tmp/root62_stop_cause_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O);M=Path('/private/tmp/phase5_exact_cycle_endpoint61_source_v1_20261016/full_archive61_v1/readback');receipt=json.loads((M/'METADATA_RECEIPT.json').read_text());entries=receipt if isinstance(receipt,list)else receipt['files']
for e in entries:
 p=M/Path(e['path']).name;b=p.read_bytes();assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256']
j=json.loads((M/'SOURCE_MANIFEST.json').read_text());wanted={e['path']:e for e in j['files']if any(e['path'].endswith('/cycle-32/trial-1/'+n)for n in ['candidate_value.bin','planning_guard.bin','observation_before.bin','MANIFEST.yaml'])};assert len(wanted)==4 and sum(e['bytes']for e in wanted.values())<=8*1024**2
archive=Path('/Users/uot/Documents/ChatGPT/ros/transfer/cold-backups/native61-complete-20261016-v1/complete61.tar.gz');assert archive.stat().st_size==3627990572;got=[];started=time.monotonic()
with tarfile.open(archive,'r|gz')as tar:
 for member in tar:
  if member.name not in wanted:continue
  e=wanted[member.name];assert member.isfile()and member.size==e['bytes'];f=tar.extractfile(member);b=f.read(8*1024**2+1);assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256'];p=O/'saved61_onset32_trial1'/Path(member.name).name;p.parent.mkdir(exist_ok=True);
  if p.exists():assert p.read_bytes()==b
  else:bounded_write_bytes(p,b)
  got.append(dict(archive_member=member.name,local=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
  if len(got)==len(wanted):break
assert len(got)==4
for e in got:
 if e['local'].endswith('.bin'):
  e['codec']=strict.verify_artifact(e['local']);assert e['codec']['source_complete']
report=dict(schema='ROOT62_BOUNDED_SAVED61_ONSET32_EXTRACTION_V1',source_archive_sha256='f06f0e976963bebaeee86a612d0ecae435f128b9599041a6cc854e2d4686bcf8',previous_full_archive_and_Mac_disk_readback_retained=True,selected_member_SHA_size_and_complete_codecs_verified=True,reader_qualification='First small extraction omitted per-directory MANIFEST required by canonical codec reader; failed after one SHA-verified saved binary was written. v2 includes original MANIFEST, validates and reuses exact existing bytes without deletion/refund. No native/Model/capture rerun.',files=got,wall_seconds=time.monotonic()-started,scope='Small immutable existing61 saved-data extraction only. No replay, Model/native invocation or source mutation. This partial read does not repeat the already completed whole outer-CRC proof.')
bounded_write(O/'SAVED61_ONSET32_TRIAL1_EXTRACTION.json',json.dumps(report,indent=2)+'\n');print(json.dumps(dict(files=len(got),wall=report['wall_seconds'],paths=[e['local']for e in got])))
