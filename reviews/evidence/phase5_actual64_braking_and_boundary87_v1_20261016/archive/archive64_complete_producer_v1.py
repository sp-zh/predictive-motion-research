from pathlib import Path
import sys,os,json,hashlib,datetime,subprocess,tarfile,zlib,resource,time,traceback,importlib.util,signal
P=Path(__file__).resolve().parent
SOURCE=Path('/home/codextransfer/predictive_motion/results/phase5/session-controlled-stop-roundoff-command-contraction-active32-brake64-dwell25-v1-20261016-attempt64')
MAX_PAYLOAD=8*1024**3;MAX_ARCHIVE=4*1024**3;MAX_TAR_RAW=MAX_PAYLOAD+256*1024**2;MAX_MEMBERS=40000;MAX_FILE=256*1024**2;START=time.monotonic()
for k,v in [(resource.RLIMIT_CPU,600),(resource.RLIMIT_AS,768*1024**2),(resource.RLIMIT_FSIZE,MAX_ARCHIVE),(resource.RLIMIT_CORE,0)]:resource.setrlimit(k,(v,v))
def fresh_json(name,x):
 encoded=(json.dumps(x,indent=2)+'\n').encode();cap=32*1024**2 if name=='SOURCE_MANIFEST.json'else 64*1024**2 if name=='FULL_NATIVE_CODEC_READBACK.json'else 1024**2;assert len(encoded)<=cap
 with(P/name).open('xb')as f:f.write(encoded);f.flush();os.fsync(f.fileno())
def digest(q):
 h=hashlib.sha256();n=0;s=q.stat()
 with q.open('rb')as f:
  while b:=f.read(65536):h.update(b);n+=len(b)
 assert n==s.st_size and (s.st_size,s.st_mtime_ns,s.st_ino)==(q.stat().st_size,q.stat().st_mtime_ns,q.stat().st_ino)
 return {'bytes':n,'sha256':h.hexdigest()}
def volumes():
 r=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-Command','Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID,FreeSpace,Size | ConvertTo-Json -Compress'],stdin=subprocess.DEVNULL,capture_output=True,timeout=15);assert r.returncode==0,r.stderr;out=json.loads(r.stdout.decode('utf-8-sig'));assert next(x for x in out if x['DeviceID']=='C:')['FreeSpace']>=80*1024**3;return out
