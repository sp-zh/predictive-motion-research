from pathlib import Path
import sys,os,json,hashlib,datetime,time,signal,resource,tarfile,gzip,importlib.util,traceback,subprocess
START=time.monotonic();HERE=Path(__file__).resolve().parent;CONFIG=HERE/'STREAM_CONFIG.json';cfg=json.loads(CONFIG.read_text());SOURCE=Path(cfg['source']);META=HERE;PURPOSE=cfg['purpose'];assert PURPOSE in ['NATIVE_FINITE66','PROTOCOL_TEST_ONLY'];MAX_PAYLOAD=int(cfg['source_payload_cap']);MAX_ARCHIVE=int(cfg['archive_aggregate_cap']);MAX_META=int(cfg['metadata_cap']);MAX_MEMBERS=40000;MAX_FILE=256*1024**2;MAX_TAR_RAW=int(4.25*1024**3)
assert 0<MAX_PAYLOAD<=int(3.5*1024**3)and 0<MAX_ARCHIVE<=4*1024**3 and 65536<MAX_META<=16*1024**2
if PURPOSE=='PROTOCOL_TEST_ONLY':assert MAX_PAYLOAD<=8*1024**2 and MAX_ARCHIVE<=8*1024**2
for key,value in [(resource.RLIMIT_CPU,600),(resource.RLIMIT_AS,768*1024**2),(resource.RLIMIT_CORE,0),(resource.RLIMIT_FSIZE,MAX_META)]:resource.setrlimit(key,(value,value))
def alarm(signum,frame):raise TimeoutError('finite direct stream1200s wall, original source and partial retained')
signal.signal(signal.SIGALRM,alarm);signal.alarm(1200)
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(q):
 s=q.stat();h=hashlib.sha256();n=0
 with q.open('rb')as f:
  while b:=f.read(65536):h.update(b);n+=len(b)
 assert n==s.st_size and(s.st_size,s.st_mtime_ns,s.st_ino)==(q.stat().st_size,q.stat().st_mtime_ns,q.stat().st_ino)
 return {'bytes':n,'sha256':h.hexdigest()}
def magic2(q):
 with q.open('rb')as f:return f.read(2)
def meta_spent():return sum(q.stat().st_size for q in META.iterdir()if q.is_file())
def fresh_json(name,data,final=False):
 assert '/'not in name;b=(json.dumps(data,indent=2)+'\n').encode();reserve=0 if final else 65536;assert len(b)<=MAX_META-reserve-meta_spent(),'metadata16MiB aggregate prewrite cap includes failed/consumed receipts'
 with(META/name).open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 (META/name).chmod(0o444)
def no_native():
 live=[]
 for q in Path('/proc').iterdir():
  if q.name.isdigit():
   try:
    if(q/'comm').read_text().strip()=='active_first_cy':live.append(q.name)
   except OSError:pass
 assert not live,'postnative only, no large stream during any native control'
