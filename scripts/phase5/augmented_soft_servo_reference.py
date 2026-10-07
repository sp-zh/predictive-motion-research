#!/usr/bin/env python3
"""Independent augmented soft-servo MODEL oracle; no fitting or physical plant evidence."""
import argparse,hashlib,json
from pathlib import Path
SOURCE_BYTES_AT_START=Path(__file__).read_bytes()
SOURCE_SHA_AT_START=hashlib.sha256(SOURCE_BYTES_AT_START).hexdigest()
import numpy as np

DT=.004;SUB=.002
FROZEN_SHA='984ee85d086aeba7da8260a20b21b301e23dfd2c698a6c61ace0ff956bbec1bb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def cells(mesh):
    output=[]
    for h in mesh:
        m=round(h/DT)
        if m<1 or abs(h-m*DT)>1e-12:raise ValueError('mesh requires positive integer 4ms periods; no remainder policy')
        output.append(m)
    return output


def params(model):
    p=model['public_parameters']
    return [np.array(model[k]) for k in ['mass_effective_kg_m2','bias_Nm']]+[np.array(p[k]) for k in ['kp_Nm_rad','damping_Nm_s_rad','friction_bound_Nm','impedance','reference_decay_s_inv']]


def domain(z,model):
    n=len(model['mass_effective_kg_m2']);q=z[:n];v=z[n:2*n];e=z[2*n:3*n]-q;box=model['local_box']
    if not np.isfinite(z).all() or np.any(q<box['q_min']) or np.any(q>box['q_max']) or np.any(abs(v)>box['v_abs_max']) or np.any(e<box['target_error_min']) or np.any(e>box['target_error_max']) or not(0<=z[-2]<=1 and 0<=z[-1]<=.2):
        raise ValueError('physical q/v/target-error or progress outside declared oracle domain')


def scalar_physical(q,v,c,parameters):
    # Scalar loop is the direct nonlinear reference, independent of matrix code.
    qp=q.copy();vp=v.copy();branch=[]
    for j,(m,g,k,d,eta,imp,b) in enumerate(zip(*parameters)):
        smooth=k*(c[j]-q[j])-d*v[j]+g
        drive=imp*(smooth+m*b*v[j])
        if drive>=eta:force=-eta;regime=1
        elif drive<=-eta:force=eta;regime=-1
        else:force=-drive;regime=0
        vp[j]=v[j]+SUB*(smooth+force)/(m+SUB*d)
        qp[j]=q[j]+SUB*vp[j];branch.append(regime)
    return qp,vp,branch


def cycle_direct(z,u,model,check=True):
    n=len(model['mass_effective_kg_m2']);p=params(model);out=z.copy()
    if check:domain(out,model)
    old_r=out[-1]
    out[3*n:4*n]+=DT*u[:n]
    out[2*n:3*n]+=DT*out[3*n:4*n]
    out[-2]+=DT*old_r+.5*DT*DT*u[-1];out[-1]+=DT*u[-1]
    branches=[]
    for _ in range(2):
        if check:domain(out,model)
        q,v,branch=scalar_physical(out[:n],out[n:2*n],out[2*n:3*n],p)
        out[:n],out[n:2*n]=q,v;branches.append(branch)
        if check:domain(out,model)
    return out,branches


