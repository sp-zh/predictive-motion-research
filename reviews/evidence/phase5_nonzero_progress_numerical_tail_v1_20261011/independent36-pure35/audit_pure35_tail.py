"""Independent saved-file/source and exact finite-operation audit; no new solver/model/native.
Absolute arithmetic on recorded pure35 U, with preserved zero/reduced failures.
"""
from pathlib import Path
from fractions import Fraction as Q
import hashlib,json,struct,math,sys,importlib.util,csv
import numpy as np
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
P=Path('/private/tmp/phase5_numerical_progress_tail_pure35_review_v1_20261011')
S=Path('/private/tmp/phase5_nonzero_progress_tail_source_review_v1_20261011')
ACT=Path('/private/tmp/phase5_geometry_qp_actual_checkpoint_v1_20261011/actual-dell/session-geometry-qp-three-cycle-v4-20261011-attempt30/run-attempt1/artifacts/cycle-0')
HELPER=Path('/private/tmp/root_independent_geometry_qp_actual_review_20261011/audit_geometry_qp_actual.py')
L=[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40]
def sha(b):return hashlib.sha256(b).hexdigest()
input_pins={}
def pin(p):
 b=p.read_bytes();input_pins[str(p)]={'bytes':len(b),'sha256':sha(b)};return b
def verify(p,expected):
 b=pin(p/'READY.json');assert sha(b)==expected;r=json.loads(b)
 for n,i in r['files'].items():
  a=pin(p/n);assert len(a)==i['bytes'] and sha(a)==i['sha256']
 return r
src=verify(S,'93448302a7db20487babd926f980257686278b750a13916d6d8fe804cebe3eb1')
packet=verify(P,'dfdc8f4e1f774d0a78b9d9797a1c543ef13a722f4c734bea79bf637375816f54')
(OUT/'PURE_READY_SNAPSHOT.json').write_bytes((P/'READY.json').read_bytes())
class Reader:
 def __init__(self,b):self.b=b;self.i=0
 def u(self):v=struct.unpack_from('<Q',self.b,self.i)[0];self.i+=8;return v
 def a(self,n):v=np.frombuffer(self.b,dtype='<f8',count=n,offset=self.i).copy();self.i+=8*n;assert np.isfinite(v).all();return v
 def m(self):n,m=self.u(),self.u();assert n<=20000 and m<=160;return self.a(n*m).reshape(n,m)
 def v(self):return self.a(self.u())
r=Reader(pin(P/'original_input.bin'));assert sha(r.b)=='896943953327260fdf3c7dbc1f337b90e2d4a013bf6a8fa28c37f1d43d32139c'
H,g,A,lo,hi,E,rhs,seed=r.m(),r.v(),r.m(),r.v(),r.v(),r.m(),r.v(),r.v();rows=[r.u() for _ in range(r.u())];assert r.i==len(r.b)
spec=importlib.util.spec_from_file_location('prior_root_file_parser',HELPER);mod=importlib.util.module_from_spec(spec);pin(HELPER);spec.loader.exec_module(mod)
orig=mod.inline_full(pin(ACT/'inline_qp.bin'));red=mod.reduction(pin(ACT/'qp_equality_reduction.bin'));obs=mod.snapshot(pin(ACT/'observation_before.bin'))
for key,x in [('H',H),('g',g),('A',A),('l',lo),('u',hi),('seed',seed)]:assert np.array_equal(orig[key],x),key
assert np.array_equal(E,red['E']) and np.array_equal(rhs,red['rhs']) and rows==[x for x in red['rows'] if x>=0]
assert obs['x'][28]==obs['x'][29]==obs['b']==0
h=.004;Hq=Q(h);dq=Q(.002);K=.5*h*h;Kq=Q(1,2)*Hq*Hq
# Return exactly the absolute binary64 operation-rounding error, without relying on producer certificates.
def err(observed,exact):
 v=abs(Q(observed)-exact)
 assert math.isfinite(observed)
 # All nonzero inexact operations in this concrete trace must be normal; exact zero permitted.
 if v:assert abs(observed)>=sys.float_info.min and v<=Q(1,2**53)*abs(exact)
 return v