def boundaries():
 assert SOURCE.resolve()==SOURCE and META.resolve()==META and SOURCE.is_absolute()and SOURCE.exists()and SOURCE.resolve()!=META.resolve()and SOURCE.resolve()not in META.resolve().parents and META.resolve()not in SOURCE.resolve().parents
 assert cfg['archive_prefix']and '/'not in cfg['archive_prefix']and '..'not in cfg['archive_prefix']and len(cfg['archive_prefix'])<=64
 assert str(SOURCE).startswith('/home/codextransfer/predictive_motion/')and str(META).startswith('/home/codextransfer/predictive_motion/transfer/cold-archives/')
 writer=json.loads(Path('/home/codextransfer/predictive_motion/PHASE5_WRITER_STATE_20261007.json').read_text());assert writer['owner_thread_id']=='01a114d9-3a3a-7071-b94f-624581000992'and writer['state']=='ACTIVE_SINGLE_WRITER';no_native()
 if PURPOSE=='NATIVE_FINITE66':
  run=SOURCE/'run-attempt1';assert any((run/n).is_file()for n in ['BUILD_RESULT.json','BUILD_FAILURE.json']);before=json.loads((run/'BEFORE_INPUT_IDENTITIES.json').read_text());after=json.loads((run/'AFTER_INPUT_IDENTITIES.json').read_text());assert before==after and len(before)==cfg['native_input_count'];entry=json.loads((SOURCE/'ENTRY_CONSUMED66.json').read_text());assert entry['profile_sha256']==cfg['native_profile_sha256']and entry['ELF_sha256']==cfg['native_ELF_sha256'];plan_name=cfg['runtime_plan_file'];assert Path(plan_name).name==plan_name and plan_name in ['active_run_plan66_v1.json'];assert digest(SOURCE/plan_name)['sha256']==entry['runtime_plan_sha256'];assert digest(SOURCE/'profile-version1/active_input.json')['sha256']==cfg['native_profile_sha256'];assert digest(SOURCE/'link-attempt1/active_first_cycle')['sha256']==cfg['native_ELF_sha256']
  volume=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-Command','Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID,FreeSpace,Size | ConvertTo-Json -Compress'],stdin=subprocess.DEVNULL,capture_output=True,timeout=15);assert volume.returncode==0,volume.stderr;vol=json.loads(volume.stdout.decode('utf-8-sig'));assert next(v for v in vol if v['DeviceID']=='C:')['FreeSpace']>=80*1024**3
 else:
  fixture=json.loads((SOURCE/'TEST_FIXTURE.json').read_text());assert fixture['no_Model_or_native_run']and fixture['fixture_id']==cfg['fixture_id'];vol=[]
 return vol
