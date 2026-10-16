from pathlib import Path
import os,sys,json,hashlib,importlib.util,gzip,tarfile,resource
resource.setrlimit(resource.RLIMIT_CPU,(60,60));sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('mac65','/Users/uot/Documents/ChatGPT/ros/tools/cold_stream_backup_v1/mac_consumer.py');mac=importlib.util.module_from_spec(spec);spec.loader.exec_module(mac)
R=Path('/Users/uot/Documents/ChatGPT/ros');O=Path('/private/tmp/root65_mac_consumer_fixture_tests_v1_20261016');O.mkdir();L=Path('/private/tmp/phase5_stop53_combined_derived_budget_v1_20261015')
spec=importlib.util.spec_from_file_location('strict65',R/'tools/cold_storage_verification_v1/strict_codec_reader.py');strict=importlib.util.module_from_spec(spec);spec.loader.exec_module(strict)
sha=lambda b:hashlib.sha256(b).hexdigest()
GOOD=Path('/private/tmp/phase5_roundoff_command64_source_v1_20261016/pure_suite64_readback_v1/current-braking-warm-nominal63-tests/max1080-stream/stream.bin');PREFIX=Path('/private/tmp/phase5_current_braking_nominal62_source_v3_20261016/pure_suite62_readback_v3/current-braking-nominal-tests/all132-real-refusals/stop_objective_mode.bin')
good=strict.verify_artifact(GOOD);prefix=strict.verify_artifact(PREFIX,require_source_complete=False);assert good['source_complete']and not prefix['source_complete']and prefix['closed_raw_prefix_valid']
producer='''from pathlib import Path
import sys,json,hashlib,io,tarfile,gzip
M=Path(sys.argv[1]);P=json.loads((M/'STREAM_PREPARED.json').read_text());J=json.loads((M/'SOURCE_MANIFEST.json').read_text());root=Path(P['native_source']);buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w:')as t:
 for e in J['files']:
  q=root/str(Path(e['path']).relative_to(P['prefix']));b=q.read_bytes();assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256'];t.add(q,arcname=e['path'],recursive=False)
 for name in P['metadata_members']:t.add(M/name,arcname=name,recursive=False)
raw=buf.getvalue();assert len(raw)<1048576;b=gzip.compress(raw,compresslevel=1,mtime=0);sys.stdout.buffer.write(b);sys.stdout.buffer.flush();sys.stderr.write(json.dumps({'complete':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'outer_tar_raw_bytes':len(raw),'source_before_after_stable':True,'source_manifest_sha256':hashlib.sha256((M/'SOURCE_MANIFEST.json').read_bytes()).hexdigest()}))
'''
results=[]
for name,bad in [('mixed_complete_closedprefix_UNKNOWN',False),('badCRC_falsely_claimed_valid',True)]:
 root=O/name;root.mkdir();source=root/'source';source.mkdir();metadata=root/'metadata';metadata.mkdir();copies={}
 for label,p in [('complete',GOOD),('prefix',PREFIX)]:
  d=source/label;d.mkdir();b=p.read_bytes()
  if bad and label=='complete':b=b[:-8]+bytes([b[-8]^1])+b[-7:]
  mac.metadata_write(d/p.name,b,L);mac.metadata_write(d/'MANIFEST.yaml',(p.parent/'MANIFEST.yaml').read_bytes(),L);copies[label]=(d/p.name,b)
 unknown=GOOD.read_bytes()[:max(16,len(GOOD.read_bytes())//2)];mac.metadata_write(source/'unknown.bin',unknown,L)
 codec=[]
 for label,facts in [('complete',good),('prefix',prefix)]:
  p,b=copies[label];e={**facts,'file':str(p),'stored_bytes':len(b),'stored_sha256':sha(b)};codec.append(e)
 codec.append(dict(file=str(source/'unknown.bin'),codec='GZIP_DEFLATE_V1',stored_bytes=len(unknown),stored_sha256=sha(unknown),source_complete=False,closed_raw_prefix_valid=False,storage_state='UNKNOWN_PREFIX',raw_bytes=None,raw_sha256=None,error='Deliberately truncated synthetic stored gzip; raw EOF/CRC unknown'))
 payload=[dict(path='native65/'+str(p.relative_to(source)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(source.rglob('*'))if p.is_file()];manifest=dict(native_source=str(source),files=payload,payload_count=len(payload),payload_bytes=sum(e['bytes']for e in payload));mac.write_json(metadata/'SOURCE_MANIFEST.json',manifest,L);mac.write_json(metadata/'FULL_NATIVE_CODEC_READBACK.json',dict(files=codec),L);mac.metadata_write(metadata/'fixture_producer.py',producer.encode(),L);mac.metadata_write(metadata/'strict_codec_reader.py',(R/'tools/cold_storage_verification_v1/strict_codec_reader.py').read_bytes(),L)
 prepared=dict(schema='OWNED_SYNTHETIC_COLD_STREAM_FIXTURE_V1',native_source=str(source),prefix='native65/',source_manifest=dict(bytes=(metadata/'SOURCE_MANIFEST.json').stat().st_size,sha256=sha((metadata/'SOURCE_MANIFEST.json').read_bytes())),codec_report=dict(bytes=(metadata/'FULL_NATIVE_CODEC_READBACK.json').stat().st_size,sha256=sha((metadata/'FULL_NATIVE_CODEC_READBACK.json').read_bytes())),metadata_members=['SOURCE_MANIFEST.json','FULL_NATIVE_CODEC_READBACK.json','fixture_producer.py','strict_codec_reader.py'],limits=dict(archive_bytes=mac.ARCHIVE_CAP,payload_bytes=mac.PAYLOAD_CAP,tar_raw_bytes=mac.TAR_CAP,metadata_bytes=mac.META_CAP),payload_count=manifest['payload_count'],payload_bytes=manifest['payload_bytes']);mac.write_json(metadata/'STREAM_PREPARED.json',prepared,L)
 archive=root/'Macarchive';report=root/'Rootreports';command=[sys.executable,'-I','-S','-B',str(metadata/'fixture_producer.py'),str(metadata)]
 if not bad:
  ready=mac.copy_stream(metadata,archive,report,command,L,60);assert ready['codec_counts']==dict(source_complete=1,closed_source_failure_prefix=1,unknown_stored_only=1)
  with tarfile.open(archive/'complete.tar.gz','r:gz')as t:
   member=t.extractfile('native65/unknown.bin');assert member.read()==unknown
  results.append(dict(case=name,success=True,counts=ready['codec_counts'],stored_unknown_bytes_restored_exact=True,Mac_READY_sha256=sha((archive/'READY.json').read_bytes())))
 else:
  failed=False
  try:mac.copy_stream(metadata,archive,report,command,L,60)
  except Exception as e:failed=True;error=repr(e)
  assert failed and(archive/'complete.tar.gz.part').is_file()and not(archive/'READY.json').exists()and(report/'FAILURE.json').is_file();results.append(dict(case=name,correctly_rejected=True,error=error,partial_preserved=True,no_READY=True,no_retry=True))
mac.write_json(O/'RESULT.json',dict(schema='ROOT65_MAC_CONSUMER_REAL_CODEC_AND_UNKNOWN_CRC_COUNTEREXAMPLE_TESTS_V1',producer='Local owned synthetic fixture producer; not the real Dell implementation/integration test',source_complete_and_source_failure_prefix_canonical_reader_verified=True,tests=results,scope='Two distinct bounded fixture IDs, no actual65/Model/native/hardware execution. All stored member/known inner rawSHA/CRC and actual Mac whole-file reopen tested; UNKNOWN has stored-byte recovery only. Every failure retained and no retry/refund. Real fixed-hostkey SSH producer stream end-to-end still required.'),L);print(json.dumps(results))
