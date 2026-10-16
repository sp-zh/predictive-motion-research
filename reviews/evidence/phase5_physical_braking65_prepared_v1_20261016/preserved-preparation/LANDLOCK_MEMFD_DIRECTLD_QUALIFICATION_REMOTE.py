from pathlib import Path
import json,subprocess,resource,os,time,hashlib,ctypes,shlex
P=Path('/mnt/d/CodexTransfer/phase5-build65-20261016');Q=P/'landlock-memfd-directld-qualification6';Q.mkdir(exist_ok=False);T=Q/'scratch';T.mkdir();src=Q/'constant.cpp';src.write_text('int main(){return 0;}\n');obj=Q/'constant.o';elf=Q/'constant';dep=Q/'constant.d';canary=Q/'protected_canary';canary.write_text('UNCHANGED\n')
fds=[os.memfd_create('compile-object65'),os.memfd_create('compile-dependency65'),os.memfd_create('linked-ELF65')]
fdobj,fddep,fdelf=fds
fdpath=lambda f:'/proc/self/fd/'+str(f)
libc=ctypes.CDLL(None,use_errno=True)
class Rules(ctypes.Structure):_fields_=[('handled',ctypes.c_uint64)]
class PathRule(ctypes.Structure):_pack_=1;_fields_=[('allowed',ctypes.c_uint64),('parent_fd',ctypes.c_int32)]
WRITE=1<<1;TRUNCATE=1<<14;HANDLED=WRITE|sum(1<<b for b in range(4,15))
def guard(outputs,cap):
 def apply():
  for k,n in [(resource.RLIMIT_CPU,10),(resource.RLIMIT_AS,256*1024**2),(resource.RLIMIT_FSIZE,cap),(resource.RLIMIT_CORE,0),(resource.RLIMIT_NOFILE,64)]:resource.setrlimit(k,(n,n))
  fd=libc.syscall(444,ctypes.byref(Rules(HANDLED)),ctypes.sizeof(Rules),0)
  if fd<0:raise OSError(ctypes.get_errno(),'create Landlock ruleset')
  for p in outputs:
   out=os.open(p,os.O_PATH|os.O_CLOEXEC|os.O_NOFOLLOW);rule=PathRule(WRITE|TRUNCATE,out);rc=libc.syscall(445,fd,1,ctypes.byref(rule),0);os.close(out)
   if rc<0:raise OSError(ctypes.get_errno(),'add fixed output Landlock rule')
  if libc.prctl(38,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'no_new_privs')
  if libc.syscall(446,fd,0)<0:raise OSError(ctypes.get_errno(),'restrict fixed-output compiler child')
  os.close(fd)
 return apply
env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC','TMPDIR':str(T),'TMP':str(T),'TEMP':str(T)}
commands=[(['/usr/bin/g++','-pipe','-fno-use-linker-plugin','-MMD','-MF',fdpath(fddep),'-c',str(src),'-o',fdpath(fdobj)],[]),(['/usr/bin/g++','-pipe','-fno-use-linker-plugin',str(obj),'-Wl,--build-id=none','-o',fdpath(fdelf)],[]),([str(elf)],[])]
records=[]
for argv,outputs in commands:
 if len(records)==1:
  dry=subprocess.run([argv[0],'-###']+argv[1:],cwd=Q,env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=5);assert dry.returncode==0 and len(dry.stderr)<65536
  lines=[shlex.split(line)for line in dry.stderr.decode().splitlines()if '/collect2 'in line];assert len(lines)==1 and lines[0][0].endswith('/collect2')
  argv=['/usr/bin/ld']+lines[0][1:];assert not any('plugin'in a or 'resolution'in a for a in argv)
 r=subprocess.run(argv,cwd=Q,env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=15,preexec_fn=guard(outputs,1024**2),pass_fds=tuple(fds));
 if r.returncode==0:
  for fd,target in ([(fdobj,obj),(fddep,dep)]if len(records)==0 else [(fdelf,elf)]if len(records)==1 else []):
   n=os.fstat(fd).st_size;assert n<=1024**2;os.lseek(fd,0,0);b=os.read(fd,n);assert len(b)==n
   with target.open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 records.append({'argv':argv,'allowed_existing_outputs':list(map(str,outputs)),'exit':r.returncode,'stderr':r.stderr.decode()[-65536:]});assert len(r.stdout)+len(r.stderr)<65536
 print(json.dumps({'last_command':records[-1]}),flush=True)
 if r.returncode:break
if all(x['exit']==0 for x in records)and len(records)==3:
 negative="from pathlib import Path\nfor s in "+repr([str(T/'forbidden_new'),str(canary)])+":\n try:Path(s).write_bytes(b'BAD')\n except PermissionError:continue\n raise RuntimeError('write unexpectedly allowed')\n"
 r=subprocess.run(['/usr/bin/python3','-I','-S','-B','-c',negative],cwd=Q,env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=5,preexec_fn=guard([],1024**2));records.append({'negative_no_new_scratch_and_no_protected_write':True,'exit':r.returncode,'stderr':r.stderr.decode()});assert r.returncode==0 and canary.read_text()=='UNCHANGED\n'and not list(T.iterdir())
out={'schema':'ANONYMOUS_MEMFD_OUTPUT_LANDLOCK_D_QUALIFICATION65_V1','landlock_ABI':libc.syscall(444,0,0,1),'records':records,'scratch_files':len(list(T.rglob('*'))),'fixed_outputs':{x.name:x.stat().st_size for x in [src,obj,dep,elf,canary]if x.exists()},'child_allowed_to_create_or_remove_any_file':False,'only_child_writes_anonymous_memfd_with_RLIMIT_FSIZE':True,'memfd_parent_persisted_only_after_exact_bounded_read':True,'global_system_permission_changes':False,'native65_Model_entry':False,'scope':'Qualified compiler/linker filesystem restriction only, not full source build or stop.'};b=(json.dumps(out,indent=2)+'\n').encode();assert len(b)<65536
with(Q/'RESULT.json').open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
print(json.dumps(out));assert len(records)==4 and all(x['exit']==0 for x in records)
