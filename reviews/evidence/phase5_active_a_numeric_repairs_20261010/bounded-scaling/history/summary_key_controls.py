"""Independent saved-IEEE algebra only; never calls a model, solver or native binary."""
import hashlib, json, struct, time
from pathlib import Path
import numpy as np

OUT=Path(__file__).resolve().parent
PACK=Path('/private/tmp/phase5_active_a_numeric_repair_checkpoint_v2_20261010')
OLD=Path('/private/tmp/phase5_active_a_functional_checkpoint_v1_20261010_collection2')
START_SOURCE=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
t0=time.monotonic()
pins={}
def pin(path,expected=None):
 b=path.read_bytes(); h=hashlib.sha256(b).hexdigest()
 if expected is not None: assert h==expected,(str(path),h,expected)
 pins[str(path)]={'bytes':len(b),'sha256':h}
 return b
ready=pin(PACK/'ACTIVE_A_NUMERIC_REPAIR_CHECKPOINT_READY.json','2e84145e5d8cfe6c69f955d2b0054b0bd76eca8267fc978bf8ba8cace1e071f4')
manifest=json.loads(ready)['files']
def payload(rel):
 v=manifest[rel];b=pin(PACK/rel,v['sha256']);assert len(b)==v['bytes'];return b
sm=payload('source-review-frozen/SOURCE_MANIFEST.json')
assert hashlib.sha256(sm).hexdigest()=='97af4ff02f2791ba67fa7d554481528690b11184e3f673d91e48d829c376cc3f'
for rel,v in json.loads(sm).items():
 b=payload('source-review-frozen/'+rel);assert len(b)==v['bytes']
backend=pin(OUT/'backend_source_read_snapshot.cpp','7f0b10b09c66c078e2342ebd1cc44ba636f76a59c5d908b0a15392ea6d589507')
plan=json.loads(payload('actual-dell/repair14/active_run_plan.json'))
bp=[x for x in plan['input_files'] if x['requested_path'].endswith('/backend/reactive_qp.cpp')]
assert len(bp)==1 and bp[0]['sha256']==hashlib.sha256(backend).hexdigest() and bp[0]['bytes']==len(backend)
prefix='actual-dell/repair14/run-attempt1/artifacts/'
class Reader:
 def __init__(self,b,role):
  self.b=b;self.i=0;assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1';assert self.text()==role
 def u(self):
  assert self.i+8<=len(self.b);v=struct.unpack_from('<Q',self.b,self.i)[0];self.i+=8;return v
 def signed(self):
  v=self.u();return v-(1<<64) if v>=(1<<63) else v
 def d(self):
  assert self.i+8<=len(self.b);v=struct.unpack_from('<d',self.b,self.i)[0];self.i+=8;return v
 def text(self):
  n=self.u();assert n<=len(self.b)-self.i;v=self.b[self.i:self.i+n].decode();self.i+=n;return v
 def nums(self,n):
  assert n<=10_000_000 and self.i+8*n<=len(self.b)
  v=np.frombuffer(self.b,dtype='<f8',count=n,offset=self.i).copy();self.i+=8*n;return v
 def vec(self):return self.nums(self.u())
 def mat(self):r,c=self.u(),self.u();return self.nums(r*c).reshape(r,c)
 def ids(self):return [self.u() for _ in range(self.u())]
 def end(self):assert self.i==len(self.b),(self.i,len(self.b))
def inline(b):
 r=Reader(b,'INLINE_QP_COMPLETE_OR_RETAINED_PREFIX');stage,error=r.text(),r.text();info=[r.u() for _ in range(7)];r.text();r.u()
 for _ in range(3):r.d()
 r.u();H,g,A,l,u=r.mat(),r.vec(),r.mat(),r.vec(),r.vec();r.d();F,f,seed=r.mat(),r.vec(),r.vec();k=r.d();labels=[(r.text(),r.text()) for _ in range(r.u())]
 assert H.shape==(160,160) and A.shape==(13156,160) and F.shape==(741,160) and len(labels)==13156
 assert all(np.isfinite(x).all() for x in [H,g,A,l,u,F,f,seed]) and np.isfinite(k)
 return H,g,A,l,u,F,f,seed,k,labels,info