def cycle_linearization(z,u,model):
    # Independently construct command matrix then exact soft-branch derivatives.
    n=len(model['mass_effective_kg_m2']);nx=4*n+2;nu=n+1
    a=np.eye(nx);b=np.zeros((nx,nu));a[2*n:3*n,3*n:4*n]=DT*np.eye(n)
    b[2*n:3*n,:n]=DT*DT*np.eye(n);b[3*n:4*n,:n]=DT*np.eye(n)
    a[-2,-1]=DT;b[-2,-1]=.5*DT*DT;b[-1,-1]=DT
    current=a@z+b@u;defect=np.zeros(nx)
    mass,bias,kp,damp,eta,imp,decay=params(model)
    for _ in range(2):
        q,v,c=current[:n],current[n:2*n],current[2*n:3*n]
        smooth=kp*(c-q)-damp*v+bias
        drive=imp*(smooth+mass*decay*v)
        interior=(abs(drive)<eta).astype(float)
        gain=SUB/(mass+SUB*damp)
        dvq=-gain*kp*(1-imp*interior)
        dvv=1-gain*((1-imp*interior)*damp+imp*interior*mass*decay)
        p=np.eye(nx)
        p[:n,:n]=np.eye(n)+SUB*np.diag(dvq);p[:n,n:2*n]=SUB*np.diag(dvv);p[:n,2*n:3*n]=-SUB*np.diag(dvq)
        p[n:2*n,:n]=np.diag(dvq);p[n:2*n,n:2*n]=np.diag(dvv);p[n:2*n,2*n:3*n]=-np.diag(dvq)
        nextq,nextv,_=scalar_physical(q,v,c,params(model));nextstate=current.copy();nextstate[:n],nextstate[n:2*n]=nextq,nextv
        f=nextstate-p@current
        a,b,defect=p@a,p@b,p@defect+f
        current=nextstate
    return a,b,defect


def rollout(initial,controls,mesh,model):
    counts=cells(mesh);z=initial.copy();states=[z.copy()];history=[];time=0.
    domain(z,model)
    for k,count in enumerate(counts):
        for _ in range(count):
            z,branches=cycle_direct(z,controls[k],model);time+=DT
            history.append({'cell':k,'time_s':time,'state':z.tolist(),'branches_2ms':branches})
        states.append(z.copy())
    return np.array(states),history


def cell_linearization(z,u,count,model):
    nx=len(z);nu=len(u);a=np.eye(nx);b=np.zeros((nx,nu));d=np.zeros(nx);current=z.copy()
    for _ in range(count):
        p,g,f=cycle_linearization(current,u,model)
        a,b,d=p@a,p@b+g,p@d+f
        current,_=cycle_direct(current,u,model)
    return a,b,d


def synthetic_model():
    return {'mass_effective_kg_m2':[.2],'bias_Nm':[.01],
            'public_parameters':{'kp_Nm_rad':[1000.],'damping_Nm_s_rad':[100.],
            'friction_bound_Nm':[.3],'impedance':[.9],'reference_decay_s_inv':[100.]},
            'local_box':{'q_min':[-.01],'q_max':[.01],'v_abs_max':.05,
                         'target_error_min':[-.001],'target_error_max':[.001]}}