results=[]
for name,target in [('zero',0.),('reduced',1e-18),('planning',1e-13)]:
 data=pin(P/'pure35/pure-margin-cases-v1'/f'{name}.stdout');lines=data.decode().splitlines()
 U=np.array([float(x) for x in next(x for x in lines if x.startswith('U,')).split(',')[1:]]);assert U.shape==(160,) and np.isfinite(U).all()
 macros=[x.split(',') for x in lines if x.startswith('progress_point,')];refs=[x.split(',') for x in lines if x.startswith('reference_point,')];assert len(macros)==200 and len(refs)==400
 targetline=next(x for x in lines if x.startswith('target,')).split(',');assert float(targetline[1])==target
 # Original E and the planning offset are distinct and use the original IEEE coefficients.
 planning_rhs=rhs.copy();planning_rhs[15]+=target;p=np.zeros(160)
 for j in range(8):p[144+j]=float(rhs[8+j]/E[8+j,144+j])
 p[151]=float(planning_rhs[15]/E[15,151])
 difference=planning_rhs-rhs;assert np.count_nonzero(difference)==int(target!=0) and difference[15]==target
 origin_error=float(np.max(np.abs(E@p-rhs)));assert origin_error<=1e-12
 assert abs(origin_error-float(targetline[3]))<=1e-28
 exact_E=sum((Q(float(E[15,j]))*Q(float(U[j])) for j in range(160)),Q(0))-Q(float(rhs[15]))
 violations=np.maximum(0,np.maximum(lo-A@U,A@U-hi));fullSI=float(violations.max());assert fullSI<=1e-7
 # Independent literal joint history: no predictor, no clamp, original actual30 accepted inputs.
 C=obs['x'][14:21].copy();w=obs['x'][21:28].copy();pa=obs['alpha'].copy();command_fail=[]
 for k,n in enumerate(L):
  for cyc in range(n):
   for j in range(7):
    alpha=float(U[8*k+j]);nw=float(w[j]+h*alpha);nc=float(C[j]+h*nw);im=float((nw-w[j])/h);jerk=float((im-pa[j])/h)
    if abs(alpha)>1 or abs(im)>1 or abs(jerk)>20 or abs(nw)>.0625:command_fail.append([k,cyc,j,alpha,im,jerk,nw])
    w[j]=nw;C[j]=nc;pa[j]=im
 # Exact underlying polynomial and rigorous sum-of-operation-error propagation for saved finite trace.
 sf=rf=0.;sq=rq=Q(0);Bs=Br=Q(0);mi=ri=0;first_bad=None;valid_m=valid_r=0;maxref_s=maxref_r=Q(0);records=[];prior_b=0.;jerk_bad=[]
 for k,n in enumerate(L):
  b=float(U[8*k+7]);bq=Q(b);os,orr=sf,rf;oqs,oqr=sq,rq;oBs,oBr=Bs,Br
  for cyc in range(n):
   if abs(b)>.5 or abs((b-prior_b)/h)>5:jerk_bad.append([k,cyc])
   for half in (1,2):
    rr=refs[ri];assert [int(x) for x in rr[1:4]]==[k,cyc,half]
    dt,record_os,record_or,sout,rout=map(float,rr[4:]);assert record_os==os and record_or==orr
    ta=h*cyc;tb=.002*half;t=ta+tb;assert dt==t
    tq=Hq*cyc+dq*half;Bt=err(ta,Hq*cyc)+err(tb,dq*half)+err(t,Q(ta)+Q(tb))
    tr=t*orr;ht=.5*t;tt=ht*t;quad=tt*b;su=os+tr;sr=su+quad;rb=t*b;rref=orr+rb
    assert sr==sout and rref==rout
    # Local quadratic coefficient rounding, with each product's actual downstream magnitude.
    ls=err(tr,Q(t)*Q(orr))+err(ht,Q(1,2)*Q(t))*abs(Q(t)*bq)+err(tt,Q(ht)*Q(t))*abs(bq)+err(quad,Q(tt)*bq)+err(su,Q(os)+Q(tr))+err(sr,Q(su)+Q(quad))
    lr=err(rb,Q(t)*bq)+err(rref,Q(orr)+Q(rb))
    sb=oBs+abs(Q(t))*oBr+Bt*abs(oqr)+Q(1,2)*Bt*(abs(Q(t))+abs(tq))*abs(bq)+ls
    rbnd=oBr+Bt*abs(bq)+lr
    ideals=oqs+tq*oqr+Q(1,2)*tq*tq*bq;idealr=oqr+tq*bq
    assert abs(Q(sr)-ideals)<=sb and abs(Q(rref)-idealr)<=rbnd
    maxref_s=max(maxref_s,sb);maxref_r=max(maxref_r,rbnd)
    valid=int(0<=sr<=1 and 0<=rref<=.2);valid_r+=valid
    if not valid and first_bad is None:first_bad=['half',k,cyc,half,sr,rref]
    records.append([ri,k,cyc,half,dt,sr,rref,float(sb),float(rbnd),valid]);ri+=1
   mm=macros[mi];assert [int(x) for x in mm[1:3]]==[k,cyc]
   s0,r0,ns,nr=map(float,mm[3:]);assert (s0,r0)==(sf,rf)
   hr=h*rf;kb=K*b;tmp=sf+hr;news=tmp+kb;hb=h*b;newr=rf+hb;assert ns==news and nr==newr
   ls=err(hr,Hq*Q(rf))+err(kb,Q(K)*bq)+err(tmp,Q(sf)+Q(hr))+err(news,Q(tmp)+Q(kb))
   lr=err(hb,Hq*bq)+err(newr,Q(rf)+Q(hb))
   Bs=Bs+abs(Hq)*Br+abs(Q(K)-Kq)*abs(bq)+ls;Br+=lr
   sq,rq=sq+Hq*rq+Kq*bq,rq+Hq*bq;sf,rf=news,newr;prior_b=b
   assert abs(Q(sf)-sq)<=Bs and abs(Q(rf)-rq)<=Br
   valid=int(0<=sf<=1 and 0<=rf<=.2);valid_m+=valid
   if not valid and first_bad is None:first_bad=['macro',k,cyc,sf,rf]
   mi+=1
 mapping=abs(exact_E-Q(target));coeff=abs(rq-exact_E);tailbound=mapping+coeff+Br;assert abs(Q(rf)-Q(target))<=tailbound
 # A second independent textbook gamma bound on the multiply/add accumulation.
 gamma=400*Q(1,2**53)/(1-400*Q(1,2**53));gammab=gamma*sum((Hq*n*abs(Q(float(U[8*k+7]))) for k,n in enumerate(L)),Q(0));assert abs(Q(rf)-rq)<=gammab
 producer=json.loads((P/'pure35/pure-margin-cases-v1'/f'{name}.ROUNDING_CERTIFICATE.json').read_text());assert producer['terminal_r']==rf and producer['valid_reference_domains']==valid_r
 if name=='planning':assert valid_m==200 and valid_r==400 and not command_fail and not jerk_bad and Q(target)>tailbound
 with (OUT/f'{name}_reference_bounds.csv').open('w',newline='') as f:
  wr=csv.writer(f);wr.writerow(['sample','cell','cycle0','half','cell_local_clock_s','pure_s','pure_r','independent_s_error_bound','independent_r_error_bound','domain_valid']);wr.writerows(records)
 results.append({'case':name,'target':target,'terminal_s':sf,'terminal_r':rf,'full_original_SI_max':fullSI,'original_Ep_rhs_max':origin_error,'original_E_exact_r_residual':float(abs(exact_E)),'planning_E_exact_r_residual':float(mapping),'original_E_vs_exact_clock_difference':float(coeff),'all200_rounding_r_bound':float(Br),'all200_rounding_s_bound':float(Bs),'max400_reference_s_bound':float(maxref_s),'max400_reference_r_bound':float(maxref_r),'total_tail_target_distance_bound':{'num':str(tailbound.numerator),'den':str(tailbound.denominator),'upper':math.nextafter(float(tailbound),math.inf)},'certified_terminal_r_lower':float(Q(target)-tailbound),'gamma400_bound':float(gammab),'macro_valid':valid_m,'reference_valid':valid_r,'first_progress_domain_failure':first_bad,'command_history_failures':command_fail,'progress_jerk_failures':jerk_bad,'source_stdout_sha256':sha(data)})
# Freeze source/data identity before publishing results.
for path,info in input_pins.items():
 b=Path(path).read_bytes();assert len(b)==info['bytes'] and sha(b)==info['sha256']
result={'schema':'ROOT_SOURCE36_PURE35_FINITE_IEEE_REVIEW_V1','source_payload_count':len(src['files']),'source_payload_bytes':sum(x['bytes'] for x in src['files'].values()),'pure_payload_count':len(packet['files']),'pure_payload_bytes':sum(x['bytes'] for x in packet['files'].values()),'cases':results,'input_pins':input_pins,'new_Model_native_Scene_FK_compiler_optimizer_calls':0,'scope':'saved30 pure35 algebra/finite arithmetic and finalsource36 only; no genuine36 forecast, task execution, stop or Phase5 acceptance'}
(OUT/'INDEPENDENT_PURE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ['case','terminal_r','full_original_SI_max','macro_valid','reference_valid','certified_terminal_r_lower','command_history_failures']} for r in results]))
