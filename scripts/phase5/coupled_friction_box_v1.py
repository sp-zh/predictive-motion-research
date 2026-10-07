"""Coupled strictly convex box QP; active-face solves and original KKT checks."""
import numpy as np

def solve_box(H,ell,eta,tolerance=1e-10,max_iterations=100):
    H=np.asarray(H,float);ell=np.asarray(ell,float);eta=np.asarray(eta,float);n=len(ell)
    if H.shape!=(n,n) or eta.shape!=(n,) or not all(np.isfinite(x).all() for x in (H,ell,eta)) or np.any(eta<0):raise ValueError('invalid coupled box input')
    symmetric=.5*(H+H.T)
    if np.max(abs(H-H.T))>1e-10:raise ValueError('asymmetric coupled Hessian')
    np.linalg.cholesky(symmetric)
    lower,upper=-eta,eta;x=np.clip(np.linalg.solve(symmetric,-ell),lower,upper)
    status=np.zeros(n,dtype=int);status[x<=lower]=-1;status[x>=upper]=1;status[eta==0]=2
    for iteration in range(1,max_iterations+1):
        free=np.flatnonzero(status==0);bound=np.flatnonzero(status!=0)
        if len(free):
            target=np.linalg.solve(symmetric[np.ix_(free,free)],-ell[free]-symmetric[np.ix_(free,bound)]@x[bound]);direction=target-x[free]
            ratios=np.full(len(free),np.inf);sides=np.zeros(len(free),dtype=int)
            below=target<lower[free];above=target>upper[free]
            ratios[below]=(lower[free][below]-x[free][below])/direction[below];sides[below]=-1
            ratios[above]=(upper[free][above]-x[free][above])/direction[above];sides[above]=1
            alpha=float(np.min(ratios))
            if alpha<1:
                x[free]+=max(0.,alpha)*direction;x=np.clip(x,lower,upper)
                hit=np.flatnonzero(ratios<=alpha+1e-14)
                for j in hit:status[free[j]]=sides[j];x[free[j]]=lower[free[j]] if sides[j]<0 else upper[free[j]]
                continue
            x[free]=target
        gradient=symmetric@x+ell;bad=np.where((status==-1)&(gradient<-tolerance),-gradient,np.where((status==1)&(gradient>tolerance),gradient,0.))
        if np.max(bad)>tolerance:status[int(np.argmax(bad))]=0;continue
        # Use original H, not the symmetrized factorization, for acceptance.
        original=H@x+ell;label=np.zeros(n,dtype=int);label[x<=lower+tolerance]=-1;label[x>=upper-tolerance]=1;label[eta==0]=2
        stationarity=np.where(label==0,abs(original),np.where(label==-1,np.maximum(-original,0),np.where(label==1,np.maximum(original,0),0)))
        violation=float(max(np.max(stationarity),np.max(lower-x),np.max(x-upper),0.))
        if not np.isfinite(x).all() or violation>tolerance:raise ArithmeticError('coupled box original KKT failure')
        return x,{'iterations':iteration,'original_KKT':violation,'branches':label.tolist()}
    raise ArithmeticError('coupled box active-set iteration limit')
