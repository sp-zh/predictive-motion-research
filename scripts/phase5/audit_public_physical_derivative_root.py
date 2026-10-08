#!/usr/bin/env python3
"""Independent selected physical-step derivative audit against frozen base FD.

Preset mathematical forces and current-state diagnostics only. No fitting,
plant, augmented-controller, timing or uniform-domain claim.
"""
import argparse,copy,csv,hashlib,json,math,subprocess,sys
from pathlib import Path
import numpy as np
BASE_SHA='fa1a00344e73d8fe2266541ba4e2b34c362351b30a4f21dfa34c04867f585a04'
EPS=(1e-6,3e-7);ABS=5e-7;REL=5e-6
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def need(b,s):
    if not b:raise AssertionError(s)
def numbers(a):
    if type(a) in (int,float):need(math.isfinite(a),'finite output')
    elif type(a) is dict:
        for x in a.values():numbers(x)
    elif type(a) is list:
        for x in a:numbers(x)
def matrix(a,m,n):
    need(type(a) is list and len(a)==m and all(type(x) is list and len(x)==n and all(type(v) in (int,float) and math.isfinite(v) for v in x) for x in a),'finite typed matrix')
def compare(analytic,fd):
    a,b=np.asarray(analytic,float),np.asarray(fd,float);need(a.shape==b.shape,'comparison shape');error=abs(a-b);ratio=error/(ABS+REL*abs(a));need(np.isfinite(error).all() and np.isfinite(ratio).all() and (ratio<=1).all(),'both declared FD entry gates')
    return {'max_absolute':float(error.max()),'max_gate_ratio':float(ratio.max())}
