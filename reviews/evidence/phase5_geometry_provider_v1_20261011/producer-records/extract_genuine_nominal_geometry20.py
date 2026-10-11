from pathlib import Path
import json,struct,hashlib,math
P=Path('/private/tmp/phase5_dynamic_session_checkpoint_v1_20261011');O=Path('/private/tmp/phase5_nominal_geometry_provider_active_v2_20261011');ROOT=P/'actual-dell/session-dynamic-three-cycle-v5-20261011-attempt20/run-attempt1/artifacts'
class R:
 def __init__(self,p):self.b=p.read_bytes();self.i=0
 def raw(self,n):x=self.b[self.i:self.i+n];assert len(x)==n;self.i+=n;return x
 def u(self):return struct.unpack('<Q',self.raw(8))[0]
 def f(self):return struct.unpack('<d',self.raw(8))[0]
 def text(self):n=self.u();assert n<=1024*1024;return self.raw(n).decode()
 def vec(self):n=self.u();assert n<=2000000;return [self.f() for _ in range(n)]
 def fixedstate(self):return {**{k:[self.f() for _ in range(7)] for k in ['q','v','C','w']},'s':self.f(),'r':self.f()}
 def state(self):return {**{k:self.vec() for k in ['q','v','C','w']},'s':self.f(),'r':self.f()}
 def matrix_skip(self):r,c=self.u(),self.u();assert r*c<=2000000;self.raw(r*c*8);return [r,c]
 def identity(self):return {'path':self.text(),'sha256':self.text(),'bytes':self.u()}
 def metadata(self):
  out={'pinocchio_version':self.text(),'nq':self.u(),'nv':self.u()}
  for k in ['joint_names','frame_names']:out[k]=[self.text() for _ in range(self.u())]
  for k in ['idx_q','idx_v','joint_nq','joint_nv']:out[k]=[self.u() for _ in range(self.u())]
  for k in ['masses','armature','gravity','R','B','damping']:out[k]=self.vec()
  return out
out={'schema':'EXACT_GENUINE_NOMINAL_Q400_X3_GEOMETRY_INPUT_V1','source_packet_READY_sha256':hashlib.sha256((P/'READY.json').read_bytes()).hexdigest(),'cycles':[]}
for cycle in range(3):
 d=ROOT/f'cycle-{cycle}';path=d/'original_nominal.bin';q=R(path);assert q.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1' and q.text()=='ORIGINAL_GENUINE_NOMINAL_BEFORE_ADAPTER';row={'cycle':cycle,'nominal_file_sha256':hashlib.sha256(q.b).hexdigest(),'nominal_file_bytes':len(q.b),'original_remote_nominal_path':f'/home/codextransfer/predictive_motion/results/phase5/session-dynamic-three-cycle-v5-20261011-attempt20/run-attempt1/artifacts/cycle-{cycle}/original_nominal.bin','transport_error':q.text(),'structural_refusal':q.text(),'nominal_invocation_sha256':q.text(),'units':q.text(),'certificate':q.text(),'pins':[q.identity() for _ in range(4)],'session_id':q.text()}
 for group in ['dependencies','loaded_libraries']:row[group]=[q.identity() for _ in range(q.u())]
 row['metadata']=q.metadata();row['actual_initial']=q.fixedstate();row['previous_alpha']=[q.f() for _ in range(7)];row['previous_b']=q.f();row['bound_startup']=q.u();row['lattice']=[q.u() for _ in range(q.u())];row['nominal_controls']=[{'cycles':q.u(),'alpha':q.vec(),'b':q.f()} for _ in range(q.u())];assert q.u()==1;row['value_success']=q.u();row['has_final']=q.u();row['value_error']=q.text();row['final']=q.state();row['extension_success']=q.u();row['first_uncertified_u64']=q.u();row['extension_error']=q.text();values=[]
 for _ in range(q.u()):
  v={'cell':q.u(),'cycle':q.u(),'half':q.u(),'elapsed':q.f(),'s':q.f(),'r':q.f()}
  for k in ['q','v','C','w','force']:v[k]=q.vec()
  v['branches']=[q.u() for _ in range(q.u())];v['iterations']=q.u();v['kkt']=q.f();v['control_clips']=q.u();v['force_clips']=q.u();values.append(v)
 for count in [200,20]:assert q.u()==count;states=[q.state() for _ in range(count)]
 assert len(values)==400;row['samples']=[]
 for group,count in [('substep',400),('cycle',200),('cell',20)]:
  assert q.u()==count
  for index in range(count):
   m={'cell':q.u(),'cycle':q.u(),'half':q.u(),'origin':q.state(),'state':q.state(),'cell_origin':q.state(),'input':q.vec()}
   assert [q.matrix_skip() for _ in range(4)]==[[30,30],[30,8],[30,30],[30,8]];q.vec();q.vec()
   if group=='substep':
    v=values[index];assert all(m[k]==v[k] for k in ['cell','cycle','half']);assert struct.pack('<7d',*m['state']['q'])==struct.pack('<7d',*v['q']);assert all(math.isfinite(x) for x in v['q']) and abs(v['elapsed']-.002*(index+1))<=1e-10
    row['samples'].append({'sample':index,'cell':v['cell'],'cycle':v['cycle'],'half':v['half'],'elapsed':v['elapsed'],'q':v['q']})
 assert q.i==len(q.b) and not row['transport_error'] and not row['structural_refusal'] and row['value_success'] and row['extension_success'];out['cycles'].append(row)
p=O/'ACTUAL_NOMINAL_Q400_X3.json';b=(json.dumps(out,indent=2)+'\n').encode();p.write_bytes(b);p.chmod(0o444);print('exact genuine input',len(b),hashlib.sha256(b).hexdigest(),'samples',sum(len(r['samples']) for r in out['cycles']))