H,g,A,l,u,F,f,seed,k,labels,inline_info=inline(payload(prefix+'inline_qp.bin'))
oldready=pin(OLD/'ACTIVE_A_FUNCTIONAL_CHECKPOINT_READY.json','25b8572470112ed66f7c3735bca1e58b2aa16ca0ebbeea4bf8c1917de2fc4fdb')
oldm=json.loads(oldready)['files'];oldrel='actual-dell/repair6/run-attempt1/artifacts/inline_qp.bin'
old=inline(pin(OLD/oldrel,oldm[oldrel]['sha256']))
for a,b in zip([H,g,A,l,u,F,f,seed],old[:8]):assert np.array_equal(a,b)
assert k==old[8] and labels==old[9]
r=Reader(payload(prefix+'qp_equality_reduction.bin'),'STRUCTURED_ORIGINAL_TERMINAL_EQUALITY_REDUCTION')
policy,stage=r.text(),r.text();valid=r.u();Z,p,E,rhs=r.mat(),r.vec(),r.mat(),r.vec();eliminated,rows=r.ids(),r.ids()
Hr,gr,Ar,lr,ur,D,Fr,seedr,y,yr,R,Hs,gs,As,ls,us,Fs,seeds=(r.mat(),r.vec(),r.mat(),r.vec(),r.vec(),r.vec(),r.mat(),r.vec(),r.vec(),r.vec(),r.vec(),r.mat(),r.vec(),r.mat(),r.vec(),r.vec(),r.mat(),r.vec())
slots=r.u();kr,eorigin,emap,efactor,esfactor=[r.d() for _ in range(5)];r.end()
assert Z.shape==(160,144) and p.shape==(160,) and E.shape==(16,160) and rhs.shape==(16,) and len(rows)==6034
assert len(eliminated)==16 and len(set(eliminated))==16 and len(set(rows))==len(rows)
assert all(np.isfinite(x).all() for x in [Z,p,E,rhs,Hr,gr,Ar,lr,ur,D,Fr,seedr,R,Hs,gs,As,ls,us,Fs,seeds])
assert y.size==0 and yr.size==0 and valid==1
# Build the analytic map from independently located ORIGINAL terminal rows.
eq=[next(i for i,x in enumerate(labels) if x[0]==('terminal/alpha/'+str(j) if j<7 else 'terminal/b')) for j in range(8)]
eq += [next(i for i,x in enumerate(labels) if x[0]==('terminal/command_w/'+str(j) if j<7 else 'terminal/progress_r')) for j in range(8)]
assert eliminated==eq and np.array_equal(E,A[eq]) and np.array_equal(rhs,l[eq]) and np.array_equal(l[eq],u[eq])
Zref=np.zeros((160,144));Zref[:144]=np.eye(144);pref=np.zeros(160)
for j in range(8):
 assert E[j,152+j]==1 and np.count_nonzero(E[j])==1 and rhs[j]==0
 assert E[8+j,144+j]!=0 and np.all(E[8+j,np.arange(160)%8!=j]==0)
 pref[144+j]=rhs[8+j]/E[8+j,144+j];Zref[144+j]=-E[8+j,:144]/E[8+j,144+j]
assert np.array_equal(Z,Zref) and np.array_equal(p,pref)
errors={}
def check(name,a,b):
 assert np.shape(a)==np.shape(b),(name,np.shape(a),np.shape(b))
 e=float(np.max(np.abs(np.asarray(a)-np.asarray(b)))) if np.size(a) else 0.
 errors[name]=e
 assert np.all(np.abs(np.asarray(a)-np.asarray(b))<=1e-11+1e-10*np.abs(b)),(name,e)
check('E_Z',E@Z,np.zeros((16,144)));check('E_p_rhs',E@p,rhs)
check('reduced_H',Hr,Z.T@H@Z);check('reduced_g',gr,Z.T@(g+H@p))
check('reduced_A',Ar,A[rows]@Z);check('reduced_l',lr,l[rows]-A[rows]@p);check('reduced_u',ur,u[rows]-A[rows]@p)
check('reduced_F',Fr,F@Z);check('reduced_seed',seedr,seed[:144]);check('reduced_constant',kr,k+g@p+.5*p@H@p)
check('D',D,1/np.sqrt(np.diag(Hr)));assert np.all(D>0)
AD=Ar*D;Rref=1/np.maximum(1.,np.max(np.abs(AD),axis=1))
check('R',R,Rref);assert np.all(R>0) and np.all(R<=1)
check('scaled_H',Hs,D[:,None]*Hr*D[None,:]);check('scaled_g',gs,D*gr)
check('scaled_A',As,R[:,None]*AD);check('scaled_l',ls,R*lr);check('scaled_u',us,R*ur)
check('scaled_F',Fs,Fr*D);check('scaled_seed',seeds,seedr/D)
check('reduced_factor_gram',Fr.T@Fr,Hr);check('scaled_factor_gram',Fs.T@Fs,Hs)
# Original retained/omitted identities plus full-SI unmeasured semantics.
s=Reader(payload(prefix+'solver_row_screen.bin'),'ORIGINAL_SI_INPUT_BOX_IMPLICATION_SCREEN');sp=s.text();kept,omitted=s.ids(),s.ids();intervals=[s.text() for _ in range(s.u())];env=[s.u() for _ in range(3)];mapping=s.text();mapped=s.signed();fullnote=s.text();scanned=s.u();worst=s.signed();defaultfull=s.d();s.end()
assert kept==rows and len(omitted)==7106 and len(intervals)==7106
assert set(kept)|set(omitted)|set(eliminated)==set(range(13156))
assert not(set(kept)&set(omitted)) and not(set(kept)&set(eliminated))
mandatory=[i for i,x in enumerate(labels) if x[0].startswith(('input/','trust/','keep/'))]
assert all(i in set(kept) for i in mandatory)
assert scanned==0 and worst==-1 and defaultfull==0 and mapped==-1
# Parse actual candidate independently, not the producer outcome summary.
c=Reader(payload(prefix+'candidate.bin'),'SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');stop=c.text()
ints=[c.u() for _ in range(7)];backendworst=c.signed();U=c.vec();floats=[c.d() for _ in range(14)];reuse=[c.u() for _ in range(4)];reset=c.text();counts=[c.u() for _ in range(4)];rowviol=c.vec();mode=c.u();timing=[c.d() for _ in range(4)];ageflags=[c.u() for _ in range(2)];preview=c.u();assert preview==0;tail=c.u();assert tail==0;request=c.u();assert request==0;c.end()
# The fixed integer fields are permission/attempts/entries/status/raw/api/iterations;
# reader consumed max-row separately below, with explicit schema check.
assert ints==[0,1,1,6,7,0,20000] and U.size==0 and rowviol.size==0 and backendworst==-1
assert reuse==[0,0,0,0] and floats[5:9]==[1.,1.,1.,1.] and floats[9:12]==[1e-9,1e-9,.1]
assert all(np.isfinite(x) for x in floats[1:]) and np.isinf(floats[0]) and mode==0
# Fixed bounded algebra test vectors are not prospective model/controller predictions.
tests=[];rng=np.random.default_rng(12102026)
ell=g-F.T@f;klin=k-.5*f@f
for Y in [seeds,np.zeros(144)]+[rng.uniform(-1e-4,1e-4,144) for _ in range(6)]:
 reducedY=D*Y;orig=p+Z@reducedY
 direct=.5*orig@H@orig+g@orig+k;scaled=.5*Y@Hs@Y+gs@Y+kr
 factor=.5*np.linalg.norm(Fs@Y+F@p+f)**2+ell@orig+klin
 e={'objective':abs(direct-scaled),'factor_cost':abs(direct-factor),'gradient':float(np.max(np.abs(D*(Z.T@(H@orig+g))-(Hs@Y+gs)))),'equality':float(np.max(np.abs(E@orig-rhs))),'row_reconstruction':float(np.max(np.abs(As@Y-R*(A[rows]@orig-A[rows]@p)))),'back_transform':float(np.max(np.abs((reducedY/D)-Y)))}
 assert max(e.values())<1e-10;tests.append(e)
