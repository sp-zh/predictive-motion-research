"""Pure saved-matrix validation of the repair12 structured coordinate map."""
import hashlib,json,struct
from pathlib import Path
import numpy as np
SRC=Path('/private/tmp/phase5_active_equality_source_review_repair12_20261010')
PACK=Path('/private/tmp/phase5_active_a_functional_checkpoint_v1_20261010_collection2')
OUT=Path(__file__).resolve().parent
ss=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();mb=(SRC/'SOURCE_MANIFEST.json').read_bytes()
assert len(mb)==2891 and hashlib.sha256(mb).hexdigest()=='6609b307f239a80ac41afac5cf13822b249bd1f5c72c1f50337e5e124ff20aab'
manifest=json.loads(mb)
for n,v in manifest.items():assert hashlib.sha256((SRC/n).read_bytes()).hexdigest()==v['sha256'] and (SRC/n).stat().st_size==v['bytes']
rel='actual-dell/repair6/run-attempt1/artifacts/inline_qp.bin';ready=(PACK/'ACTIVE_A_FUNCTIONAL_CHECKPOINT_READY.json').read_bytes();assert hashlib.sha256(ready).hexdigest()=='25b8572470112ed66f7c3735bca1e58b2aa16ca0ebbeea4bf8c1917de2fc4fdb'
v=json.loads(ready)['files'][rel];b=(PACK/rel).read_bytes();assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
class Reader:
 def __init__(self):self.i=0
 def u(self):v=struct.unpack_from('<Q',b,self.i)[0];self.i+=8;return v
 def d(self):v=struct.unpack_from('<d',b,self.i)[0];self.i+=8;return v
 def text(self):n=self.u();v=b[self.i:self.i+n].decode();self.i+=n;return v
 def nums(self,n):v=np.frombuffer(b,dtype='<f8',count=n,offset=self.i).copy();self.i+=8*n;return v
 def vec(self):return self.nums(self.u())
 def mat(self):r,c=self.u(),self.u();return self.nums(r*c).reshape(r,c)
r=Reader();assert r.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1' and r.text()=='INLINE_QP_COMPLETE_OR_RETAINED_PREFIX';r.text();r.text()
for _ in range(7):r.u()
r.text();r.u()
for _ in range(3):r.d()
r.u();H,g,A,lo,hi=r.mat(),r.vec(),r.mat(),r.vec(),r.vec();r.d();F,f,seed=r.mat(),r.vec(),r.vec();constant=r.d();labels=[(r.text(),r.text()) for _ in range(r.u())]
eq=[next(i for i,x in enumerate(labels) if x[0]==('terminal/alpha/'+str(j) if j<7 else 'terminal/b')) for j in range(8)]+[next(i for i,x in enumerate(labels) if x[0]==('terminal/command_w/'+str(j) if j<7 else 'terminal/progress_r')) for j in range(8)]
E=A[eq];rhs=lo[eq];assert len(set(eq))==16 and np.array_equal(lo[eq],hi[eq])
Z=np.zeros((160,144));Z[:144]=np.eye(144);p=np.zeros(160)
for j in range(8):
 assert E[j,152+j]==1 and np.count_nonzero(E[j])==1 and rhs[j]==0
 pivot=144+j;row=E[8+j];assert row[pivot]!=0 and np.all(row[np.arange(160)%8!=j]==0)
 p[pivot]=rhs[8+j]/row[pivot];Z[pivot]=-row[:144]/row[pivot]
assert np.array_equal(Z[:144],np.eye(144)) and np.array_equal(Z[152:],np.zeros((8,144)))
assert np.max(np.abs(E@Z))<1e-12 and np.max(np.abs(E@p-rhs))<1e-12
# Independent QR subspace/projector reference, not the structured formula.
Q,_=np.linalg.qr(E.T,mode='complete');N=Q[:,16:]
projection=Z@np.linalg.solve(Z.T@Z,Z.T);qr_projection=N@N.T
errors={'nullspace_residual':float(np.max(np.abs(E@Z))),'particular_residual':float(np.max(np.abs(E@p-rhs))),'span_projector_error':float(np.max(np.abs(projection-qr_projection)))}
assert errors['span_projector_error']<1e-12
Hr=Z.T@H@Z;Fr=F@Z;gr=Z.T@(H@p+g);kr=constant+g@p+.5*p@H@p;fr=F@p+f;Ar=A@Z;lr=lo-A@p;ur=hi-A@p
ell=g-F.T@f;kell=constant-.5*f@f
rng=np.random.default_rng(12102026)
max_cost=max_gradient=max_rows=max_last=0.
for y in [seed[:144],np.zeros(144)]+[rng.uniform(-1e-4,1e-4,144) for _ in range(6)]:
 U=p+Z@y
 max_last=max(max_last,float(np.max(np.abs(U[152:]))));assert np.array_equal(U[152:],np.zeros(8))
 direct=.5*U@H@U+g@U+constant;reduced=.5*y@Hr@y+gr@y+kr
 factor=.5*(Fr@y+fr)@(Fr@y+fr)+(Z.T@ell)@y+kell+ell@p
 max_cost=max(max_cost,float(abs(direct-reduced)),float(abs(direct-factor)))
 max_gradient=max(max_gradient,float(np.max(np.abs(Z.T@(H@U+g)-(Hr@y+gr)))))
 max_rows=max(max_rows,float(np.max(np.abs(A@U-(Ar@y+A@p)))))
 assert np.max(np.abs(E@U-rhs))<1e-12
 assert np.all(np.abs(U)<=np.tile([1]*7+[.5],20))
assert max_cost<1e-10 and max_gradient<1e-10 and max_rows<1e-10
eig=np.linalg.eigvalsh(Hr);assert eig.min()>0
# No solver or transformed matrix files; condition numbers are diagnostics only.
result={'scope':'READ_ONLY_REPAIR12_SOURCE_PLUS_ACTUAL_REPAIR6_MATRIX_MAP_CHECK_NOT_NATIVE_REPAIR12_OUTPUT','source_sha256':ss,'source_manifest_sha256':hashlib.sha256(mb).hexdigest(),'source_manifest':manifest,'matrix_identity':v,'old_actual_matrix_source':'repair6; not claimed actual repair12 reduction artifact','equality_original_indices':eq,'reduced_dimension':144,'pivot_columns':list(range(144,152)),'free_columns':list(range(144)),'last8_inputs_literal_zero':True,'seed_recovery_max_error':float(np.max(np.abs(p+Z@seed[:144]-seed))),'errors':{**errors,'objective':max_cost,'gradient':max_gradient,'original_rows':max_rows,'last8_controls':max_last},'actual_rhs_nonzero':bool(np.any(rhs!=0)),'test_vectors':8,'random_seed':12102026,'structured_reduced_H_condition':float(eig.max()/eig.min()),'orthonormal_reduced_H_condition':float(np.linalg.cond(N.T@H@N)),'factor_offset_recorded_by_producer':False,'factor_offset_independently_reconstructed':True,'solver_calls':0,'Model_calls':0,'phase5':'NOT_ACCEPTED'}
for n,v in manifest.items():assert hashlib.sha256((SRC/n).read_bytes()).hexdigest()==v['sha256']
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==ss
(OUT/'map_results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('source_manifest','equality_original_indices','free_columns')},indent=2))
