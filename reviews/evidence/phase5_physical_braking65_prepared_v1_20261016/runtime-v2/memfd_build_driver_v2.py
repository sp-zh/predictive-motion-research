from pathlib import Path
import os,sys,json,hashlib,subprocess,time,selectors,signal,resource,ctypes,shlex,fcntl
PLAN=Path(sys.argv[1]);plan=json.loads(PLAN.read_text());BASE=Path(plan['build_root']);OUT=BASE/'targeted-build-attempt1';OUT.mkdir(exist_ok=False);START=time.monotonic();MIB=1024**2;CAP=512*MIB;META_CAP=20*MIB;metadata_spent=0;records=[];active=None
assert plan['schema']=='FINITE65_D_LANDLOCK_MEMFD_TARGETED_BUILD_V1'and len(plan['compile'])<=24 and len(plan['link'])<=10
alloc={'qualification':16*MIB,'compile':60*MIB,'link':240*MIB,'scratch_reserved_never_filesystem_writable':64*MIB,'pure':32*MIB,'saved_probe':80*MIB,'metadata':20*MIB};assert sum(alloc.values())==CAP
ledger={'schema':'FINITE65_D_BUILD512_PREWRITE_QUOTA_V1','cap':CAP,'allocations':alloc,'target_precharges':[],'compile_charged':0,'link_charged':0,'no_refund_reset_or_automatic_retry':True,'child_disk_scratch_hard_cap':0,'qualification_history_adopted_within_prior16MiB':True}
def meta_write(p,b):
 global metadata_spent
 assert p.parent==OUT and not p.is_symlink()and len(b)<=META_CAP-metadata_spent,'metadata aggregate prewrite budget';metadata_spent+=len(b)
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:f.write(b);f.flush();os.fsync(f.fileno())
def dump(n,j):meta_write(OUT/n,(json.dumps(j,indent=2)+'\n').encode())
def digest(p):
 p=Path(p);before=p.stat();h=hashlib.sha256();n=0
 with p.open('rb')as f:
  while b:=f.read(65536):h.update(b);n+=len(b)
 after=p.stat();assert(before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)and n==before.st_size
 return {'path':str(p),'resolved_path':str(p.resolve()),'bytes':n,'sha256':h.hexdigest()}
def identities(rows):
 actual=[digest(x['path'])for x in rows];assert actual==rows,'pinned build input drift';return actual
libc=ctypes.CDLL(None,use_errno=True)
class Rules(ctypes.Structure):_fields_=[('handled',ctypes.c_uint64)]
HANDLED=(1<<1)|sum(1<<b for b in range(4,15))
def limits(cap):
 def child():
  for key,n in [(resource.RLIMIT_CPU,120),(resource.RLIMIT_AS,2*1024**3),(resource.RLIMIT_FSIZE,cap),(resource.RLIMIT_CORE,0),(resource.RLIMIT_NOFILE,64),(resource.RLIMIT_NPROC,32)]:resource.setrlimit(key,(n,n))
  fd=libc.syscall(444,ctypes.byref(Rules(HANDLED)),ctypes.sizeof(Rules),0)
  if fd<0:raise OSError(ctypes.get_errno(),'Landlock create')
  if libc.prctl(38,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'no_new_privs')
  if libc.syscall(446,fd,0)<0:raise OSError(ctypes.get_errno(),'Landlock zero disk-write restriction')
  os.close(fd)
 return child
