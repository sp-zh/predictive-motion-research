#!/usr/bin/env python3
"""Independent 7D friction-box QP algebra: no fitting or plant prediction."""
import hashlib
import itertools
import json
from pathlib import Path

SOURCE=Path(__file__).resolve()
SOURCE_BYTES=SOURCE.read_bytes()
import numpy as np

INPUT=Path('reviews/evidence/public_coupled_servo_design_review_20261007.json')
INPUT_BYTES=INPUT.read_bytes()
OUT=Path('results/phase5-reference/root-coupled-friction-box-oracle-20261007-v1')
TOL=1e-10

def kkt(H,ell,eta,f,status):
    gradient=H@f+ell
    violation=np.maximum(abs(f)-eta,0.)
    residual=[]
    for i,s in enumerate(status):
        residual.append(abs(gradient[i]) if s==0 else max(0.,-gradient[i]) if s<0 else max(0.,gradient[i]))
    return {'box_violation':float(np.max(violation)),'KKT_residual':float(max(residual)),
            'gradient':gradient.tolist(),'objective':float(.5*f@H@f+ell@f)}

def canonical(f,eta):
    # At an exact threshold use the saturated side. TOL classifies roundoff
    # in this oracle, not an enlargement of the box or a physical tolerance.
    return np.where(f<=-eta+TOL,-1,np.where(f>=eta-TOL,1,0))

def enumerate_box(H,ell,eta):
    assert np.linalg.eigvalsh(H)[0]>0
    candidates=[]
    for status in itertools.product((-1,0,1),repeat=len(eta)):
        status=np.array(status);free=np.flatnonzero(status==0);bound=np.flatnonzero(status!=0)
        f=status*eta
        if free.size:
            f[free]=np.linalg.solve(H[np.ix_(free,free)],-ell[free]-H[np.ix_(free,bound)]@f[bound])
        metrics=kkt(H,ell,eta,f,status)
        if metrics['box_violation']<=TOL and metrics['KKT_residual']<=TOL:
            candidates.append((metrics['objective'],f.copy(),status.copy()))
    assert candidates,'no KKT active set'
    best=min(candidates,key=lambda x:x[0]);f=best[1]
    # SPD gives a unique primal point even when its active-set descriptions tie.
    assert max(np.max(abs(x[1]-f)) for x in candidates)<1e-8
    status=canonical(f,eta)
    metrics=kkt(H,ell,eta,f,status)
    assert metrics['box_violation']<=TOL and metrics['KKT_residual']<=TOL
    return f,status,metrics,len(candidates)

def active_derivative(H,f,status,dH,dell):
    free=np.flatnonzero(status==0);df=np.zeros(len(f))
    if free.size:df[free]=-np.linalg.solve(H[np.ix_(free,free)],(dH@f+dell)[free])
    return df

