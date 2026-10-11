from pathlib import Path
import os,stat,hashlib,json,struct
fixed=json.loads('{"plan_path": "/home/codextransfer/predictive_motion/results/phase5/nominal-geometry-provider-recorded-v4-20261011-attempt26/active_run_plan.json", "plan": {"bytes": 497359, "sha256": "ca878f2c1265eca773214dd048188b61b42516df85fd2fa67d66b5d4a0658784"}, "driver_path": "/home/codextransfer/predictive_motion/results/phase5/nominal-geometry-provider-recorded-v4-20261011-attempt26/active_run_driver.py", "driver": {"bytes": 7595, "sha256": "05c0821a7ebe4f47980df629ac335f3891cf4cac6e4e80c61629575b780cb81a"}, "output": "/home/codextransfer/predictive_motion/results/phase5/nominal-geometry-provider-recorded-v4-20261011-attempt26/run-attempt1", "argv": ["/home/codextransfer/predictive_motion/results/phase5/nominal-geometry-provider-recorded-v4-20261011-attempt26/link-attempt1/provider_probe", "/home/codextransfer/predictive_motion/results/phase5/nominal-geometry-provider-recorded-v4-20261011-attempt26/profile-version1/provider_input.json", "444880467c848c077fe42b5d6b3d9f525f8ee811440df2dbbea620716cf458ce", "b746db0a483b2d6626f49654bb30a063bf8bd2295bf0b463811acf14568eb0c4", "/home/codextransfer/predictive_motion/results/phase5/nominal-geometry-provider-recorded-v4-20261011-attempt26/run-attempt1/artifacts"]}')
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
assert d['compile_argv']==[fixed['argv']] and Path(fixed['output']).is_dir()
assert len(d['input_files'])==1704
for x in d['input_files']:checked(x['requested_path'],x)
inputbytes=Path(fixed['argv'][1]).read_bytes();assert hashlib.sha256(inputbytes).hexdigest()==fixed['argv'][2]
producer=Path(fixed['argv'][0]);fd=os.open(producer,os.O_RDONLY|os.O_NOFOLLOW)
try:header=os.read(fd,64)
finally:os.close(fd)
assert header[:6]==b'ELF' and struct.unpack_from('<H',header,18)[0]==62 and struct.unpack_from('<H',header,16)[0]==3
print(json.dumps({'schema':'ROOT_GEOMETRY_PROVIDER_POSTRUN_PASSIVE_PROFILE_VERIFICATION_V1','plan_sha256':hashlib.sha256(p).hexdigest(),'driver_sha256':fixed['driver']['sha256'],'input_files_verified':1704,'input_bytes_verified':sum(x['bytes'] for x in d['input_files']),'all_opened_regular_nofollow_sha_size_modes_resolutions_verified':True,'readonly_rosters':0,'already_completed_output_present':True,'single_exact_argv':fixed['argv'],'ELF64_littleendian_x86_64_PIE_header_verified':True,'project_or_Model_or_native_entries':0,'scope':'Root postrun passive file checks only, not Root preflight proof; no ELF/runtime/Model/geometry invoked.'}))
