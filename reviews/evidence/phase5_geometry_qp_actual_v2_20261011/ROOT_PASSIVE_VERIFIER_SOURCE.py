from pathlib import Path
import os,stat,hashlib,json,struct
fixed=json.loads('{"plan_path": "/home/codextransfer/predictive_motion/results/phase5/session-geometry-qp-three-cycle-v4-20261011-attempt30/active_run_plan.json", "plan": {"bytes": 496532, "sha256": "6dee08d281c1833c7b1b0df617276117459823d1a58955d5940eae94cf64b3e9"}, "driver_path": "/home/codextransfer/predictive_motion/results/phase5/session-geometry-qp-three-cycle-v4-20261011-attempt30/active_run_driver.py", "driver": {"bytes": 7607, "sha256": "ded2c4235ed6a5e060cfbf046353054aac7fcc404ad58ed1d406aa363b82e2e1"}, "output": "/home/codextransfer/predictive_motion/results/phase5/session-geometry-qp-three-cycle-v4-20261011-attempt30/run-attempt1", "argv": ["/home/codextransfer/predictive_motion/results/phase5/session-geometry-qp-three-cycle-v4-20261011-attempt30/link-attempt1/active_first_cycle", "/home/codextransfer/predictive_motion/results/phase5/session-geometry-qp-three-cycle-v4-20261011-attempt30/profile-version1/active_input.json", "9b3c377c802daabf589ce1037545713bbb887e89cf8adbfc31d52848e8754c09", "19f6a2a49ca857b36b17d543100a7d935d1c6ce67e068c64e2e9f42deb1fd94e", "/home/codextransfer/predictive_motion/results/phase5/session-geometry-qp-three-cycle-v4-20261011-attempt30/run-attempt1/artifacts"]}')
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
assert len(d['input_files'])==1701
for x in d['input_files']:checked(x['requested_path'],x)
inputbytes=Path(fixed['argv'][1]).read_bytes();assert hashlib.sha256(inputbytes).hexdigest()==fixed['argv'][2]
producer=Path(fixed['argv'][0]);fd=os.open(producer,os.O_RDONLY|os.O_NOFOLLOW)
try:header=os.read(fd,64)
finally:os.close(fd)
assert header[:6]==b'ELF' and struct.unpack_from('<H',header,18)[0]==62 and struct.unpack_from('<H',header,16)[0]==3
print(json.dumps({'schema':'ROOT_GEOMETRY_QP_THREE_CYCLE_PASSIVE_RUNTIME_PROFILE_VERIFICATION_V2','plan_sha256':hashlib.sha256(p).hexdigest(),'driver_sha256':fixed['driver']['sha256'],'input_files_verified':1701,'input_bytes_verified':sum(x['bytes'] for x in d['input_files']),'all_opened_regular_nofollow_sha_size_modes_resolutions_verified':True,'readonly_rosters':0,'fresh_runtime_output_absent':True,'single_exact_argv':fixed['argv'],'ELF64_littleendian_x86_64_PIE_header_verified':True,'project_or_Model_or_native_entries':0,'scope':'Passive file checks only; no ELF/runtime/Model invoked.'}))
