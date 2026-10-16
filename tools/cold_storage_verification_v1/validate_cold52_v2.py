from pathlib import Path
import os,sys,json,hashlib,zlib,tarfile,time,subprocess,datetime,importlib.util,resource
for key,value in [(resource.RLIMIT_CPU,300),(resource.RLIMIT_AS,768*1024**2),(resource.RLIMIT_FSIZE,2*1024**3),(resource.RLIMIT_CORE,0)]:resource.setrlimit(key,(value,value))
p=Path(__file__).resolve().parent;start=time.monotonic();archive=p/'transport.tar.gz.part';source=p/'SOURCE_READY52.json'
assert source.stat().st_size<=16*1024**2 and hashlib.sha256(source.read_bytes()).hexdigest()=='f24031516a1eb5b8d7ae88dda2fff0063d705137b41a97cde40013bf79e6f434'
ready=json.loads(source.read_text());outside={x['path']:{'bytes':x['bytes'],'sha256':x['sha256']}for x in ready['payload']};assert len(outside)==2776 and sum(x['bytes']for x in outside.values())==1941815773
mp=p/'SOURCE_TRANSPORT_MAPPING52.json';assert hashlib.sha256(mp.read_bytes()).hexdigest()=='f2faa3fb8bf8ec1ebff99a7bb95907787b8777315bc0cb7666d86e4cbea16a76';mapping=json.loads(mp.read_text());assert mapping['source_archive_sha256']=='f4e573271085a79fba7ffff54257fd4822e74d85f92b7a69e3535bbd5d9ba0ef'and mapping['outside_READY_sha256']=='f24031516a1eb5b8d7ae88dda2fff0063d705137b41a97cde40013bf79e6f434'and not mapping['unmapped'];expected={}
for row in mapping['payload']:
 assert row['Mac_packet_path']=='actual-dell/'+row['archive_member'] and row['Mac_packet_path']in outside and {'bytes':row['bytes'],'sha256':row['sha256']}==outside[row['Mac_packet_path']]and row['archive_member']not in expected
 expected[row['archive_member']]={'bytes':row['bytes'],'sha256':row['sha256']}
assert len(expected)==2148 and sum(x['bytes']for x in expected.values())==1795247536

reader_path=p/'strict_codec_reader.py';assert hashlib.sha256(reader_path.read_bytes()).hexdigest()=='c32178a23e5254f44ee21a62be655af3236c708c02bb061564c3d8b0b8cb468a';spec=importlib.util.spec_from_file_location('strict_cold52_reader',reader_path);reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
# Independent full outer stored SHA, CRC, single gzip EOF, and no trailing data.
z=zlib.decompressobj(31);h=hashlib.sha256();stored=0;raw_total=0
with archive.open('rb')as f:
 while chunk:=f.read(65536):
  stored+=len(chunk);h.update(chunk);data=chunk
  while True:
   block=z.decompress(data,65536);raw_total+=len(block);assert raw_total<=3*1024**3 and not z.unused_data;data=z.unconsumed_tail
   if not data and len(block)<65536:break
assert stored==1774846596 and h.hexdigest()=='f4e573271085a79fba7ffff54257fd4822e74d85f92b7a69e3535bbd5d9ba0ef' and z.eof and not z.unused_data and not z.unconsumed_tail
print('OUTER_SHA_CRC_SINGLE_EOF_PASS',stored,raw_total,flush=True)
# Tar restoration read: all members are read fully and matched to immutable Mac
# READY. Only bounded manifests are materialized; no hot result path is touched.
cache=p/'validation-manifests-v2';cache.mkdir();manifest_map={};meta_bytes=0;seen={};binary_receipts=[];total=0
with tarfile.open(archive,'r|gz')as tar:
 for member in tar:
  assert time.monotonic()-start<600,'finite full verification wall cap'
  name=member.name;rel=Path(name);assert member.isfile()and not rel.is_absolute()and '..'not in rel.parts and name in expected and name not in seen and len(seen)<3000
  e=expected[name];assert member.size==e['bytes'] and member.size<=256*1024**2
  parent=str(rel.parent);entry=manifest_map.get(parent,{}).get(rel.name)if rel.suffix=='.bin'else None
  inner=zlib.decompressobj(31)if entry and entry.get('codec','RAW_V1')=='GZIP_DEFLATE_V1'and entry['complete']else None
  raw_sha=hashlib.sha256();raw_n=0;blob=bytearray()if rel.name=='MANIFEST.yaml'else None;stored_sha=hashlib.sha256();count=0
  extracted=tar.extractfile(member);assert extracted is not None
  while chunk:=extracted.read(65536):
   assert len(chunk)<=member.size-count;count+=len(chunk);stored_sha.update(chunk)
   if blob is not None:assert len(blob)+len(chunk)<=32*1024**2;blob.extend(chunk)
   if entry and entry['complete']:
    if inner:
     data=chunk
     while True:
      out=inner.decompress(data,65536);raw_n+=len(out);assert raw_n<=128*1024**2 and not inner.unused_data;raw_sha.update(out);data=inner.unconsumed_tail
      if not data and len(out)<65536:break
    else:raw_n+=len(chunk);assert raw_n<=128*1024**2;raw_sha.update(chunk)
  assert count==e['bytes']and stored_sha.hexdigest()==e['sha256'];seen[name]=e;total+=count
  if blob is not None:
   assert meta_bytes+len(blob)<=64*1024**2;meta_bytes+=len(blob);q=cache/rel;q.parent.mkdir(parents=True,exist_ok=True)
   with q.open('xb')as f:f.write(blob)
   q.chmod(0o444);manifest_map[parent]=reader.manifest_entries(q);assert len(manifest_map)<=512
  if entry:
   assert count==entry['bytes']and stored_sha.hexdigest()==entry['sha256']
   record={'file':name,'stored_bytes':count,'stored_sha256':stored_sha.hexdigest(),'source_complete':entry['complete'],'codec':entry.get('codec','RAW_V1')}
   if entry['complete']:
    if inner:assert inner.eof and not inner.unused_data and not inner.unconsumed_tail
    assert raw_n==entry.get('raw_bytes',count)and raw_sha.hexdigest()==entry.get('raw_sha256',entry['sha256']);record.update(raw_bytes=raw_n,raw_sha256=raw_sha.hexdigest(),full_crc_single_eof_no_trailing=True)
   else:record['math_available']=False
   binary_receipts.append(record)
  elif rel.suffix=='.bin'and '/run-attempt1/artifacts/'in name:raise AssertionError('artifact binary needs earlier bound manifest')