def case(name,model,mesh):
    n=len(model['mass_effective_kg_m2']);nx=4*n+2;nu=n+1;count=len(mesh)
    q=.5*(np.array(model['local_box']['q_min'])+np.array(model['local_box']['q_max']))
    m,g,k,d,eta,imp,decay=params(model)
    initial=np.r_[q,np.array([(-1)**j*2e-5 for j in range(n)]),q-g/k,np.array([(-1)**j*4e-5 for j in range(n)]),.2,.01]
    controls=np.array([[.0006*np.sin(.7*i+.4*j) for j in range(n)]+[.002*np.cos(.4*i)] for i in range(count)])
    states,history=rollout(initial,controls,mesh,model)
    transitions=[cell_linearization(states[i],controls[i],m,model) for i,m in enumerate(cells(mesh))]
    offsets=[initial.copy()];maps=[np.zeros((nx,count*nu))];initial_maps=[np.eye(nx)]
    for i,(a,b,f) in enumerate(transitions):
        offsets.append(a@offsets[-1]+f);current=a@maps[-1];current[:,i*nu:(i+1)*nu]+=b;maps.append(current);initial_maps.append(a@initial_maps[-1])
    offsets=np.array(offsets);maps=np.array(maps);initial_maps=np.array(initial_maps)
    affine_error=float(np.max(abs(states-(offsets+np.einsum('kij,j->ki',maps,controls.ravel())))))
    fd_step=1e-6;control_fd_error=initial_fd_error=0.
    for j in range(count*nu):
        plus,minus=controls.copy(),controls.copy();plus.flat[j]+=fd_step;minus.flat[j]-=fd_step
        zp,hp=rollout(initial,plus,mesh,model);zm,hm=rollout(initial,minus,mesh,model)
        assert [h['branches_2ms'] for h in hp]==[h['branches_2ms'] for h in history]==[h['branches_2ms'] for h in hm]
        control_fd_error=max(control_fd_error,float(np.max(abs((zp-zm)/(2*fd_step)-maps[:,:,j]))))
    for j in range(nx):
        plus,minus=initial.copy(),initial.copy();plus[j]+=fd_step;minus[j]-=fd_step
        zp,hp=rollout(plus,controls,mesh,model);zm,hm=rollout(minus,controls,mesh,model)
        assert [h['branches_2ms'] for h in hp]==[h['branches_2ms'] for h in history]==[h['branches_2ms'] for h in hm]
        initial_fd_error=max(initial_fd_error,float(np.max(abs((zp-zm)/(2*fd_step)-initial_maps[:,:,j]))))
    # Generic lifted state solve, rather than the condensed forward recurrence.
    lifted_n=(count+1)*nx;l=np.eye(lifted_n);rhs=np.zeros((lifted_n,count*nu+1));rhs[:nx,-1]=initial
    for i,(a,b,f) in enumerate(transitions):
        l[(i+1)*nx:(i+2)*nx,i*nx:(i+1)*nx]=-a
        rhs[(i+1)*nx:(i+2)*nx,i*nu:(i+1)*nu]=b;rhs[(i+1)*nx:(i+2)*nx,-1]=f
    eliminated=np.linalg.solve(l,rhs);expected=np.column_stack((maps.reshape(lifted_n,-1),offsets.ravel()))
    elimination_error=float(np.max(abs(eliminated-expected)));lifted_residual=float(np.max(abs(l@states.ravel()-rhs@np.r_[controls.ravel(),1.])))
    # Full state cost plus all controls and exact 4ms command-acceleration jumps.
    weights=np.r_[np.ones(n)*100,np.ones(n)*.5,np.ones(n)*.01,np.ones(n)*.02,.2,.3]
    quadrature=np.r_[mesh,mesh[-1]];w=np.repeat(quadrature,nx)*np.tile(weights,count+1)
    desired=np.tile(initial,count+1);desired[-2::nx]=.8
    s=maps.reshape(lifted_n,-1);offset=offsets.ravel()-desired;ru=np.repeat(mesh,nu)*.01
    slew=np.zeros((count*nu,count*nu));prior=np.linspace(.0001,.0002,nu);slew_offset=np.zeros(count*nu);slew_offset[:nu]=-prior/DT
    for i in range(count):
        slew[i*nu:(i+1)*nu,i*nu:(i+1)*nu]=np.eye(nu)/DT
        if i:slew[i*nu:(i+1)*nu,(i-1)*nu:i*nu]=-np.eye(nu)/DT
    jerk_weight=DT*1e-5
    h=s.T@(w[:,None]*s)+np.diag(ru)+jerk_weight*slew.T@slew
    gradient=s.T@(w*offset)+jerk_weight*slew.T@slew_offset
    constant=.5*np.sum(w*offset**2)+.5*jerk_weight*np.sum(slew_offset**2)
    u=controls.ravel();direct=.5*np.sum(w*(states.ravel()-desired)**2)+.5*np.sum(ru*u*u)+.5*jerk_weight*np.sum((slew@u+slew_offset)**2)
    condensed=.5*u@h@u+gradient@u+constant;cost_error=float(abs(direct-condensed))
    assert affine_error<1e-10 and control_fd_error<1e-6 and initial_fd_error<1e-6 and elimination_error<1e-10 and lifted_residual<1e-10 and cost_error<1e-10
    return {'name':name,'n':n,'mesh_s':mesh,'duration_s':sum(mesh),'initial':initial.tolist(),'controls':controls.tolist(),'model_scope':'Synthetic or frozen mathematical MODEL rollout only, never plant evidence','states':states.tolist(),'history':history,'cell_A':[a.tolist() for a,b,d in transitions],'cell_B':[b.tolist() for a,b,d in transitions],'cell_defect':[d.tolist() for a,b,d in transitions],'condensed_offsets':offsets.tolist(),'control_sensitivities':maps.tolist(),'initial_sensitivities':initial_maps.tolist(),'quadratic_cost':{'H':h.tolist(),'g':gradient.tolist(),'constant':float(constant),'direct':float(direct),'condensed':float(condensed)},'checks':{'nonlinear_nominal_affine':affine_error,'control_fd':control_fd_error,'initial_fd':initial_fd_error,'lifted_elimination':elimination_error,'lifted_dynamics':lifted_residual,'full_quadratic_substitution':cost_error,'all_measurement_and_forecast_domain_checks_pass':True,'finite_difference_branch_sequences_unchanged':True}}


