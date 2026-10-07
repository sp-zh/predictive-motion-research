#!/usr/bin/env python3
"""Exact rational counterexample and discrete-jerk continuation reference.
No production library/robot calls. Synthetic analytic cases, not robot trials.
"""
from fractions import Fraction as F
import argparse,hashlib,json
from pathlib import Path

def bounds(s,r,prev,dt,vmax,amax,jmax,continuation):
    lo=max(-amax,prev-jmax*dt,-r/dt)
    hi=min(amax,prev+jmax*dt,(vmax-r)/dt,2*(1-s-dt*r)/(dt*dt))
    if continuation:
        horizon=(amax/(jmax*dt)).__ceil__()
        # A ramp from any allowed acceleration reaches zero within this many
        # future steps. Every prefix is checked, including both speed caps.
        for k in range(horizon+1):
            lo=max(lo,-r/(dt*(k+1))-jmax*dt*k/2)
            hi=min(hi,(vmax-r)/(dt*(k+1))+jmax*dt*k/2)
    return lo,hi

def run(continuation):
    s,r,prev,dt,vmax,amax,jmax=map(F,['.1','.001','-.04','.004','.2','.5','5'])
    rows=[];result='NOT_STOPPED'
    for tick in range(50):
        lo,hi=bounds(s,r,prev,dt,vmax,amax,jmax,continuation)
        if lo>hi:
            rows.append({'tick':tick,'feasible':False,'lower':str(lo),'upper':str(hi),'r':str(r),'previous_b':str(prev)});result='INFEASIBLE';break
        b=max(lo,min(hi,-r/dt));new_s=s+dt*r+dt*dt*b/2;new_r=r+dt*b
        assert 0<=new_s<=1 and 0<=new_r<=vmax and abs(b)<=amax and abs((b-prev)/dt)<=jmax
        rows.append({'tick':tick,'feasible':True,'b':str(b),'b_float':float(b),'r_after':str(new_r),'s_after':str(new_s)})
        s,r,prev=new_s,new_r,b
        if r==0 and b==0:result='STOPPED_WITH_ZERO_ACCELERATION';break
    return {'result':result,'steps':rows}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('Refuse overwrite')
    old=run(False);safe=run(True)
    assert old['result']=='INFEASIBLE';assert safe['result']=='STOPPED_WITH_ZERO_ACCELERATION'
    assert [r['b_float'] for r in safe['steps']]==[-.06,-.0775,-.0575,-.0375,-.0175,0.]
    lo,hi=bounds(F('.1'),F('.1995'),F('.10'),F('.004'),F('.2'),F('.5'),F('5'),False)
    vlo,vhi=bounds(F('.1'),F('.1995'),F('.10'),F('.004'),F('.2'),F('.5'),F('5'),True)
    assert lo<=hi and vlo>vhi
    d={'scope':__doc__.strip(),'status':'INDEPENDENT_COUNTEREXAMPLE_AND_REFERENCE_VERIFIED',
      'initial':{'s':'.1','r':'.001','previous_b':'-.04','dt':'.004','speed_cap':'.2','acceleration_cap':'.5','jerk_cap':'5'},
      'old_one_step_greedy':old,'finite_jerk_continuation_reference':safe,
      'upper_speed_case':{'r':'.1995','previous_b':'.1','one_step_feasible':True,'future_speed_cap_viable':False,'viable_lower':str(vlo),'viable_upper':str(vhi)},
      'formula':'For every K>=0, r+dt*(K+1)*b +/- j*dt^2*K*(K+1)/2 must admit nonnegative/below-cap continuation under the corresponding jerk ramp.',
      'scope_limit':'speed/acceleration/jerk continuation and this far-from-end position case; not a universal position/collision/hardware stopping proof',
      'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(d['status']);print('greedy: infeasible after3 braking steps; continuation:5 braking steps then b=0; all exact rational bounds checked')

if __name__=='__main__':main()
