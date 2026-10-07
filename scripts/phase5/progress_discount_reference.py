#!/usr/bin/env python3
"""Offline exact exponential near-term progress objective reference, not trials."""
import math,json,hashlib,argparse
from pathlib import Path

def coefficients(h,tau):
    x=h/tau
    A=-tau*math.expm1(-x)
    if x<1e-3:
        # (1-(1+x)*exp(-x))/x^2, with a stable small-x series.
        series=.5;power=1.;factorial=2.
        for n in range(3,14):
            power*=x;factorial*=n;series+=(-1 if n%2 else 1)*(n-1)*power/factorial
        B=h*h*series
    elif x>700:B=tau*tau
    else:B=tau*tau*(-math.expm1(-x)-x*math.exp(-x))
    return A,B

def integral(mesh,b,initial_r,tau):
    t=0.;r=initial_r;total=0.
    for h,control in zip(mesh,b):
        A,B=coefficients(h,tau);total+=math.exp(-t/tau)*(A*r+B*control);r+=h*control;t+=h
    return total

def numeric(mesh,b,initial_r,tau):
    # Composite Simpson reference on every cell, independent of coefficients.
    t=0.;r=initial_r;total=0.
    for h,control in zip(mesh,b):
        n=20000;dx=h/n;s=0.
        for k in range(n+1):
            u=k*dx;value=math.exp(-(t+u)/tau)*(r+control*u)
            s+=(1 if k in [0,n] else 4 if k%2 else 2)*value
        total+=dx*s/3;t+=h;r+=h*control
    return total

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('Refuse overwrite')
    cases=[]
    for mesh,b,r,tau in [([.04,.02,.08],[.02,-.01,.005],.03,.3),([.004,.036,.06],[.5,-.2,0],.1,10.),([.04,.04],[0.,.1],0.,.03)]:
        exact=integral(mesh,b,r,tau);ref=numeric(mesh,b,r,tau);assert abs(exact-ref)<1e-12;cases.append({'mesh':mesh,'b':b,'r0':r,'tau':tau,'exact':exact,'simpson_reference':ref,'error':abs(exact-ref)})
    A,B=coefficients(.04,1e12);assert abs(A-.04)<1e-12 and abs(B-.0008)<1e-12
    d={'scope':__doc__.strip(),'status':'ANALYTIC_REFERENCE_PASS','formula':'I=sum_k exp(-t_k/tau)*(A(h_k,tau)*r_k+B(h_k,tau)*b_k), A=tau*(1-exp(-h/tau)), B=tau^2*(1-(1+h/tau)*exp(-h/tau)); objective subtracts w_progress*I','undiscounted_limit':'tau→infinity gives integral r dt = s_N-s_0; finite tau rewards earlier progress; no hard minimum speed','cases':cases,'large_tau_limit_error_A':abs(A-.04),'large_tau_limit_error_B':abs(B-.0008),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'policy':'unimplemented development objective candidate only; preserves constraints mathematically but would change optimization preference and must be new frozen protocol'}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print('PROGRESS_DISCOUNT_REFERENCE_PASS cases=3 integration+large_tau_limit')

if __name__=='__main__':main()
