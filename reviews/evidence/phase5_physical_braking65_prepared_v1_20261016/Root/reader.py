"""Independent saved-byte parser and scalar replay, never calls a Model/controller."""
from pathlib import Path
import math
import numpy as np
import root63_nominal_reader_v4 as old
ROLE='STOP_COST_SAME_BOUNDARY_PHYSICAL_DOUBLEHAT_AND_FIRST_PROGRESS_BAND_V5'

def parse(path, source_complete=True):
 raw,receipt=old.strict.verify_artifact(path,collect=True,require_source_complete=source_complete)
 assert len(raw)<=131072
 r=old.R(raw,ROLE)
 out=dict(cycle=r.u(),stop=r.u(),factors=r.u(),weights=r.take('<5d'),objective=r.text())
 assert out['stop']==1 and out['factors']==909 and out['weights']==(100.,1000.,1000.,0.,0.)
 for k in ['trial','regenerate','ordinal','max_families','max_attempts','max_builds','precharge']:out[k]=r.u()
 assert [out[k]for k in ['max_families','max_attempts','max_builds','precharge']]==[149,1080,89,2048]
 assert out['trial']<3 and out['regenerate']==int(out['trial']==0) and 0<out['ordinal']<=89
 out['policies']=r.take('<4d');assert out['policies']==(2e-7,1e-7,.75e-7,.02)
 for k in ['C','w','alpha','q','v','baseline_offset','target']:out[k]=list(r.take('<7d'))
 out['s'],out['r'],out['b']=r.take('<3d')
 assert r.take('<3Q')==(0,0,1)
 expected=np.array(out['q'])+np.array(out['baseline_offset'])-.02*np.array(out['v'])
 assert np.array_equal(expected,np.array(out['target']))
 records=[];terminal=False
 while r.at<len(raw):
  if len(raw)-r.at<8:break
  tag=r.u()
  if tag==0:terminal=True;break
  assert tag==1 and len(records)<1080
  if len(raw)-r.at<104:break
  rec=r.take('<5Q8d');c,f,reason,cell,step,*vals=rec
  assert c<8 and f<(149 if c==7 else 133) and reason<=13 and cell<=20 and step<40
  if records:
   last=records[-1]
   assert (c==last[0] and f==last[1]+1)or(c==last[0]+1 and f==0)
  else:assert c==f==0
  assert reason==1 or all(math.isfinite(x)for x in vals)
  records.append(rec)
 out.update(records=records,source_complete=source_complete,terminal=terminal,raw_bytes=len(raw),receipt=receipt)
 if not terminal:
  assert not source_complete
  return out
 assert source_complete
 out['complete'],count=r.take('<2Q');assert count==len(records)
 out['summary']=[r.take('<2Q3d')for _ in range(8)]
 assert r.take('<2Q')==(20,8)
 out['controls']=np.array(r.take('<160d')).reshape(20,8);out['scope']=r.text();r.end()
 if not out['regenerate']:
  assert not records and out['complete']==0 and all(s==(0,0,0.,0.,0.)for s in out['summary'])
 else:
  assert out['complete']==1 and np.isfinite(out['controls']).all() and np.array_equal(out['controls'][-1],np.zeros(8))
  for c,summary in enumerate(out['summary']):
   own=[x for x in records if x[0]==c];assert own
   if c<7:
    assert [x[1]for x in own[:132]]==list(range(132))
    valid=[x for x in own[:132]if x[2]==0]
    if valid:
     assert len(own)==132
     selected=min(valid,key=lambda x:x[7])
    else:
     assert len(own)==133 and own[-1][1:3]==(132,0)
     selected=own[-1]
   else:
    assert own[-1][2]==0 and all(x[2]!=0 for x in own[:-1])
    selected=own[-1]
   assert summary==(selected[1],len(own),selected[5],selected[6],selected[8])
 return out

def integrate(u,w,C):
 for a,m in zip(u,old.MESH):
  for _ in range(m):w=w+.004*a;C=C+.004*w
 return w,C