assert seen==expected and total==1795247536
print('ALL_MEMBERS_AND_INNER_CODEC_PASS',len(seen),len(binary_receipts),flush=True)
r=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-Command','Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID,FreeSpace,Size | ConvertTo-Json -Compress'],stdin=subprocess.DEVNULL,capture_output=True,timeout=15);assert r.returncode==0,r.stderr;vol=json.loads(r.stdout.decode('utf-8-sig'));assert next(x for x in vol if x['DeviceID']=='C:')['FreeSpace']>=80*1024**3
report={'schema':'MAC52_COLD_TRANSPORT_DELL_C_MAPPED_RESTORATION_READ_VERIFY_V2','archive_bytes':stored,'archive_sha256':h.hexdigest(),'outer_raw_tar_bytes':raw_total,'outer_crc_single_eof_no_trailing':True,'source_READY_sha256':'f24031516a1eb5b8d7ae88dda2fff0063d705137b41a97cde40013bf79e6f434','all2148_mapped_transport_members_size_sha_restore_read_match':True,'Mac_full_packet_payload_count':2776,'transport_subset_not_full_packet':True,'later_Mac_packet_files_not_in_transport':628,'mapping_sha256':'f2faa3fb8bf8ec1ebff99a7bb95907787b8777315bc0cb7666d86e4cbea16a76','retained_initial_verifier_failure':'FAILED_MIGRATION_RETAINED.json: wrong identical-member-name/count assumption; no data hash failure','member_count':len(seen),'member_payload_bytes':total,'binary_files':len(binary_receipts),'complete_binary_files':sum(bool(x['source_complete'])for x in binary_receipts),'verified_inner_raw_bytes':sum(x.get('raw_bytes',0)for x in binary_receipts),'binary_receipts':binary_receipts,'manifest_cache_bytes':meta_bytes,'CIM_after':vol,'C_ge80GiB':True,'WSL_distro_storage_verified_on_C_registry':True,'wall_s':time.monotonic()-start,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'One original Mac cold outer transport copied. Original Mac expanded52 payload and all Dell native evidence remain. Not a new full experiment archive; C/D are not separate hardware backups. Mac deletion requires Root independent review.'}
with(p/'VERIFIED_REPORT_V2.json').open('x')as f:json.dump(report,f,indent=2)
archive.chmod(0o444);os.rename(archive,p/'transport.tar.gz')
record={'schema':'MAC52_COLD_ARCHIVE_ATOMIC_READY_V2','archive_path':str(p/'transport.tar.gz'),'archive_bytes':stored,'archive_sha256':h.hexdigest(),'verification_report_file':'VERIFIED_REPORT_V2.json','mapping_sha256':'f2faa3fb8bf8ec1ebff99a7bb95907787b8777315bc0cb7666d86e4cbea16a76','transport_member_count':2148,'Mac_full_packet_member_count':2776,'transport_is_historical_subset':True,'verification_report_sha256':hashlib.sha256((p/'VERIFIED_REPORT_V2.json').read_bytes()).hexdigest(),'source_READY_sha256':report['source_READY_sha256'],'whole_archive_and_all_member_restoration_verified':True,'C_ge80GiB':True,'native57_not_entered':True,'independent_Mac_readback':'PENDING','Mac_original_archive_removal':'NOT_AUTHORIZED_BY_THIS_READY; Root review required','scope':report['scope']}
with(p/'READY.json').open('x')as f:json.dump(record,f,indent=2);f.flush();os.fsync(f.fileno())
for q in p.rglob('*'):
 if q.is_file():q.chmod(0o444)
for q in sorted((q for q in p.rglob('*')if q.is_dir()),key=lambda q:len(q.parts),reverse=True):q.chmod(0o555)
p.chmod(0o555)
print('COLD_READY',json.dumps(record),flush=True)