outcomes=json.loads(payload('ACTUAL_NUMERIC_REPAIR_OUTCOMES.json'));reported=next(x for x in outcomes if x['version']=='repair14')
assert reported['controls']==[] and reported['backend_primal']==floats[1] and reported['backend_dual']==floats[2]
elf=json.loads(payload('actual-dell/NATIVE_ELF_INDEX.json'))[-1]
run=json.loads(payload('actual-dell/repair14/run-attempt1/compile-1.result.json'));assert run['exit']==1 and run['argv'][3]==elf['sha256']
result={'scope':'INDEPENDENT_ACTUAL_REPAIR14_SAVED_MATRIX_ALGEBRA_AND_READ_ONLY_SOURCE_NO_MODEL_SOLVER_NATIVE','source_sha256':START_SOURCE,'input_pins':pins,'source_manifest_payloads':len(json.loads(sm)),'backend_snapshot_matches_frozen_runtime_pin':True,'native_ELF_record':elf,'native_ELF_bytes_locally_verified':False,'original_array_values_bit_equal_actual_repair6':True,'dimensions':{'original_controls':160,'reduced_controls':144,'original_rows':13156,'solver_rows':len(rows),'omitted':len(omitted),'eliminated':len(eliminated),'cost_factor_rows':len(F)},'errors':errors,'fixed_vector_checks':tests,'D_range':[float(D.min()),float(D.max())],'explicit_R_range':[float(R.min()),float(R.max())],'row_count_explicit_R_less_than_one':int(np.sum(R<1)),'largest_solver_row_norm':float(np.max(np.abs(As))),'stored_numeric_slots':slots,'saved_certificates':{'equality_origin_error':eorigin,'equality_map_error':emap,'factor_error':efactor,'scaled_factor_error':esfactor},'actual_result':{'status':ints[3],'raw_status':ints[4],'api_error':ints[5],'iterations':ints[6],'controls_count':len(U),'scaled_Y_count':len(y),'reduced_Y_count':len(yr),'backend_primal_transformed_units':floats[1],'backend_dual_transformed_units':floats[2],'setup_seconds':floats[3],'solve_seconds':floats[4],'rho_updates':counts[2],'rho_estimate':floats[12],'backend_internal_row_scale':[floats[5],floats[6]],'backend_internal_variable_scale':[floats[7],floats[8]],'preview':preview,'tail':tail,'request':request,'stop_reason':stop},'full_original_SI':{'rows_scanned':scanned,'default_max_field':defaultfull,'worst_row':worst,'interpretation':'UNMEASURED_NO_CANDIDATE_NOT_PASS'},'solver_calls':0,'Model_calls':0,'phase5':'NOT_ACCEPTED','elapsed_seconds':time.monotonic()-t0}
for name,v in pins.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==v['sha256']
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==START_SOURCE
(OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('input_pins','fixed_vector_checks')},indent=2))