def stop(p):
 try:os.killpg(p.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 try:p.wait(timeout=2)
 except subprocess.TimeoutExpired:
  try:os.killpg(p.pid,signal.SIGKILL)
  except ProcessLookupError:pass
  p.wait(timeout=5)
def interrupted(signum,_):
 if active is not None:stop(active)
 raise RuntimeError('owned build interrupted '+str(signum))
signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
def execute(kind,index,row):
 global active
 cap=5*MIB//4 if kind=='compile' else 24*MIB;targets=row['targets'];assert len(targets)==(2 if kind=='compile' else 1)
 assert all(not Path(t).exists()and Path(t).parent==OUT for t in targets)
 charge=cap*len(targets);key=kind+'_charged';assert charge<=alloc[kind]-ledger[key],'aggregate target quota before memfd/compiler/any persistence';ledger[key]+=charge;ledger['target_precharges'].extend({'path':t,'cap':cap,'before_child':True}for t in targets);dump('LEDGER.json',ledger)
 fds=[os.memfd_create('finite65-'+kind+'-'+str(index)+'-'+str(j),os.MFD_CLOEXEC)for j in range(len(targets))]
 for fd in fds:os.ftruncate(fd,0);os.lseek(fd,0,0)
 paths=['/proc/self/fd/'+str(f)for f in fds];argv=[paths[int(a[1:])]if a in ['@0','@1']else a for a in row['argv']]
 extra=[];dryargv=None
 if kind=='link':
  dryargv=[argv[0],'-###']+argv[1:];d=subprocess.run(dryargv,cwd=OUT,env=plan['env'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,pass_fds=tuple(fds),timeout=10,preexec_fn=limits(cap));assert d.returncode==0 and len(d.stderr)<=65536 and not d.stdout
  lines=[shlex.split(v)for v in d.stderr.decode().splitlines()if '/collect2 'in v];assert len(lines)==1 and lines[0][0].endswith('/collect2')
  original_collect2=lines[0];argv=['/usr/bin/ld']+original_collect2[1:];assert not any('plugin'in v or 'resolution'in v for v in argv)
  required=[Path(a)for a in argv if a.startswith('/')and not a.startswith('/proc/self/fd/')and Path(a).is_file()]+[Path('/usr/bin/ld')]
  extra=[digest(p)for p in sorted(set(required))];dump('link-'+str(index)+'-EXACT_LD_AND_CRT_INPUTS_BEFORE.json',{'gxx_dryrun_argv':dryargv,'gxx_dryrun':d.stderr.decode(),'original_collect2_argv':original_collect2,'actual_ld_argv':argv,'extra_inputs':extra,'only_executable_replaced':True})
 record={'kind':kind,'index':index,'argv':argv,'target_precharged_cap':cap,'targets':targets,'child_disk_write_create_remove_rename_truncate_allowed':False,'memfd_only_outputs':True,'stage':'BEFORE_CHILD'};dump(kind+'-'+str(index)+'-PREFIX.json',record);started=time.monotonic();p=None;captures={'stdout':bytearray(),'stderr':bytearray()};error=None
 try:
  p=subprocess.Popen(argv,cwd=OUT,env=plan['env'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,pass_fds=tuple(fds),close_fds=True,start_new_session=True,preexec_fn=limits(cap));active=p;sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ,'stdout');sel.register(p.stderr,selectors.EVENT_READ,'stderr')
  while sel.get_map():
   if time.monotonic()-started>150 or time.monotonic()-START>1800:raise TimeoutError('finite build command/batch wall')
   for key,_ in sel.select(.1):
    b=os.read(key.fileobj.fileno(),65536)
    if not b:sel.unregister(key.fileobj);continue
    remaining=131072-len(captures[key.data]);captures[key.data].extend(b[:max(0,remaining)])
    if len(b)>remaining:raise RuntimeError('finite stdout/stderr128KiB capture bound')
  record['exit']=p.wait(timeout=5);record['stage']='CHILD_EXIT_REAPED';sel.close()
 except BaseException as e:
  error=repr(e)
  if p is not None:stop(p)
 finally:
  active=None
  if p is not None:
   for stream in [p.stdout,p.stderr]:
    if stream:stream.close()
  record['error']=error;record['wall_seconds']=time.monotonic()-started;record['captured_bytes']={k:len(v)for k,v in captures.items()}
  for k,b in captures.items():meta_write(OUT/(kind+'-'+str(index)+'.'+k),bytes(b))
  outputs=[]
  for fd,target in zip(fds,targets):
   n=os.fstat(fd).st_size;assert 0<=n<=cap,'memfd independent post child cap before parent persist';os.lseek(fd,0,0);actual=Path(target if record.get('exit')==0 and error is None else target+'.failed-prefix');h=hashlib.sha256();seen=0
   with actual.open('xb')as f:
    while b:=os.read(fd,min(65536,cap-seen+1)):
     assert len(b)<=cap-seen,'parent prewrite fixed target bound';f.write(b);h.update(b);seen+=len(b)
    f.flush();os.fsync(f.fileno())
   assert seen==n;outputs.append({'path':str(actual),'bytes':seen,'sha256':h.hexdigest(),'source':'anonymous memfd bounded by inherited RLIMIT_FSIZE and parent same precharge'});os.close(fd)
  record['outputs']=outputs
  if extra:assert extra==[digest(x['path'])for x in extra],'ld/CRT input drift';dump('link-'+str(index)+'-EXACT_LD_AND_CRT_INPUTS_AFTER.json',extra)
  dump(kind+'-'+str(index)+'-RESULT.json',record)
 return record
try:
 assert libc.syscall(444,0,0,1)>=3 and plan['env']['TMPDIR']==str(BASE/'scratch-never-writable')and plan['env']['TMP']==plan['env']['TEMP']==plan['env']['TMPDIR']
 assert not list(Path(plan['env']['TMPDIR']).rglob('*'))
 before=identities(plan['inputs']);dump('BEFORE_INPUT_IDENTITIES.json',before);dump('LEDGER.json',ledger)
 for kind in ['compile','link']:
  for index,row in enumerate(plan[kind],1):
   r=execute(kind,index,row);records.append(r);dump('BATCH_PREFIX.json',{'records':records,'complete':False})
   assert r.get('exit')==0 and r['error']is None,'first compiler/link refusal retained; no automatic retry/cap expansion'
 after=identities(plan['inputs']);dump('AFTER_INPUT_IDENTITIES.json',after);assert not list(Path(plan['env']['TMPDIR']).rglob('*'))
 dump('BUILD_RESULT.json',{'complete':True,'records':records,'metadata_charged_before_final_record':metadata_spent,'ledger':ledger,'zero_disk_scratch':True,'native65_or_Model_invocations':0,'scope':'Finite targeted build only, pure tests and actual controller entry not yet.'})
except BaseException as e:
 dump('BUILD_FAILURE.json',{'complete':False,'error':repr(e),'records':records,'ledger':ledger,'all_failed_output_prefixes_and_charges_retained':True,'native65_or_Model_invocations':0});raise
