"""Independent retained-data nominal parser/replay, not a controller or Model call."""
from pathlib import Path
import struct,json,hashlib,math,sys
import numpy as np
sys.path.insert(0,'/private/tmp')
import root61_parser_and_formal_review_v1 as m61
strict=m61.strict
ROLE='STOP_COST_AND_CURRENT_HISTORY_FINITE_BRAKING_NOMINAL_FAMILY_DIAGNOSTICS_V2'
MESH=(1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40)
LENGTHS=(1,2,3,4,5,6,7,8,10,12,16,19);SUPPORTS=(2,3,4,5,6,7,8,10,12,16,19)
class R(m61.m60.R):
 def u(self):return self.take('<Q')[0]
 def d(self):return self.take('<d')[0]
def parse(path,source_complete=True):
 b,receipt=strict.verify_artifact(path,collect=True,require_source_complete=source_complete);assert len(b)<=131072;r=R(b,ROLE)
 o=dict(cycle=r.u(),stop=r.u(),factors=r.u(),weights=r.take('<5d'),objective=r.text());assert o['stop']==1 and o['factors']==909 and o['weights']==(100.,1000.,1000.,0.,0.)and 0<len(o['objective'])<=256
 for k in['trial','regenerate','ordinal','max_families','max_attempts','max_builds','precharge']:o[k]=r.u()
 assert o['trial']<3 and o['regenerate']==int(o['trial']==0)and 0<o['ordinal']<=89 and [o[k]for k in['max_families','max_attempts','max_builds','precharge']]==[132,1056,89,2048];o['floor']=r.d();assert o['floor']==1e-8
 for k in['C','w','alpha']:o[k]=list(r.take('<7d'))
 o['s'],o['r'],o['b']=r.take('<3d');records=[];terminal=False
 while r.at<len(b):
  if len(b)-r.at<8:break
  tag=r.u()
  if tag==0:terminal=True;break
  assert tag==1 and len(records)<1056
  if len(b)-r.at<88:break
  row=r.take('<5Q6d');channel,family,reason,cell,step,*values=row;assert channel<8 and family<132 and reason<=8 and cell<=20 and step<40
  if records:
   prior=records[-1];assert(channel==prior[0]and family==prior[1]+1 and prior[2]!=0)or(channel==prior[0]+1 and family==0 and prior[2]==0)
  else:assert channel==family==0
  assert reason==1 or all(math.isfinite(v)for v in values);records.append(row)
 o['records']=records;o['source_complete']=source_complete;o['raw_bytes']=len(b);o['receipt']=receipt
 if not terminal:
  assert not source_complete;o['terminal']=False;return o
 assert source_complete;o['terminal']=True;o['build_complete'],count=r.take('<2Q');assert count==len(records);o['summary']=[r.take('<2Q2d')for _ in range(8)];assert r.take('<2Q')==(20,8);o['controls']=np.array(r.take('<160d')).reshape(20,8);o['scope']=r.text();r.end()
 if not o['regenerate']:assert not records and o['build_complete']==0 and all(e==(0,0,0.,0.)for e in o['summary'])
 else:
  assert o['build_complete']==1 and np.isfinite(o['controls']).all()and np.array_equal(o['controls'][-1],np.zeros(8))
  for c,s in enumerate(o['summary']):
   own=[e for e in records if e[0]==c];assert own and own[-1][2]==0 and all(e[2]for e in own[:-1]);assert(s[0],s[1],s[2],s[3])==(own[-1][1],len(own),own[-1][5],own[-1][6])
 return o