def main():
    OUT.mkdir(exist_ok=False)
    public=json.loads(INPUT_BYTES)
    M=np.array(public['pinocchio_models']['inspection_mjcf']['M'])
    inv=np.linalg.inv(M);R=np.array(public['regularizer_R'])
    original_H=inv+np.diag(R);H=.5*(original_H+original_H.T)
    eta=np.array(public['compiled_mjModel']['frictionloss'])
    imp=np.array(public['compiled_mjModel']['solimp']).reshape(7,5)
    ref=np.array(public['compiled_mjModel']['solref']).reshape(7,2)
    B=2/(imp[:,1]*ref[:,0]);raw_R=(1-imp[:,0])/imp[:,0]*np.array(public['compiled_mjModel']['invweight0'])
    assert np.max(abs(raw_R-R))<1e-15
    assert np.linalg.eigvalsh(M)[0]>0 and np.linalg.eigvalsh(H)[0]>0
    v=np.array([.01,-.008,.006,-.004,.003,-.002,.001])
    fixtures=[('zero_drive',np.zeros(7),np.zeros(7))]
    for name,s in [('all_lower',-1),('all_upper',1)]:
        f=s*eta;gradient=-s*.7*np.ones(7)
        fixtures.append((name,gradient-H@f,v))
    expected_status=np.array([-1,0,1,0,-1,1,0]);expected_f=expected_status*eta
    expected_f[expected_status==0]=.15*eta[expected_status==0]
    expected_gradient=-expected_status*.4
    mixed_ell=expected_gradient-H@expected_f
    fixtures.append(('strict_mixed_active_set',mixed_ell,v))
    unbounded=eta*np.array([2.,.2,-.15,.1,-.05,.1,-.1])
    fixtures.append(('axis_clip_counterexample',-H@unbounded,v))
    for name,s in [('threshold_lower',-1),('threshold_upper',1)]:
        f=np.zeros(7);f[0]=s*eta[0]
        fixtures.append((name,-H@f,np.zeros(7)))
    reports=[];solved={}
    for name,ell,velocity in fixtures:
        f,status,metrics,valid=enumerate_box(H,ell,eta)
        original_metrics=kkt(original_H,ell,eta,f,status)
        assert original_metrics['KKT_residual']<TOL
        # Represent each declared abstract drive as W*tau+B*v. This is not a
        # claim that tau is an executable actuator command or physical input.
        tau=M@(ell-B*velocity)
        assert np.max(abs(inv@tau+B*velocity-ell))<1e-12
        item={'name':name,'ell':ell.tolist(),'synthetic_velocity':velocity.tolist(),'synthetic_tau_smooth':tau.tolist(),'force':f.tolist(),'status_lower_free_upper':status.tolist(),'original_KKT':original_metrics,'valid_active_set_descriptions':valid}
        if name=='axis_clip_counterexample':
            unconstrained=np.linalg.solve(H,-ell);clipped=np.clip(unconstrained,-eta,eta)
            clip_metrics=kkt(original_H,ell,eta,clipped,canonical(clipped,eta))
            assert clip_metrics['box_violation']==0 and clip_metrics['KKT_residual']>.01
            assert clip_metrics['objective']-original_metrics['objective']>.001
            item['naive_axis_clip']={'unconstrained':unconstrained.tolist(),'force':clipped.tolist(),'original_KKT':clip_metrics,'objective_loss':clip_metrics['objective']-original_metrics['objective'],'max_force_error':float(np.max(abs(clipped-f)))}
        reports.append(item);solved[name]=(f,status,ell)
    f,status,ell=solved['strict_mixed_active_set']
    assert np.array_equal(status,expected_status) and np.max(abs(f-expected_f))<1e-12
    h=1e-6;derivatives=[]
    directions=[]
    for j in (0,3,6):
        direction=np.eye(7)[j];directions.append(('ell_axis_'+str(j),np.zeros((7,7)),direction))
    dH=np.diag(np.linspace(.1,.3,7));dH[1,3]=dH[3,1]=.08
    directions.append(('symmetric_H_direction',dH,np.zeros(7)))
    for name,dH,dell in directions:
        df=active_derivative(H,f,status,dH,dell)
        plus,sp,_,_=enumerate_box(H+h*dH,ell+h*dell,eta)
        minus,sm,_,_=enumerate_box(H-h*dH,ell-h*dell,eta)
        assert np.array_equal(status,sp) and np.array_equal(status,sm)
        fd=(plus-minus)/(2*h);err=float(np.max(abs(fd-df)))
        assert err<1e-7
        derivatives.append({'name':name,'dH':dH.tolist(),'dell':dell.tolist(),'df_exact_fixed_active_set':df.tolist(),'central_FD':fd.tolist(),'max_error':err,'active_set_unchanged':True})
    thresholds=[];direction=np.eye(7)[0]
    for name in ('threshold_lower','threshold_upper'):
        f,status,ell=solved[name]
        plus,sp,_,_=enumerate_box(H,ell+h*direction,eta)
        minus,sm,_,_=enumerate_box(H,ell-h*direction,eta)
        right=(plus-f)/h;left=(f-minus)/h
        convention=active_derivative(H,f,status,np.zeros((7,7)),direction)
        assert np.max(abs(left-right))>.1
        selected=right if name.endswith('lower') else left
        assert np.max(abs(convention-selected))<1e-7
        thresholds.append({'name':name,'canonical_status':status.tolist(),'saturated_side_derivative':convention.tolist(),'right_derivative':right.tolist(),'left_derivative':left.tolist(),'max_side_difference':float(np.max(abs(left-right))),'unique_ordinary_derivative':False})
    result={'status':'PASS_NOMINAL_COUPLED_BOX_QP_ALGEBRA_ONLY','source_sha256':hashlib.sha256(SOURCE_BYTES).hexdigest(),'public_input_sha256':hashlib.sha256(INPUT_BYTES).hexdigest(),'numpy_version':np.__version__,'M':M.tolist(),'R':R.tolist(),'H':H.tolist(),'original_H':original_H.tolist(),'H_symmetrization_max_correction':float(np.max(abs(H-original_H))),'H_eigenvalues':np.linalg.eigvalsh(H).tolist(),'friction_bounds':eta.tolist(),'B_s_inv':B.tolist(),'algorithm':'Exhaustive 3^7 free/lower/upper active sets, free-block linear solve, original box/KKT checks; no production solver','KKT_check_tolerance':TOL,'fixtures':reports,'fixed_active_set_sensitivities':derivatives,'thresholds':thresholds,'limits':['Single public nominal configuration; no physical rollout or prediction accuracy gate','Synthetic drives/velocities are algebra fixtures, not executable actuator inputs','No fitting, model/domain expansion, private plant state, MPC integration, stopping or Phase5 acceptance','Saturated-side threshold Jacobian is a convention; ordinary derivative is not unique']}
    assert SOURCE.read_bytes()==SOURCE_BYTES and INPUT.read_bytes()==INPUT_BYTES
    (OUT/'SOURCE_SNAPSHOT.py').write_bytes(SOURCE_BYTES);(OUT/'PUBLIC_INPUT_SNAPSHOT.json').write_bytes(INPUT_BYTES)
    encoded=json.dumps(result,indent=2)+'\n';(OUT/'oracle.json').write_text(encoded)
    Path('reviews/evidence/coupled_friction_box_root_oracle_20261007.json').write_text(encoded)
    ready={'source_sha256':result['source_sha256'],'public_input_sha256':result['public_input_sha256'],'files':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in OUT.iterdir()}}
    assert SOURCE.read_bytes()==SOURCE_BYTES and INPUT.read_bytes()==INPUT_BYTES
    (OUT/'READY.json').write_text(json.dumps(ready,indent=2)+'\n')
    counter=next(c for c in reports if c['name']=='axis_clip_counterexample')['naive_axis_clip']
    print(json.dumps({'status':result['status'],'fixtures':len(reports),'max_original_KKT_residual':max(x['original_KKT']['KKT_residual'] for x in reports),'clip_counterexample':counter,'max_sensitivity_FD_error':max(x['max_error'] for x in derivatives),'threshold_side_difference':[x['max_side_difference'] for x in thresholds],'source_sha256':result['source_sha256']},indent=2))

if __name__=='__main__':main()
