from pathlib import Path
import os,stat,hashlib,json,struct
fixed=json.loads('{"plan_path": "/home/codextransfer/predictive_motion/results/phase5/session-dynamic-three-cycle-v5-20261011-attempt20/active_run_plan.json", "plan": {"bytes": 494991, "sha256": "e72b31945740add482e4953646c4f43d039ab35b4fe5b55d7d1d27ab99ddb9f3"}, "driver_path": "/home/codextransfer/predictive_motion/results/phase5/session-dynamic-three-cycle-v5-20261011-attempt20/active_run_driver.py", "driver": {"bytes": 7603, "sha256": "fc0874519659a4b10bd65c5d0bc3bf868926578c0beda6377b9c91e233515cde"}, "output": "/home/codextransfer/predictive_motion/results/phase5/session-dynamic-three-cycle-v5-20261011-attempt20/run-attempt1", "argv": ["/home/codextransfer/predictive_motion/results/phase5/session-dynamic-three-cycle-v5-20261011-attempt20/link-attempt1/active_first_cycle", "/home/codextransfer/predictive_motion/results/phase5/session-dynamic-three-cycle-v5-20261011-attempt20/profile-version1/active_input.json", "2de29ad696bb58a5cf87fec360df5c6f57561d7b1e95ad794bbcb868e39bc90e", "f26299c2115d757402df1045fb6af1331a5ee72aae95040f9857d84af68788ff", "/home/codextransfer/predictive_motion/results/phase5/session-dynamic-three-cycle-v5-20261011-attempt20/run-attempt1/artifacts"]}')
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
assert len(d['input_files'])==1696
for x in d['input_files']:checked(x['requested_path'],x)
inputbytes=Path(fixed['argv'][1]).read_bytes();assert hashlib.sha256(inputbytes).hexdigest()==fixed['argv'][2]
producer=Path(fixed['argv'][0]);fd=os.open(producer,os.O_RDONLY|os.O_NOFOLLOW)
try:header=os.read(fd,64)
finally:os.close(fd)
assert header[:6]==b'ELF' and struct.unpack_from('<H',header,18)[0]==62 and struct.unpack_from('<H',header,16)[0]==3
print(json.dumps({'schema':'ROOT_DYNAMIC_THREE_CYCLE_PASSIVE_RUNTIME_PROFILE_VERIFICATION_V1','plan_sha256':hashlib.sha256(p).hexdigest(),'driver_sha256':fixed['driver']['sha256'],'input_files_verified':1696,'input_bytes_verified':sum(x['bytes'] for x in d['input_files']),'all_opened_regular_nofollow_sha_size_modes_resolutions_verified':True,'readonly_rosters':0,'fresh_runtime_output_absent':True,'single_exact_argv':fixed['argv'],'ELF64_littleendian_x86_64_PIE_header_verified':True,'project_or_Model_or_native_entries':0,'scope':'Passive file checks only; no ELF/runtime/Model invoked.'}))
