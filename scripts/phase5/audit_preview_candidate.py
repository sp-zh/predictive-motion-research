#!/usr/bin/env python3
"""Independent lifted-QP candidate KKT and closed-form dynamics audit.

An offline mathematical check, not nonlinear geometry, robot or timing acceptance.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--x',type=Path,required=True)
    p.add_argument('--y',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mesh-seconds',type=float,nargs='+',required=True)
    p.add_argument('--control-dt',type=float,required=True);p.add_argument('--previous-b',type=float,required=True)
    a=p.parse_args()
    if a.output.exists():p.error('Refuse audit overwrite')
    load=lambda name:np.loadtxt(a.snapshot/name,delimiter=',')
    H,A,g,lo,hi=[load(name) for name in ('H.csv','A.csv','g.csv','l.csv','u.csv')]
    x=np.loadtxt(a.x);y=np.loadtxt(a.y);off=load('decision_offset.csv');origin=load('controls_origin.csv')
    q0,v0,acceptedv,pa=[load(name) for name in ('initial_q.csv','initial_v.csv','accepted_v.csv','previous_command_acc.csv')]
    n=len(q0);nx=2*n+2;nu=n+1;N=len(origin)//nu;offset=(N+1)*nx
    mesh=np.array(a.mesh_seconds if len(a.mesh_seconds)>1 else a.mesh_seconds*N)
    if N<1 or len(origin)!=N*nu or len(mesh)!=N or np.any(mesh<=0) or not np.isfinite(mesh).all():raise ValueError('Invalid mesh/controls')
    if len(x)!=offset+N*nu or len(off)!=len(x) or len(y)!=len(lo) or H.shape!=(len(x),len(x)) or A.shape!=(len(lo),len(x)):raise ValueError('Lifted dimensions mismatch')
    if not all(np.isfinite(z).all() for z in (x,y,off,origin,q0,v0,acceptedv,pa,H,A,g)):raise ValueError('Nonfinite candidate/input')
    if not np.isfinite(a.control_dt) or a.control_dt<=0 or not np.isfinite(a.previous_b):raise ValueError('Invalid history interval')
    ax=A@x;viol=float(np.max(np.maximum(np.maximum(lo-ax,ax-hi),0)))
    station=float(np.max(np.abs(H@x+g+A.T@y)))
    controls=x[offset:]+origin;state_error=0.;kin=[];s0,r0=off[nx-2:nx]
    for k in range(N+1):
        t=mesh[:k].sum();q=q0+t*v0;v=v0.copy();s=s0+t*r0;r=r0;start=0.
        for j in range(k):
            h=mesh[j];aj=controls[j*nu:j*nu+n];bj=controls[j*nu+n];moment=h*(t-start-h/2)
            q=q+moment*aj;v=v+h*aj;s+=moment*bj;r+=h*bj;start+=h
        ref=np.r_[q,v,s,r];state_error=max(state_error,float(np.max(np.abs(ref-(x[k*nx:(k+1)*nx]+off[k*nx:(k+1)*nx])))));kin.append(ref)
    vc=v0+a.control_dt*controls[:n];ca=(vc-acceptedv)/a.control_dt;cj=(ca-pa)/a.control_dt
    eq=np.isfinite(lo)&np.isfinite(hi)&(lo==hi);pos=(y>0)&np.isfinite(hi)&(~eq);neg=(y<0)&np.isfinite(lo)&(~eq)
    comp=max(float(np.max(np.abs(y[pos]*(hi[pos]-ax[pos])),initial=0)),float(np.max(np.abs(y[neg]*(lo[neg]-ax[neg])),initial=0)))
    missing=float(np.max(np.abs(y[((~eq)&np.isposinf(hi)&(y>0))|((~eq)&np.isneginf(lo)&(y<0))]),initial=0))
    d={'scope':__doc__.strip(),'status':'QP_ONLY_CHECKS_PASS' if max(viol,station,state_error,comp,missing)<1e-7 else 'FAIL',
       'max_original_row_violation':viol,'physical_stationarity_inf':station,'complementarity_max':comp,'wrong_infinite_bound_dual_max':missing,
       'closed_state_error':state_error,'terminal_velocity_max':float(np.max(np.abs(kin[-1][n:2*n]))),'terminal_progress_speed':float(kin[-1][-1]),
       'first_command_acceleration_max':float(np.max(np.abs(ca))),'first_command_jerk_max':float(np.max(np.abs(cj))),
       'first_progress_acceleration':float(controls[n]),'first_progress_jerk':float((controls[n]-a.previous_b)/a.control_dt),
       'planned_progress':[float(z[-2]) for z in kin],'progress_inputs':[float(controls[j*nu+n]) for j in range(N)],
       'mesh_seconds':mesh.tolist(),'control_dt':a.control_dt,'numpy_version':np.__version__,'nonlinear_validation':'NOT_CHECKED'}
    files=[a.x,a.y,Path(__file__)]+[f for f in sorted(a.snapshot.iterdir()) if f.is_file()]
    d['inputs_sha256']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in d.items() if k!='inputs_sha256'},indent=2));raise SystemExit(0 if d['status']=='QP_ONLY_CHECKS_PASS' else 1)

if __name__=='__main__':main()