def replay(o,constants,warm=None):
 controls={};independent_error=0.;valid_counts=[0]*8
 for rec in o['records']:
  c,f,reason,cell,step,p1,p2,score,last_rate,last_position,max_jerk,observed,bound=rec
  prog=c==7;rate=o['r']if prog else o['w'][c];prior=o['b']if prog else o['alpha'][c];pos=o['s']if prog else o['C'][c]
  warm_case=f==(148 if prog else 132);early=None
  if warm_case:
   assert warm is not None and np.shape(warm)==(20,8),'genuine previous accepted candidate required for warm family'
   u=np.asarray(warm)[:,c];P1=P2=0.;target=0.
  elif prog:
   target=2e-7;P2=0.
   if f<132:u,P1=old.family(rate,prior,target,f)
   else:u,P1,early=old.envelope(rate,prior,target,f-132,pos)
  else:
   L=old.LENGTHS[f//11];M=old.SUPPORTS[f%11];peak=(M-1)//2
   base=[prior*max(0.,1.-(k+1)/L)for k in range(20)]
   a=[min((k+1)/(peak+1),(M-k)/(M-peak))if k<M else 0. for k in range(20)]
   b=[a[18-k]if k<19 else 0. for k in range(20)]
   bw,bc=integrate(base,rate,pos);wa,ca=integrate(a,0.,0.);wb,cb=integrate(b,0.,0.)
   det=wa*cb-wb*ca;scale=abs(wa*cb)+abs(wb*ca)
   if not scale>0 or abs(det)<=1e-10*scale:
    assert reason==11 and (cell,step)==(0,0) and p1==p2==score==max_jerk==0 and last_rate==rate and last_position==pos
    assert observed==det and bound==1e-10*scale
    continue
   P1=((-bw)*cb-(o['target'][c]-bc)*wb)/det
   P2=(wa*(o['target'][c]-bc)-ca*(-bw))/det
   independent=np.linalg.solve(np.array([[wa,wb],[ca,cb]]),np.array([-bw,o['target'][c]-bc]))
   independent_error=max(independent_error,float(np.max(np.abs(independent-[P1,P2]))))
   u=[base[k]+P1*a[k]+P2*b[k]for k in range(20)];target=0.
  proof=early if early is not None else old.check(u,rate,prior,pos,prog,0. if prog else constants['control_range'][2*c],0. if prog else constants['control_range'][2*c+1],target,warm_case)
  pr=list(proof)
  if pr[0]==0 and not prog and not warm_case and abs(pr[4]-o['target'][c])>1e-12:pr[0]=13;pr[6]=abs(pr[4]-o['target'][c]);pr[7]=1e-12
  if pr[0]==0 and prog and rate+.004*u[0]<1e-7:pr[0:3]=[12,0,0];pr[6]=rate+.004*u[0];pr[7]=1e-7
  expected_score=abs(pos+.004*(rate+.004*u[0])-o['target'][c])if pr[0]==0 and not prog else 0.
  assert tuple(pr[:3])==(reason,cell,step),(c,f,pr[:3],rec[:5])
  for x,y in zip([p1,p2,score,last_rate,last_position,max_jerk,observed,bound],[P1,P2,expected_score,*pr[3:]]):
   assert x==y or abs(x-y)<=1e-12*max(1.,abs(x),abs(y)),(c,f,x,y)
  if reason==0:
   valid_counts[c]+=1;controls[(c,f)]=u
 if o['terminal']and o['regenerate']:
  for c,s in enumerate(o['summary']):assert np.allclose(o['controls'][:,c],controls[(c,s[0])],rtol=0.,atol=1e-12)
 return dict(records_replayed=len(o['records']),valid_counts=valid_counts,independent_2x2_error_inf=independent_error,source_complete=o['source_complete'],terminal=o['terminal'],scope='literal scalar/provenance/family arithmetic only; no Model/SI/B/C/actual stop acceptance')