reader=HERE/'strict_codec_reader.py';assert digest(reader)['sha256']=='c32178a23e5254f44ee21a62be655af3236c708c02bb061564c3d8b0b8cb468a';sp=importlib.util.spec_from_file_location('strict65',reader);codec=importlib.util.module_from_spec(sp);sp.loader.exec_module(codec)
phase=sys.argv[1];assert phase in ['prepare','stream']
try:
 vol=boundaries()
 if phase=='prepare':
  assert not(META/'STREAM_PREPARED.json').exists()and not(META/'STREAM_CONSUMED.json').exists();files=[]
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
  assert 0<len(files)<=MAX_MEMBERS and sum(q.stat().st_size for q in files)<=MAX_PAYLOAD;rows=[];native=[]
  for q in files:
   row={'path':cfg['archive_prefix']+'/'+str(q.relative_to(SOURCE)),**digest(q)};rows.append(row)
   if q.suffix=='.bin':
    if(q.parent/'MANIFEST.yaml').is_file():
     entry=codec.manifest_entries(q.parent/'MANIFEST.yaml').get(q.name)
     if entry is None:native.append({'file':str(q),'codec':'GZIP_DEFLATE_V1'if magic2(q)==b'\x1f\x8b'else'RAW_V1','source_complete':False,'closed_raw_prefix_valid':False,'storage_state':'UNKNOWN_PREFIX','error':'Original manifest lacks native file entry, completeness unavailable','stored_bytes':row['bytes'],'stored_sha256':row['sha256'],'raw_bytes':None,'raw_sha256':None})
     elif entry['complete']:native.append({**codec.verify_artifact(q,False,True),'kind':'NATIVE_ARTIFACT','availability':'COMPLETE_SOURCE_RAW_AVAILABLE'})
     elif entry.get('storage_stream_complete',True)and entry.get('raw_hash_valid',True)and(entry.get('codec','RAW_V1')=='RAW_V1'or entry.get('compressor_input_hash_valid')and entry.get('raw_sha256')):native.append({**codec.verify_artifact(q,False,False),'kind':'NATIVE_ARTIFACT','availability':'CLOSED_SOURCE_FAILURE_PREFIX_NO_MATH'})
     else:native.append({'file':str(q),'codec':entry.get('codec','RAW_V1'),'source_complete':False,'closed_raw_prefix_valid':False,'storage_state':'UNKNOWN_PREFIX','error':entry.get('error','original failedprefix raw availability unknown'),'kind':'NATIVE_ARTIFACT','stored_bytes':row['bytes'],'stored_sha256':row['sha256'],'raw_bytes':None,'raw_sha256':None})
    elif 'run-attempt1'in q.relative_to(SOURCE).parts and 'artifacts'in q.relative_to(SOURCE).parts:
     with q.open('rb')as f:magic=f.read(2)
     native.append({'file':str(q),'codec':'GZIP_DEFLATE_V1'if magic==b'\x1f\x8b'else'RAW_V1','source_complete':False,'closed_raw_prefix_valid':False,'storage_state':'UNKNOWN_PREFIX','error':'Original native manifest unavailable, no raw source certification','kind':'NATIVE_ARTIFACT','stored_bytes':row['bytes'],'stored_sha256':row['sha256'],'raw_bytes':None,'raw_sha256':None})
    elif row['bytes']>128*1024**2:native.append({'file':str(q),'codec':'RAW_V1','source_complete':False,'closed_raw_prefix_valid':False,'storage_state':'UNKNOWN_PREFIX','kind':'OPAQUE_NON_NATIVE_RAW_FILE','error':'Opaque binary above128MiB raw-review cap: stored bytes preserved, no raw completeness certification','stored_bytes':row['bytes'],'stored_sha256':row['sha256'],'raw_bytes':None,'raw_sha256':None})
    else:native.append({'file':str(q),'codec':'RAW_V1','source_complete':True,'closed_raw_prefix_valid':True,'kind':'OPAQUE_NON_NATIVE_RAW_FILE','stored_bytes':row['bytes'],'stored_sha256':row['sha256'],'raw_bytes':row['bytes'],'raw_sha256':row['sha256'],'scope':'Whole opaque raw bytes observed only, no project-native role or mathematical completeness claim.'})
  fresh_json('FULL_NATIVE_CODEC_READBACK.json',{'files':native,'scope':'Source complete/closed failedprefix/unknown original retained distinctly; stored evidence archive is not mathematical acceptance.'});fresh_json('SOURCE_MANIFEST.json',{'schema':'POSTNATIVE66_DIRECT_MAC_SOURCE_MANIFEST_V1','purpose':PURPOSE,'native_source':str(SOURCE),'archive_prefix':cfg['archive_prefix'],'files':rows,'payload_count':len(rows),'payload_bytes':sum(x['bytes']for x in rows),'scope':'All selected complete original stored native/source/profile/ELF evidence; dependency cache/buildobjects excluded, no standalone environment restore. Dell original remains, archive stream persisted only on Mac.'})
  names=['SOURCE_MANIFEST.json','FULL_NATIVE_CODEC_READBACK.json',Path(__file__).name,'strict_codec_reader.py'];identities={n:digest(HERE/n)for n in names};fresh_json('STREAM_PREPARED.json',{'schema':'POSTNATIVE66_DIRECT_MAC_PREPARED_V1','utc':stamp(),'purpose':PURPOSE,'payload_count':len(rows),'payload_bytes':sum(x['bytes']for x in rows),'native_source':str(SOURCE),'prefix':cfg['archive_prefix']+'/','source_manifest':identities['SOURCE_MANIFEST.json'],'codec_report':identities['FULL_NATIVE_CODEC_READBACK.json'],'metadata_members':identities,'limits':{'archive_bytes':MAX_ARCHIVE,'payload_bytes':MAX_PAYLOAD,'metadata_bytes':MAX_META,'tar_raw_bytes':MAX_TAR_RAW},'config_identity':digest(CONFIG),'source_manifest_sha256':identities['SOURCE_MANIFEST.json']['sha256'],'archive_aggregate_cap':MAX_ARCHIVE,'no_Dell_tar_file':True,'actual_volumes':vol,'scope':'Preparation and original-source codec readback only; no Mac stream/backup completion yet.'})
  for q in files:q.chmod((q.stat().st_mode&0o7777)&~0o222)
  print(json.dumps({'prepared_sha256':digest(META/'STREAM_PREPARED.json')['sha256'],'payload_bytes':sum(x['bytes']for x in rows),'payload_count':len(rows)}),flush=True)
 else:
  prepared=json.loads((META/'STREAM_PREPARED.json').read_text());assert prepared['purpose']==PURPOSE and prepared['archive_aggregate_cap']==MAX_ARCHIVE and digest(CONFIG)==prepared['config_identity'];assert not(META/'STREAM_CONSUMED.json').exists();assert all(digest(HERE/n)==d for n,d in prepared['metadata_members'].items());manifest=json.loads((META/'SOURCE_MANIFEST.json').read_text());rows=manifest['files'];assert len(rows)==prepared['payload_count']and sum(r['bytes']for r in rows)==prepared['payload_bytes'];fresh_json('STREAM_CONSUMED.json',{'schema':'POSTNATIVE66_DIRECT_MAC_SINGLE_USE_STREAM_CONSUMED_V1','utc':stamp(),'purpose':PURPOSE,'prepared_sha256':digest(META/'STREAM_PREPARED.json')['sha256'],'archive_aggregate_cap':MAX_ARCHIVE,'automatic_retries':0,'failed_Mac_partial_must_stay_charged':True})
  class CountedOutput:
   def __init__(self):self.charged=0;self.written=0;self.hash=hashlib.sha256()
   def write(self,data):
    n=len(data);assert n<=MAX_ARCHIVE-self.charged,'4GiB prewrite attempted-byte cap no refund';self.charged+=n;at=0
    while at<n:
     try:got=os.write(1,data[at:])
     except InterruptedError:continue
     if got<=0:raise BrokenPipeError('stream output failed; no retry')
     self.hash.update(data[at:at+got]);self.written+=got;at+=got
    return n
   def flush(self):pass
   def tell(self):return self.written
  output=CountedOutput()
  class CountedTarRaw:
   def __init__(self,gzip_file):self.file=gzip_file;self.bytes=0
   def write(self,data):
    assert len(data)<=MAX_TAR_RAW-self.bytes,'4.25GiB tarraw prewrite bound';self.bytes+=len(data);return self.file.write(data)
   def flush(self):self.file.flush()
  with gzip.GzipFile(fileobj=output,mode='wb',compresslevel=1,mtime=0,filename='')as compressed:
   tar_raw=CountedTarRaw(compressed)
   with tarfile.open(fileobj=tar_raw,mode='w|')as tar:
    for row in rows:
     rel=Path(row['path']).relative_to(cfg['archive_prefix']);q=SOURCE/rel;assert digest(q)=={k:row[k]for k in ['bytes','sha256']};tar.add(q,arcname=row['path'],recursive=False)
    for name,identity in prepared['metadata_members'].items():assert digest(HERE/name)==identity;tar.add(HERE/name,arcname=name,recursive=False)

  assert output.written==output.charged and all(digest(SOURCE/Path(r['path']).relative_to(cfg['archive_prefix']))=={k:r[k]for k in ['bytes','sha256']}for r in rows);after=boundaries();record={'schema':'POSTNATIVE66_DIRECT_MAC_PRODUCER_STREAM_SENT_V1','complete':True,'utc':stamp(),'purpose':PURPOSE,'bytes':output.written,'sha256':output.hash.hexdigest(),'outer_tar_raw_bytes':tar_raw.bytes,'attempted_bytes_charged':output.charged,'prepared_sha256':digest(META/'STREAM_PREPARED.json')['sha256'],'source_manifest_sha256':prepared['source_manifest_sha256'],'source_payload_count':len(rows),'tar_members':len(rows)+len(prepared['metadata_members']),'source_before_after_stable':True,'no_Dell_tar_file':True,'actual_volumes_after':after,'wall_seconds':time.monotonic()-START,'Mac_persisted_reopen_readback':'PENDING','scope':'Complete bounded stream emitted once only. Producer READY does not prove Mac persistence/independent member+codec/reopen verification or phase/stop acceptance.'};fresh_json('STREAM_SENT.json',record,True);sys.stderr.write(json.dumps(record)+'\n');sys.stderr.flush()
except BaseException as error:
 try:fresh_json(('PREPARE_FAILURE.json'if phase=='prepare'else'STREAM_FAILURE.json'),{'error':repr(error),'utc':stamp(),'traceback':traceback.format_exc()[-16384:],'wall_seconds':time.monotonic()-START,'partial_preserved':True,'stream_attempted_bytes':output.charged if 'output'in locals()else None,'stream_written_bytes':output.written if 'output'in locals()else None,'no_retry_or_refund':True,'purpose':PURPOSE},True)
 except BaseException:pass
 raise