def signature(inp,val,c):
    q,v,C=[np.asarray(inp[k],float) for k in ('q','v','C')];gain=np.asarray(c['gainprm']).reshape(7,10);bias=np.asarray(c['biasprm']).reshape(7,10);sides=[]
    def stage(x,key,flags,margin):
        result=[];side=[]
        for j in range(7):
            lo,hi=c[key][2*j:2*j+2]
            if not c[flags][j]:result.append(x[j]);side.append(0);continue
            which=-1 if x[j]<lo else 1 if x[j]>hi else 0;distance=lo-x[j] if which==-1 else x[j]-hi if which==1 else min(x[j]-lo,hi-x[j]);need(distance>margin,'strict clip support at every perturbation');result.append(min(max(x[j],lo),hi));side.append(which)
        sides.append(side);return np.asarray(result)
    u=stage(C,'control_range','control_limited',1e-8);raw=gain[:,0]*u+bias[:,0]+bias[:,1]*q+bias[:,2]*v;act=stage(raw,'actuator_force_range','actuator_force_limited',1e-7);stage(act,'joint_actuator_force_range','joint_actuator_force_limited',1e-7)
    f=np.asarray(val['friction']['force']);eta=np.asarray(c['friction_bounds']);H=np.asarray(val['H']);ell=np.asarray(val['ell']);g=np.asarray([math.fsum(float(H[j,k])*float(f[k]) for k in range(7))+float(ell[j]) for j in range(7)]);labels=[]
    for j in range(7):
        label=2 if eta[j]==0 else -1 if f[j]<=-eta[j] else 1 if f[j]>=eta[j] else 0;labels.append(label)
        if label==0:need(eta[j]-abs(f[j])>1e-7 and abs(g[j])<=1e-10,'strict free support')
        elif label!=2:need((g[j] if label==-1 else -g[j])>1e-7,'strict active support')
    need(labels==val['friction']['branches'],'exact friction labels');return sides+[labels]
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ('output','binary','freeze'):ap.add_argument('--'+key,type=Path,required=True)
    for key in ('binary-sha','freeze-sha'):ap.add_argument('--'+key,required=True)
    args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False);source=Path(__file__);source_bytes=source.read_bytes();(out/'SOURCE_SNAPSHOT.py').write_bytes(source_bytes)
    root=Path('/home/codextransfer/predictive_motion');base=root/'build-public-coupled-cpp-v2/public_coupled_probe_v2';xml=root/'experiments/generated/inspection/inspection_fr3.xml';const=root/'results/phase5/development/public-coupled-servo-v1-training/public_constants.json';raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013/raw.csv');old=root/'results/phase5/development/public-coupled-cpp-v2/inputs/cases.json'
    need(sha(base)==BASE_SHA and sha(args.binary)==args.binary_sha and sha(args.freeze)==args.freeze_sha,'pinned native identities');need(sha(raw)=='ea70d9e8b01bc6e44387e2f4701779243bb1b202020a61aef18312fac1c054e8','raw identity')
    entries={x['path']:x for x in json.loads(args.freeze.read_text())['files']};owned=[base,args.binary,xml,const,raw,old]+list((root/'tools/phase5_public_coupled_cpp_v2').glob('*'))+list((root/'tools/phase5_public_coupled_derivative_cpp').glob('*'))
    for p in owned:need(sha(p)==entries[str(p)]['sha256'],'owned source frozen '+str(p))
    sys.path.insert(0,str(root/'scripts/phase5'));from validate_public_coupled_native_output_v2 import validate_output
    c=json.loads(const.read_text());oldcases=json.loads(old.read_text());q=next(x['q'] for x in oldcases['cases'] if x['name']=='nominal_zero')
    with raw.open() as f:rows=list(csv.DictReader(f))
    moving=[float(rows[1380]['v_before_'+str(j)]) for j in range(7)];need(int(rows[1380]['tick'])==690,'predeclared moving velocity')
    # These first calls obtain current M/n only. Their predicted q/v are ignored.
    seed=[{'name':'root_current_stationary','q':q,'v':[0.]*7,'targets':[q],'expect_success':True},{'name':'root_current_moving','q':q,'v':moving,'targets':[q],'expect_success':True}]
    seedinp={'cases':seed,'box_cases':[]};dump(out/'current_diagnostic_inputs.json',seedinp)
    declaration={'epsilons':EPS,'absolute_per_entry':ABS,'relative_per_entry':REL,'preset_mixed_force':['-eta0','+eta1','.2eta2',0,0,0,0],'preset_gradient':[.1,-.1,0,0,0,0,0],'preset_all_bound_gradient_magnitude':.25,'force_saturation_target_offset_rad':.07,'control_saturation_below_lower_rad':.15,'scope':__doc__,'current_diagnostic_semantics':'Frozen original base probe current M/bias only; returned next states ignored in fixture construction. No derivative call or parameter selection from errors.'};dump(out/'PRE_FORECAST_DECLARATION.json',declaration)
    def invoke(binary,inp,dest):
        run=subprocess.run([str(binary),str(xml),str(const),str(inp),str(dest)],capture_output=True,text=True);dest.with_suffix('.stdout').write_text(run.stdout);dest.with_suffix('.stderr').write_text(run.stderr);dest.with_suffix('.exit').write_text(str(run.returncode)+'\n');need(run.returncode==0,'native returncode');r=json.loads(dest.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)));numbers(r);return r
    current=invoke(base,out/'current_diagnostic_inputs.json',out/'current_diagnostics.json');validate_output(current,seedinp);values=[x['last'] for x in current['cases']];M=np.asarray(values[0]['M']);W=np.asarray(values[0]['W']);H=(W+W.T)/2+np.diag(current['metadata']['R']);eta=np.asarray(c['friction_bounds']);B=np.asarray(current['metadata']['B']);kp=np.asarray(c['gainprm']).reshape(7,10)[:,0];bias=np.asarray(c['biasprm']).reshape(7,10);passive=np.asarray(c['passive_damping']);q=np.asarray(q)
    def Cfrom(act,v):return ((np.asarray(act)-bias[:,0]-bias[:,1]*q-bias[:,2]*np.asarray(v))/kp).tolist()
    cases=[]
    def preset(name,f,g,motion=False,supported=True):
        index=1 if motion else 0;v=seed[index]['v'];n=np.asarray(values[index]['bias']);tau=M@(-H@np.asarray(f)+np.asarray(g)-B*np.asarray(v));act=tau+n+passive*np.asarray(v);C=Cfrom(act,v)
        ranges=np.asarray(c['joint_actuator_force_range']).reshape(7,2);controls=np.asarray(c['control_range']).reshape(7,2)
        need((act>ranges[:,0]).all() and (act<ranges[:,1]).all() and (np.asarray(C)>controls[:,0]).all() and (np.asarray(C)<controls[:,1]).all(),'preset mathematical fixture supported before FD')
        cases.append({'name':name,'q':q.tolist(),'v':v,'C':C,'expect_value':True,'expect_J':supported,'preset_force':list(map(float,f)),'preset_gradient':list(map(float,g))})
    z=np.zeros(7);preset('root_all_free_stationary',z,z)
    f=z.copy();f[0]=-eta[0];f[1]=eta[1];f[2]=.2*eta[2];g=z.copy();g[0]=.1;g[1]=-.1;preset('root_mixed_stationary',f,g);preset('root_mixed_nonzero_motion',f,g,True)
    f=np.asarray([(-1 if j%2==0 else 1)*eta[j] for j in range(7)]);g=np.asarray([(.25 if j%2==0 else -.25) for j in range(7)]);preset('root_all_strict_bounds',f,g)
    eq=Cfrom(values[0]['bias'],[0.]*7)
    cases.append({'name':'root_strong_joint_force','q':q.tolist(),'v':[0.]*7,'C':(q+np.asarray([.07*(-1 if j%2 else 1) for j in range(7)])).tolist(),'expect_value':True,'expect_J':True})
    C=eq.copy();C[0]=c['control_range'][0]-.15;cases.append({'name':'root_strong_control','q':q.tolist(),'v':[0.]*7,'C':C,'expect_value':True,'expect_J':True})
    f=z.copy();f[0]=-eta[0];preset('root_weak_lower',f,z,supported=False)
    act=np.asarray(values[0]['bias']).copy();act[0]=c['joint_actuator_force_range'][1];cases.append({'name':'root_joint_force_threshold','q':q.tolist(),'v':[0.]*7,'C':Cfrom(act,[0.]*7),'expect_value':True,'expect_J':False})
    C=eq.copy();C[0]=c['control_range'][0];cases.append({'name':'root_control_threshold_conservative','q':q.tolist(),'v':[0.]*7,'C':C,'expect_value':True,'expect_J':False})
    bad=copy.deepcopy(cases[0]);bad.update(name='root_q_dimension6',q=q.tolist()[:6],expect_value=False,expect_J=False);cases.append(bad)
    bad=copy.deepcopy(cases[0]);bad.update(name='root_v_nonfinite',v=['.inf']*7,expect_value=False,expect_J=False);cases.append(bad)
    dump(out/'cases.json',{'cases':cases});positives=[x for x in cases if x['expect_J']];fd_cases=[]
    for case in positives:
        fd_cases.append({'name':case['name']+'_nominal','q':case['q'],'v':case['v'],'targets':[case['C']],'expect_success':True})
        for ei,e in enumerate(EPS):
            for j in range(21):
                for sign in (-1,1):
                    inp=copy.deepcopy(case);key=('q','v','C')[j//7];inp[key][j%7]+=sign*e;fd_cases.append({'name':f'{case["name"]}_{ei}_{j}_{sign}','q':inp['q'],'v':inp['v'],'targets':[inp['C']],'expect_success':True})
    fdinp={'cases':fd_cases,'box_cases':[]};dump(out/'fd_inputs.json',fdinp)
    analytic=invoke(args.binary,out/'cases.json',out/'analytic.json');finite=invoke(base,out/'fd_inputs.json',out/'finite_differences.json');validate_output(finite,fdinp)
    need(analytic['model_success'] is True and len(analytic['cases'])==len(cases) and [x['name'] for x in analytic['cases']]==[x['name'] for x in cases],'complete ordered analytic roster')
    lookup={x['name']:x['last'] for x in finite['cases']};fdlookup={x['name']:x for x in fd_cases};reports=[]
    for case,answer in zip(cases,analytic['cases']):
        need(type(answer['value_success']) is bool and answer['value_success']==case['expect_value'] and type(answer['jacobian_success']) is bool and answer['jacobian_success']==case['expect_J'],'expected typed value/J outcomes')
        if not case['expect_J']:
            need('jacobian' not in answer and type(answer.get('error')) is str and bool(answer['error']),'explicit unsupported without fabricated Jacobian');reports.append({'name':case['name'],'value_success':answer['value_success'],'jacobian_success':False,'error':answer['error']});continue
        matrix(answer['jacobian'],14,21);d=answer['diagnostics'];matrix(d['nq'],7,7);matrix(d['nv'],7,7);need(len(d['mass_q'])==7,'full mass tensor');[matrix(a,7,7) for a in d['mass_q']];need(all(1<=x<=1e12 for x in d['solve_conditions']) and all(0<=x<=1e-10 for x in d['solve_residuals']),'condition/residual guards')
        value=answer['value'];need(value==lookup[case['name']+'_nominal'],'unchanged base values');sig=signature(case,value,c);epsreports=[]
        if 'preset_force' in case:need(max(abs(np.asarray(value['friction']['force'])-case['preset_force']))<=1e-10 and max(abs(np.asarray(d['friction_gradient'])-case['preset_gradient']))<=1e-10,'preset force/gradient construction')
        for ei,e in enumerate(EPS):
            J=np.zeros((14,21));Nq=np.zeros((7,7));Nv=np.zeros((7,7));mass=[np.zeros((7,7)) for _ in range(7)]
            for j in range(21):
                names=[f'{case["name"]}_{ei}_{j}_{s}' for s in (-1,1)];minus,plus=[lookup[x] for x in names]
                for name,point in zip(names,(minus,plus)):
                    x=fdlookup[name];need(signature({'q':x['q'],'v':x['v'],'C':x['targets'][0]},point,c)==sig,'each perturbation same strict branch')
                J[:,j]=(np.r_[plus['q'],plus['v']]-np.r_[minus['q'],minus['v']])/(2*e)
                if j<7:Nq[:,j]=(np.asarray(plus['bias'])-minus['bias'])/(2*e);mass[j]=(np.asarray(plus['M'])-minus['M'])/(2*e)
                elif j<14:Nv[:,j-7]=(np.asarray(plus['bias'])-minus['bias'])/(2*e)
            epsreports.append({'epsilon':e,'transition':compare(answer['jacobian'],J),'nq':compare(d['nq'],Nq),'nv':compare(d['nv'],Nv),'mass_q':[compare(d['mass_q'][j],mass[j]) for j in range(7)]})
        reports.append({'name':case['name'],'epsilons':epsreports,'branch_signature':sig,'nv_max_abs':float(abs(np.asarray(d['nv'])).max()),'pass':True})
    for p in owned:need(sha(p)==entries[str(p)]['sha256'],'owned identities unchanged')
    need(source.read_bytes()==source_bytes and sha(args.freeze)==args.freeze_sha,'root source/freeze unchanged')
    report={'decision':'PASS_SELECTED_PHYSICAL_DERIVATIVE_REFERENCE','scope':__doc__,'source_sha256':hashlib.sha256(source_bytes).hexdigest(),'binary_sha256':args.binary_sha,'freeze_sha256':args.freeze_sha,'base_sha256':BASE_SHA,'epsilons':EPS,'absolute_per_entry':ABS,'relative_per_entry':REL,'supported_cases':6,'unsupported_threshold_cases':3,'invalid_cases':2,'independent_FD_base_calls':len(fd_cases),'current_diagnostic_base_calls':2,'cases':reports,'phase5':'NOT_ACCEPTED','new_plant':False};dump(out/'audit.json',report);files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in out.iterdir() if p.is_file()};dump(out/'READY.json',{'files':files,'scope':__doc__});print(json.dumps({'supported':6,'unsupported':3,'invalid':2,'base_FD_calls':len(fd_cases),'all_two_epsilon_gates':True}))
if __name__=='__main__':main()