def rejection_and_boundary_tests(model):
    for h in [.041,.0,-.004]:
        try:cells([h]);raise AssertionError('undefined mesh accepted')
        except ValueError:pass
    n=len(model['mass_effective_kg_m2']);box=model['local_box'];q=.5*(np.array(box['q_min'])+np.array(box['q_max']));parameters=params(model);z=np.r_[q,np.zeros(n),q-parameters[1]/parameters[2],np.zeros(n),.2,.01]
    rejected=[]
    for name,index,value in [('q',0,box['q_max'][0]+.001),('v',n,box['v_abs_max']+.001),('target_error',2*n,q[0]+box['target_error_max'][0]+.001),('progress',4*n+1,.3)]:
        bad=z.copy();bad[index]=value
        try:rollout(bad,np.zeros((1,n+1)),[.004],model);raise AssertionError('out-of-domain accepted')
        except ValueError:rejected.append(name)
    future_rejected=[]
    for name,index in [('next_target_error',0),('next_progress_speed',n)]:
        badcontrol=np.zeros((1,n+1));badcontrol[0,index]=1000.
        try:rollout(z,badcontrol,[.004],model);raise AssertionError('forecast outside domain accepted')
        except ValueError:future_rejected.append(name)
    # Exact binary clip threshold with a deliberately separate algebraic fixture.
    threshold=synthetic_model();threshold['mass_effective_kg_m2']=[1.];threshold['bias_Nm']=[0.]
    for key,value in [('kp_Nm_rad',1.),('damping_Nm_s_rad',1.),('friction_bound_Nm',.5),('impedance',.5),('reference_decay_s_inv',1.)]:threshold['public_parameters'][key]=[value]
    p=params(threshold);q=np.zeros(1);v=np.zeros(1);c=np.ones(1);h=1e-6
    base=scalar_physical(q,v,c,p);left=(base[1]-scalar_physical(q,v,c-h,p)[1])/h;right=(scalar_physical(q,v,c+h,p)[1]-base[1])/h
    assert base[2]==[1] and abs(float(left[0]-right[0]))>1e-4
    return {'undefined_mesh_rejections':[.041,.0,-.004],'initial_domain_rejections':rejected,'forecast_domain_rejections':future_rejected,'exact_positive_clip_threshold_branch':base[2],'one_sided_v_derivatives':{'left':float(left[0]),'right':float(right[0])},'derivative_not_unique':True,'branch_convention':'At equality abs(drive)>=eta choose saturated branch derivative; ordinary Jacobian is undefined there.','box_is_not_accuracy_certificate':True}


