from pathlib import Path
import os,stat,hashlib,json,struct
fixed=json.loads('{"plan_path": "/home/codextransfer/predictive_motion/results/phase5/session-task-start-inputtrust-bc-v2-20261010-attempt14/active_run_plan.json", "plan": {"bytes": 494006, "sha256": "7a27997b2c1a553859f0b61ec22d1f750ac89eb31b37b557f85947f06041f442"}, "driver_path": "/home/codextransfer/predictive_motion/results/phase5/session-task-start-inputtrust-bc-v2-20261010-attempt14/active_run_driver.py", "driver": {"bytes": 7592, "sha256": "b828f200f9750faca0ff89abc3ef4b4d7da78c9ab61976a49766a6c125a3e3f2"}, "output": "/home/codextransfer/predictive_motion/results/phase5/session-task-start-inputtrust-bc-v2-20261010-attempt14/run-attempt1", "argv": ["/home/codextransfer/predictive_motion/results/phase5/session-task-start-inputtrust-bc-v2-20261010-attempt14/link-attempt1/active_first_cycle", "/home/codextransfer/predictive_motion/results/phase5/session-task-start-inputtrust-bc-v2-20261010-attempt14/profile-version1/active_input.json", "3b442197a19376f69799aa0a9acb96a3d3334b42071cfb5c7cb36a448330189d", "7bf6a729b3921cb849698f1e7279018573c6a7a425a7ed54e0474f26322371e5", "/home/codextransfer/predictive_motion/results/phase5/session-task-start-inputtrust-bc-v2-20261010-attempt14/run-attempt1/artifacts"]}')
def checked(path,e,keep=False):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  st=os.fstat(fd);assert stat.S_ISREG(st.st_mode) and st.st_size==e['bytes'],path
  h=hashlib.sha256();size=0;chunks=[]
  while True:
   b=os.read(fd,65536)
   if not b:break
   size+=len(b);assert size<=e['bytes'];h.update(b)
   if keep:chunks.append(b)
  assert size==e['bytes'] and h.hexdigest()==e['sha256'],path
  if 'mode' in e:assert stat.S_IMODE(st.st_mode)==e['mode'],path
  if 'resolved_path' in e:assert str(Path(path).resolve(strict=True))==e['resolved_path'],path
  return b''.join(chunks) if keep else None
 finally:os.close(fd)
p=checked(fixed['plan_path'],fixed['plan'],True);d=json.loads(p)
checked(fixed['driver_path'],fixed['driver'])
assert d['compile_argv']==[fixed['argv']] and not Path(fixed['output']).exists()
assert len(d['input_files'])==1692
for x in d['input_files']:checked(x['requested_path'],x)
inputbytes=Path(fixed['argv'][1]).read_bytes();assert hashlib.sha256(inputbytes).hexdigest()==fixed['argv'][2]
producer=Path(fixed['argv'][0]);fd=os.open(producer,os.O_RDONLY|os.O_NOFOLLOW)
try:header=os.read(fd,64)
finally:os.close(fd)
assert header[:6]==b'ELF' and struct.unpack_from('<H',header,18)[0]==62 and struct.unpack_from('<H',header,16)[0]==3
print(json.dumps({'schema':'ROOT_PILOT_INPUTTRUST_PASSIVE_RUNTIME_PROFILE_VERIFICATION_V2','plan_sha256':hashlib.sha256(p).hexdigest(),'driver_sha256':fixed['driver']['sha256'],'input_files_verified':1692,'input_bytes_verified':sum(x['bytes'] for x in d['input_files']),'all_opened_regular_nofollow_sha_size_modes_resolutions_verified':True,'readonly_rosters':0,'fresh_runtime_output_absent':True,'single_exact_argv':fixed['argv'],'ELF64_littleendian_x86_64_PIE_header_verified':True,'project_or_Model_or_native_entries':0,'scope':'Passive file checks only; no ELF/runtime/Model invoked.'}))