def family(rate,prior,target,index):
 L=LENGTHS[index//11];M=SUPPORTS[index%11];peak=(M-1)//2;base=[];shape=[];change=0.;den=0.
 for k,m in enumerate(MESH):
  b=prior*max(0.,1.-float(k+1)/L);a=min(float(k+1)/(peak+1),float(M-k)/(M-peak))if k<M else 0.;base.append(b);shape.append(a);change+=.004*m*b;den+=.004*m*a
 pulse=(target-rate-change)/den;return [b+pulse*a for b,a in zip(base,shape)],pulse

def check(values,rate,prior,position,progress,lo,hi,target):
 maxjerk=0.;reason=0;cell=step=0;observed=bound=0.
 def result(reason,observed,bound):return(reason,cell,step,rate,position,maxjerk,observed,bound)
 for cell,(a,m)in enumerate(zip(values,MESH)):
  step=0;cap,jcap=(.5,5.)if progress else(1.,20.)
  if not math.isfinite(a):return result(1,a,0)
  if abs(a)>cap*.999:return result(2,abs(a),cap*.999)
  j0=abs((a-prior)/.004)
  if j0>jcap*.999:return result(3,j0,jcap*.999)
  if progress:
   bernstein=position+.5*.004*m*rate
   if not math.isfinite(bernstein)or not 0<=bernstein<=1:return result(6,bernstein,0. if bernstein<0 else 1.)
  for step in range(m):
   if progress:
    for t in[.002,.004]:
     s=position+t*rate+.5*t*t*a;r=rate+t*a
     if not math.isfinite(s)or not 0<=s<=1:return result(6,s,0. if s<0 else 1.)
     if not math.isfinite(r)or not 0<r<=.2:return result(6,r,0. if r<=0 else .2)
    position=position+.004*rate+.5*.004*.004*a;rate=rate+.004*a;j=abs((a-prior)/.004);maxjerk=max(maxjerk,j)
    if j>5:return result(3,j,5.)
    prior=a
   else:
    nxt=rate+.004*a;implied=(nxt-rate)/.004;j=abs((implied-prior)/.004);C=position+.004*nxt
    if not all(map(math.isfinite,[nxt,C,j])):return result(1,0,0)
    if abs(implied)>1:return result(2,abs(implied),1.)
    if j>20:return result(3,j,20.)
    if abs(nxt)>.0625:return result(4,abs(nxt),.0625)
    if C<lo+.005 or C>hi-.005:return result(5,C,lo+.005 if C<lo+.005 else hi-.005)
    rate=nxt;position=C;prior=implied;maxjerk=max(maxjerk,j)
 cell=20;step=0
 if values[-1]!=0:return result(7,values[-1],0)
 if not math.isfinite(rate)or abs(rate-target)>1e-12:return result(8,abs(rate-target),1e-12)
 return result(0,rate,target)

def replay(o,constants):
 ranges=constants['control_range'];counts=[0]*8;successes=[]
 for row in o['records']:
  c,f,reason,cell,step,pulse,last_rate,last_position,maxjerk,observed,bound=row;progress=c==7;rate=o['r']if progress else o['w'][c];prior=o['b']if progress else o['alpha'][c];position=o['s']if progress else o['C'][c];target=min(1e-8,rate)if progress else 0.;u,p=family(rate,prior,target,f);e=check(u,rate,prior,position,progress,0. if progress else ranges[2*c],0. if progress else ranges[2*c+1],target);assert e[:3]==(reason,cell,step),(c,f,e[:3],(reason,cell,step))
  actual=[pulse,last_rate,last_position,maxjerk,observed,bound];expected=[p,*e[3:]];assert len(actual)==len(expected)==6
  for x,y in zip(actual,expected):assert x==y or abs(x-y)<=1e-12*max(1.,abs(x),abs(y)),(c,f,x,y)
  counts[c]+=1
  if reason==0:
   successes.append(c)
   if o.get('terminal')and o['regenerate']:assert np.allclose(o['controls'][:,c],u,rtol=0,atol=1e-14)
 return dict(attempts=len(o['records']),counts_per_channel=counts,successful_channels=successes,every_rejected_reason_location_and_observed_bound_recomputed=True,scope='Independent scalar recurrence/family+codec review only; no Model/native/SI/nonlinear/B/C/physical stop acceptance.')