def cycle_branch_checks(model):
    n=len(model['mass_effective_kg_m2']);box=model['local_box'];q=.5*(np.array(box['q_min'])+np.array(box['q_max']));m,g,k,d,eta,imp,decay=params(model)
    results=[];h=1e-7
    for level in [0.,1.5,-1.5]:
        z=np.r_[q,np.zeros(n),q-g/k+level*eta/(imp*k),np.zeros(n),.2,.01];u=np.zeros(n+1)
        value,branches=cycle_direct(z,u,model);a,b,f=cycle_linearization(z,u,model);combined=np.column_stack((a,b));worst=0.
        for j in range(len(z)+len(u)):
            plus=np.r_[z,u];minus=plus.copy();plus[j]+=h;minus[j]-=h
            zp,bp=cycle_direct(plus[:len(z)],plus[len(z):],model);zm,bm=cycle_direct(minus[:len(z)],minus[len(z):],model)
            assert bp==branches==bm
            worst=max(worst,float(np.max(abs((zp-zm)/(2*h)-combined[:,j]))))
        defect=float(np.max(abs(value-a@z-b@u-f)))
        assert worst<1e-6 and defect<1e-12
        results.append({'drive_relative_to_bound':level,'branches_2ms':branches,'max_full_augmented_state_control_fd_error':worst,'affine_defect_identity_error':defect,'fixture_domain_checks_pass':True})
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--model',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    model_bytes=args.model.read_bytes()
    assert hashlib.sha256(model_bytes).hexdigest()==FROZEN_SHA;model=json.loads(model_bytes)
    meshes=[[.04,.036,.044,.032,.048],[DT*m for m in [8,12,9,11,10,10,8,12,9,11,10,10,8,12,9,11,10,10,8,12]]]
    result={'scope':__doc__,'status':'MODEL_ALGEBRA_ORACLE_PASS_NOT_CTRL001_OR_PHASE5','numpy_version':np.__version__,'frozen_model_path':str(args.model),'frozen_model_sha256':sha(args.model),'source_sha256':SOURCE_SHA_AT_START,'cases':[case('n1_synthetic_nonuniform',synthetic_model(),meshes[0]),case('n7_frozen_soft_v2_nonuniform20',model,meshes[1])],'full_augmented_cycle_branch_checks':{'n1':cycle_branch_checks(synthetic_model()),'n7':cycle_branch_checks(model)},'rejection_and_threshold_checks':rejection_and_boundary_tests(model),'state_order':'physical q/v, accepted c/w, progress s/r','input_order':'command acceleration alpha, progress acceleration b','clock_contract':'At each4ms update w+=Δalpha,c+=Δw_next; holdc across two2msphysicalsoftsteps; progress s+=Δr+.5Δ²b,r+=Δb. Fortyms=tenreal4msupdates; onlypositiveinteger4msmesh supported.'}
    assert sha(args.model)==FROZEN_SHA
    assert sha(Path(__file__))==SOURCE_SHA_AT_START,'Oracle source changed during execution; refuse output'
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'SOURCE_SNAPSHOT.py').write_bytes(SOURCE_BYTES_AT_START)
    (args.output/'MODEL_SNAPSHOT.json').write_bytes(model_bytes)
    (args.output/'oracle.json').write_text(json.dumps(result,indent=2)+'\n')
    summary={k:v for k,v in result.items() if k!='cases'};summary['cases']=[{k:c[k] for k in ['name','n','mesh_s','duration_s','checks']} for c in result['cases']]
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    note=f'''# Independent augmented soft-servo oracle

Status: MODEL_ALGEBRA_ORACLE_PASS_NOT_CTRL001_OR_PHASE5. No fit, physical plant, authoritative Dell edits, external-chat messages or Git operations. All trajectories here are pure model algebra, even when their parameters come from the frozen soft-v2 model. This oracle can check a local C++ transition module; it cannot close CTRL-001 or Phase5.

Frozen model SHA: {FROZEN_SHA}. Startup source SHA: {SOURCE_SHA_AT_START}. SOURCE_SNAPSHOT.py and MODEL_SNAPSHOT.json preserve the exact bytes used. Source and model are checked unchanged before any output is published; READY uses the same startup source identity. NumPy {np.__version__} was used locally.

State z=(physical q,v, accepted command c,w, progress s,r); u=(command alpha, progress b). Each actual4ms cycle first performs w+=Delta*alpha, c+=Delta*w_next, then holds c for two2ms soft-friction physical steps. Progress advances s+=Delta*r+0.5*Delta^2*b and r+=Delta*b. A40ms cell composes ten such4ms cycles. Nonuniform cells must be positive integer4ms multiples; undefined remainder policies are rejected. Intermediate2ms task references, if added by C++, must evaluate s(t)=s0+t*r0+0.5*t^2*b; the oracle exports full-cycle states.

The scalar direct reference evaluates soft force s=k(c-q)-D*v+g, f=-clip(I*(s+m*B*v),-eta,eta), v_next=v+delta*(s+f)/(m+delta*D), q_next=q+delta*v_next. Independently assembled branch derivatives use gain=delta/(m+delta*D): interior dv/dq=-gain*(1-I)*k, dv/dv=1-gain*((1-I)*D+I*m*B), dv/dc=-dv/dq. Saturated branches replace(1-I) by1 and omit I*m*B. At exact clipping equality the saturated derivative is only a declared one-sided branch convention; ordinary derivatives are nonunique.

The command/progress Jacobian is composed with the two physical Jacobians. Cell A/B/defect are composed over all actual cycles at held alpha/b; defect is the nominal forward state minus A*initial-B*control. Full-horizon state and control sensitivities follow the chain rule. Generic lifted-state elimination is independently solved and compared with these condensed maps. The synthetic full quadratic objective includes all physical/command/progress state components, all controls, nonzero target/initial offsets and actual4ms control-jump history. The cost is an algebraic test, not a tuned research objective.

Executed cases: n=1 synthetic nonuniform5cells/.2s, and n=7 frozen parameters nonuniform20cells/.8s. The latter has30state components,160control components and630lifted state entries. All160control and30initial-state finite differences check the direct nonlinear rollout without resetting physical states. Selected interior and both saturated4ms cycle fixtures also check full augmented state/control Jacobians. Exact threshold one-sided derivatives differ; undefined meshes and initial/forecast domain violations are rejected.

N7 maxima: nominal affine consistency {result['cases'][1]['checks']['nonlinear_nominal_affine']:.4e}; control FD {result['cases'][1]['checks']['control_fd']:.4e}; initial FD {result['cases'][1]['checks']['initial_fd']:.4e}; lifted elimination {result['cases'][1]['checks']['lifted_elimination']:.4e}; lifted dynamics {result['cases'][1]['checks']['lifted_dynamics']:.4e}; full cost substitution {result['cases'][1]['checks']['full_quadratic_substitution']:.4e}. Detailed n1/n7 branch and rejection records are in summary.json; full numerical A/B/defects, sensitivities, model histories and cost H/g/constant are in oracle.json.

Initial physical state and accepted command history remain distinct. Domain checks apply to initial physical q/v/target-minus-q, every pre/post physical substep after a command update, and progress s/r. Passing a declared box is not an accuracy guarantee. No claim is made about arbitrary commands, fitted parameter physical identity, robot stopping, full nonlinear safety, real-time solver behavior or actual task progress.

Earlier v1 numerical output is retained unchanged. Its exact252c3d source was recovered into a separate retention directory. The root-rerun's mixed READY/source identity remains a recorded race: its oracle/summary numerical bytes matched v1, but an in-flight source edit caused READY to read a different source hash. This final publication uses a startup snapshot and an unchanged-source assertion to avoid mixing identities. Parent owns backing up this fixed source and immutable output.
'''
    (args.output/'REFERENCE.md').write_text(note)
    manifest={'scope':__doc__,'files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in args.output.iterdir()},'frozen_model_sha256':FROZEN_SHA,'source_sha256':SOURCE_SHA_AT_START};(args.output/'READY.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