def wall_timeout(signum,frame):raise TimeoutError('archive finite1200s wall cap; partial retained')
signal.signal(signal.SIGALRM,wall_timeout);signal.alarm(1200)
try:
 assert SOURCE.resolve()!=P.resolve()and SOURCE.resolve()not in P.resolve().parents and P.resolve()not in SOURCE.resolve().parents,'archive destination outside source collection'
 before=volumes();assert next(x for x in before if x['DeviceID']=='C:')['FreeSpace']>=80*1024**3+MAX_ARCHIVE+128*1024**2,'existing source stock already allocated; single part/final max4GiB plus bounded metadata128MiB above80GiB reserve';run=SOURCE/'run-attempt1';assert (run/'BUILD_RESULT.json').exists()or(run/'BUILD_FAILURE.json').exists();assert json.loads((run/'BEFORE_INPUT_IDENTITIES.json').read_text())==json.loads((run/'AFTER_INPUT_IDENTITIES.json').read_text())
 active=[]
 for q in Path('/proc').iterdir():
  if q.name.isdigit():
   try:
    if(q/'comm').read_text().strip()=='active_first_cy':active.append(q.name)
   except OSError:pass
 assert not active,'no large archival IO during any native control execution'
 files=[]
 for q in sorted(SOURCE.rglob('*')):
  if not q.is_file():continue
  assert not q.is_symlink();rel=q.relative_to(SOURCE)
  if rel.parts[0]in ['build-attempt1','link-attempt1']:
   if not(q.suffix in ['.json','.stdout','.stderr']or q.name=='active_first_cycle'):continue
  elif q.suffix in ['.o','.d','.map']:continue
  else:
   with q.open('rb')as f:magic=f.read(4)
   if magic==b'\x7fELF':continue
  assert q.stat().st_size<=MAX_FILE and len(str(rel).encode())<=512;files.append(q)
 assert 0<len(files)<=MAX_MEMBERS and sum(q.stat().st_size for q in files)<=MAX_PAYLOAD
 rows=[{'path':'native64/'+str(q.relative_to(SOURCE)),**digest(q)}for q in files]
 # Every original complete native binary is independently reconstructed once,
 # including per-file stored/raw hashes and CRC/EOF. Original incomplete source
 # prefixes retain their availability rather than receiving invented math.
 reader=P/'strict_codec_reader.py';assert digest(reader)['sha256']=='c32178a23e5254f44ee21a62be655af3236c708c02bb061564c3d8b0b8cb468a';spec=importlib.util.spec_from_file_location('strict64',reader);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);codecs=[]
 for q in sorted((run/'artifacts').rglob('*.bin')):
  e=mod.manifest_entries(q.parent/'MANIFEST.yaml')[q.name]
  if e['complete']:codecs.append({**mod.verify_artifact(q,False,True),'math_available':True,'math_scope':'Complete raw bytes available for separate mathematics review, not a passed research result.'})
  elif e.get('storage_stream_complete',True)and e.get('raw_hash_valid',True)and(e.get('codec','RAW_V1')=='RAW_V1'or(e.get('compressor_input_hash_valid')and e.get('raw_sha256'))):codecs.append({**mod.verify_artifact(q,False,False),'math_available':False,'math_scope':'Source incomplete. Closed/rawhashavailable prefix only; never successful source or math.'})
  else:codecs.append({'file':str(q),'source_complete':False,'stored':digest(q),'math_available':False,'raw_reconstruction':'UNAVAILABLE_OR_UNKNOWN_RETAINED_NO_MATH'})
 fresh_json('FULL_NATIVE_CODEC_READBACK.json',{'scope':'All native artifact files. Source completeness is distinct from codec readability; failed prefixes are never certified as successful source/math.','files':codecs})
 manifest={'schema':'COMPLETE64_ARCHIVE_SOURCE_MANIFEST_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_source':str(SOURCE),'files':rows,'payload_count':len(rows),'payload_bytes':sum(x['bytes']for x in rows),'cold_peak_plan':{'existing_source_stock_max_bytes':MAX_PAYLOAD,'source_stock_extra_copy_bytes':0,'single_part_or_final_max_bytes':MAX_ARCHIVE,'atomic_rename_extra_copy_bytes':0,'metadata_max_bytes':128*1024**2,'untouched_C_reserve_bytes':80*1024**3,'before_free_min_bytes':80*1024**3+MAX_ARCHIVE+128*1024**2},'excluded':'Build objects, dependency caches and extra executables. Native active ELF retained; all native run files, frozen source/profile, input identities, actual failures and small metadata included.','scope':'Complete64 stored native execution evidence archive on DellC; no complete second physical-device replica or phase acceptance.'};fresh_json('SOURCE_MANIFEST.json',manifest)
 part=P/'complete64.tar.gz.part'
 with tarfile.open(part,'x:gz',compresslevel=1)as t:
  for q,row in zip(files,rows):assert digest(q)=={k:row[k]for k in ['bytes','sha256']};t.add(q,arcname=row['path'],recursive=False)
  for name in ['SOURCE_MANIFEST.json','FULL_NATIVE_CODEC_READBACK.json','archive64_complete_producer_v1.py','strict_codec_reader.py']:t.add(P/name,arcname=name,recursive=False)
 with part.open('rb')as f:os.fsync(f.fileno())
 assert part.stat().st_size<=MAX_ARCHIVE and time.monotonic()-START<1200
 # Exact file content and safe member-set restoration, discarding bytes.
 expected={x['path']:{k:x[k]for k in ['bytes','sha256']}for x in rows}
 for name in ['SOURCE_MANIFEST.json','FULL_NATIVE_CODEC_READBACK.json','archive64_complete_producer_v1.py','strict_codec_reader.py']:expected[name]=digest(P/name)
 seen={};raw_bytes=0
 with tarfile.open(part,'r|gz')as t:
  for m in t:
   assert m.isfile()and m.name in expected and m.name not in seen and not m.name.startswith('/')and '..'not in Path(m.name).parts and m.size==expected[m.name]['bytes'];h=hashlib.sha256();n=0;src=t.extractfile(m)
   while b:=src.read(65536):h.update(b);n+=len(b)
   assert {'bytes':n,'sha256':h.hexdigest()}==expected[m.name];seen[m.name]=expected[m.name];raw_bytes+=n
 assert set(seen)==set(expected)
 z=zlib.decompressobj(31);stored=0;inflated=0
 with part.open('rb')as f:
  while b:=f.read(65536):
   stored+=len(b);data=b
   while True:
    out=z.decompress(data,65536);inflated+=len(out);assert inflated<=MAX_TAR_RAW and not z.unused_data;data=z.unconsumed_tail
    if not data and len(out)<65536:break
 assert z.eof and not z.unused_data and not z.unconsumed_tail and stored==part.stat().st_size
 identity=digest(part);after=volumes();final=P/'complete64.tar.gz';part.chmod(0o444);os.rename(part,final);directory_fd=os.open(P,os.O_RDONLY|os.O_DIRECTORY);os.fsync(directory_fd);os.close(directory_fd)
 fresh_json('READY.json',{'schema':'COMPLETE64_DELL_C_ARCHIVE_READY_V1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive_path':str(final),**identity,'source_manifest':digest(P/'SOURCE_MANIFEST.json'),'codec_report':digest(P/'FULL_NATIVE_CODEC_READBACK.json'),'payload_count':len(rows),'payload_bytes':manifest['payload_bytes'],'members_verified':len(seen),'full_member_bytes_verified':raw_bytes,'outer_tar_raw_bytes':inflated,'full_gzip_crc_singleEOF_no_trailing':True,'native_before_after_inputs_equal':True,'actual_volumes_before':before,'actual_volumes_after':after,'wall_seconds':time.monotonic()-START,'Mac_full_stream_readback':'PENDING','scope':'Complete stored native64 evidence and recoverable source/profile archive on DellC, source incomplete evidence retained. Same Dell C original+archive are not independent physical-device backups. Mac metadata/selected packet only. No Git/phase acceptance claim.'})
 for q in P.iterdir():
  if q.is_file():q.chmod(0o444)
 print(json.dumps({'archive':str(final),'identity':identity,'READY_sha256':digest(P/'READY.json')['sha256'],'payload_count':len(rows),'payload_bytes':manifest['payload_bytes'],'native_codec_files':len(codecs),'native_complete_codec_files':sum(bool(x['source_complete'])for x in codecs),'wall_seconds':time.monotonic()-START}),flush=True)
except BaseException as e:
 try:fresh_json('FAILURE.json',{'error':repr(e),'traceback':traceback.format_exc(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wall_seconds':time.monotonic()-START,'partial_preserved':True,'no_retry_or_overwrite':True})
 except BaseException:pass
 raise
