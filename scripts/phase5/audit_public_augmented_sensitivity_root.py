#!/usr/bin/env python3
"""Independent augmented cycle/cell sensitivity audit; no plant or main controller.

Old frozen value FD, every perturbed physical substep's original diagnostics,
closed-form command/progress coefficients and exact semiimplicit identities.
"""
import argparse,copy,hashlib,json,math,subprocess,sys
from pathlib import Path
import numpy as np
from audit_public_physical_derivative_root import signature,compare,numbers,matrix,need
from public_coupled_augmented_root_reference import exact_command_progress
BASE_SHA='fa1a00344e73d8fe2266541ba4e2b34c362351b30a4f21dfa34c04867f585a04'
VALUE_SHA='2fa952127cdd37ceb56396231e2972d50d36c94e9a19c341c9c17169442acf57'
EPS=(1e-6,3e-7);H=.004;DT=.002;BATCH=96
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def pack(z):return np.r_[z['q'],z['v'],z['C'],z['w'],z['s'],z['r']]
def point(p):return dict(q=p['q'],v=p['v'],C=p['C'],w=p['w'],s=p['s_reference'],r=p['r_reference'])
def close(a,b,tol,label):
    a,b=np.asarray(a),np.asarray(b);need(a.shape==b.shape and np.isfinite(a).all() and np.max(abs(a-b))<=tol,label)
def blocks(k,half):
    # command already latched for full kth cycle; progress at true half time.
    command=k*H;t=(k-1)*H+half*DT
    A=np.zeros((16,30));B=np.zeros((16,8));I=np.eye(7)
    A[:7,14:21]=I;A[:7,21:28]=command*I;B[:7,:7]=H*H*k*(k+1)/2*I
    A[7:14,21:28]=I;B[7:14,:7]=command*I
    A[14,28]=1;A[14,29]=t;A[15,29]=1;B[14,7]=.5*t*t;B[15,7]=t
    return A,B

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('output','binary','freeze','predeclared'):p.add_argument('--'+k,type=Path,required=True)
    for k in ('binary-sha','freeze-sha'):p.add_argument('--'+k,required=True)
    args=p.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
    root=Path('/home/codextransfer/predictive_motion');base=root/'build-public-coupled-cpp-v2/public_coupled_probe_v2';value=root/'build-public-coupled-augmented-cpp-v1/public_coupled_augmented_probe';xml=root/'experiments/generated/inspection/inspection_fr3.xml';const=root/'results/phase5/development/public-coupled-servo-v1-training/public_constants.json'
    need(sha(base)==BASE_SHA and sha(value)==VALUE_SHA and sha(args.binary)==args.binary_sha and sha(args.freeze)==args.freeze_sha,'pinned native identities')
    frozen={x['path']:x for x in json.loads(args.freeze.read_text())['files']};owned=[base,value,args.binary,xml,const]
    for directory in ('phase5_public_coupled_cpp_v2','phase5_public_coupled_augmented_cpp','phase5_public_coupled_derivative_cpp','phase5_public_coupled_augmented_sensitivity_cpp'):owned+=list((root/'tools'/directory).glob('*'))
    for q in owned:need(str(q) in frozen and sha(q)==frozen[str(q)]['sha256'],'owned source frozen '+str(q))
    sources=[Path(__file__),Path(__file__).with_name('audit_public_physical_derivative_root.py'),Path(__file__).with_name('public_coupled_augmented_root_reference.py')];snapshots={str(q):q.read_bytes() for q in sources}
    for q in sources:(out/('SOURCE_'+q.name)).write_bytes(snapshots[str(q)])
    fixture=json.loads(args.predeclared.read_text());(out/'PREDECLARED.json').write_bytes(args.predeclared.read_bytes());st=fixture['state'];held=fixture['cells'][0]
    positives=[dict(name='root_single_cycle',state=st,cells=[held]),dict(name='root_held10',state=st,cells=[dict(held,cycles=10)]),dict(name='root_held_split',state=st,cells=[dict(held,cycles=n) for n in (1,3,2,4)]),dict(name=fixture['name'],state=st,cells=fixture['cells'])]
    negatives=[]
    for name,key,val in [('root_initial_s_boundary','s',0.),('root_initial_r_boundary','r',0.)]:
        x=copy.deepcopy(positives[0]);x['name']=name;x['state'][key]=val;negatives.append(x)
    x=copy.deepcopy(positives[0]);x['name']='root_initial_alpha_boundary';x['cells'][0]['alpha'][0]=1.;negatives.append(x)
    x=copy.deepcopy(positives[0]);x['name']='root_future_progress_failure';x['state']['r']=.199;x['cells']=[dict(cycles=4,alpha=[0.]*7,b=.1)];negatives.append(x)
    x=copy.deepcopy(positives[0]);x['name']='root_invalid_q_dimension';x['state']['q'].pop();negatives.append(x)
    cases=positives+negatives;dump(out/'cases.json',{'cases':cases})
    dump(out/'PRE_FORECAST_DECLARATION.json',{'epsilons':EPS,'batch_cap':BATCH,'FD_absolute_per_entry':5e-7,'FD_relative_per_entry':5e-6,'exact_identity_tolerance':1e-12,'cases':cases,'distinct_cell_control_columns':True,'scope':__doc__})
    def invoke(binary,inp,dest):
        r=subprocess.run([str(binary),str(xml),str(const),str(inp),str(dest)],capture_output=True,text=True)
        dest.with_suffix('.stdout').write_text(r.stdout);dest.with_suffix('.stderr').write_text(r.stderr);dest.with_suffix('.exit').write_text(str(r.returncode)+'\n');need(r.returncode==0,'native process return')
        data=json.loads(dest.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)));numbers(data);need(data['model_success'] is True,'model initialized');return data
    def batches(binary,roster,prefix,physical=False):
        answers=[]
        for k in range(0,len(roster),BATCH):
            inp={'cases':roster[k:k+BATCH]}
            if physical:inp['box_cases']=[]
            src=out/f'{prefix}_{k//BATCH:03d}_inputs.json';dest=out/f'{prefix}_{k//BATCH:03d}.json';dump(src,inp);r=invoke(binary,src,dest)
            need(len(r['cases'])==len(inp['cases']) and [x['name'] for x in r['cases']]==[x['name'] for x in inp['cases']],'exact ordered batch roster');answers+=r['cases']
        need(len({x['name'] for x in answers})==len(answers),'unique names');return answers
    analytic=invoke(args.binary,out/'cases.json',out/'analytic.json')['cases'];need([x['name'] for x in analytic]==[x['name'] for x in cases],'exact analytic roster')
    fd=[];directions={}
    for case in (positives[0],positives[1],positives[3]):
        dirs=[('state',j) for j in range(30)]+[(i,j) for i in range(len(case['cells'])) for j in range(8)];directions[case['name']]=dirs
        nominal=copy.deepcopy(case);nominal['name']=case['name']+'_nominal';fd.append(nominal)
        for ei,e in enumerate(EPS):
            for di,(cell,j) in enumerate(dirs):
                for sign in (-1,1):
                    x=copy.deepcopy(case);x['name']=f'{case["name"]}_{ei}_{di}_{sign}'
                    if cell=='state':
                        if j<28:key=('q','v','C','w')[j//7];x['state'][key][j%7]+=sign*e
                        else:key=('s','r')[j-28];x['state'][key]+=sign*e
                    elif j<7:x['cells'][cell]['alpha'][j]+=sign*e
                    else:x['cells'][cell]['b']+=sign*e
                    fd.append(x)
    values=batches(value,fd,'value_fd');lookup={x['name']:x for x in values};inputs={x['name']:x for x in fd};c=json.loads(const.read_text())
    # Original fa1 one-step diagnostics at every FD substep, using its actual
    # previous q/v and already-latched C. These are never fitted or simulated.
    physical=[]
    def domain(z):
        need(min(z['s'],1-z['s'],z['r'],.2-z['r'])>1e-8 and max(abs(a) for a in z['w'])<.0625-1e-8,'strict augmented perturbation domain')
        limits=np.asarray(c['control_range']).reshape(7,2);C=np.asarray(z['C']);need(((C-limits[:,0])>1e-8).all() and ((limits[:,1]-C)>1e-8).all(),'strict augmented C neighborhood')
    for x,v in zip(fd,values):
        need(v['success'] is True and v['has_final_state'] is True and len(v['substeps'])==2*sum(y['cycles'] for y in x['cells']),'complete supported value')
        previous=x['state'];domain(previous)
        for cell in x['cells']:need(max(abs(a) for a in cell['alpha'])<1-1e-8 and math.isfinite(cell['b']),'strict held input neighborhood')
        ref=exact_command_progress(previous['C'],previous['w'],previous['s'],previous['r'],[(y['cycles'],y['alpha'],y['b']) for y in x['cells']])
        for i,(q,oracle) in enumerate(zip(v['substeps'],ref)):
            z=point(q);domain(z)
            close(z['C'],oracle['C'],2e-13,'exact held commands');close(z['w'],oracle['w'],2e-13,'exact accepted velocity');close([z['s'],z['r']],[oracle['s'],oracle['r']],2e-13,'exact progress')
            physical.append(dict(name=f'{x["name"]}_p{i}',q=previous['q'],v=previous['v'],targets=[q['C']]))
            previous=z
    diagnostics=batches(base,physical,'physical_diagnostic',True);dlookup={x['name']:x for x in diagnostics};plookup={x['name']:x for x in physical};sigs={}
    for x,v in zip(fd,values):
        ss=[]
        for i,q in enumerate(v['substeps']):
            name=f'{x["name"]}_p{i}';a=dlookup[name];need(a['success'] is True and len(a['trace'])==1,'physical diagnostic success');a=a['last'];close(a['q'],q['q'],0.,'exact original step q');close(a['v'],q['v'],0.,'exact original step v')
            ss.append(signature(dict(q=plookup[name]['q'],v=plookup[name]['v'],C=q['C']),a,c))
            M=np.asarray(a['M']);K=M+DT*np.diag(np.asarray(c['passive_damping'])-np.asarray(c['biasprm']).reshape(7,10)[:,2]);S=(np.asarray(a['H'])+np.asarray(a['H']).T)/2
            for mat in (M,K,S):ev=np.linalg.eigvalsh(mat);need(ev[0]>0 and ev[-1]/ev[0]<=1e12,'perturbed SPD condition support')
        sigs[x['name']]=ss
    reports=[]
    for case,a in zip(positives,analytic[:4]):
        need(a['sensitivity_success'] is True and a['value']['success'] is True and a['first_uncertified_substep']==-1,'complete sensitivity')
        total=sum(x['cycles'] for x in case['cells']);need(len(a['substep_maps'])==2*total and len(a['cycle_maps'])==total and len(a['cell_maps'])==len(case['cells']),'complete maps')
        globalA=np.eye(30);globalB=np.zeros((30,8*len(case['cells'])));cycle_index=0;cell_initial=case['state'];orig=case['state'];globalmaps=[]
        for ci,cell in enumerate(case['cells']):
            priorA=np.eye(30);priorB=np.zeros((30,8));u=np.r_[cell['alpha'],cell['b']]
            for k in range(1,cell['cycles']+1):
                previousQA=priorA[:7].copy();previousQB=priorB[:7].copy()
                for half in (1,2):
                    si=2*cycle_index+half-1;m=a['substep_maps'][si];need((m['cell'],m['cycle'],m['half'])==(ci,k,half),'map timing/order');matrix(m['A'],30,30);matrix(m['B'],30,8);matrix(m['cell_A'],30,30);matrix(m['cell_B'],30,8)
                    A=np.asarray(m['A']);B=np.asarray(m['B']);CA=A@priorA;CB=A@priorB+B
                    close(CA,m['cell_A'],1e-12,'independent cell A product');close(CB,m['cell_B'],1e-12,'independent cell B sum');close(pack(m['origin']),pack(orig),0.,'cycle-local origin');close(pack(m['cell_origin']),pack(cell_initial),0.,'cell origin');close(m['input'],u,0.,'held input');close(pack(m['state']),pack(point(a['value']['substeps'][si])),0.,'map/value endpoint')
                    close(m['defect'],pack(m['state'])-A@pack(orig)-B@u,1e-12,'local matched defect');close(m['cell_defect'],pack(m['state'])-CA@pack(cell_initial)-CB@u,1e-12,'cell matched defect')
                    LA,LB=blocks(1,half);EA,EB=blocks(k,half);close(A[14:],LA,1e-12,'local command/progress A');close(B[14:],LB,1e-12,'local command/progress B');close(CA[14:],EA,1e-12,'closed-form cell A');close(CB[14:],EB,1e-12,'closed-form cell B')
                    close(A[:14,21:28],H*A[:14,14:21],1e-12,'physical accepted-w chain coefficient');close(B[:14,:7],H*H*A[:14,14:21],1e-12,'tiny alpha h-squared chain coefficient');close(CA[:14,28:],np.zeros((14,2)),0.,'physical/progress separation');close(CB[:14,7],np.zeros(14),0.,'physical b separation')
                    close(CA[:7],previousQA+DT*CA[7:14],1e-12,'semiimplicit cell q A');close(CB[:7],previousQB+DT*CB[7:14],1e-12,'semiimplicit cell q B');previousQA=CA[:7].copy();previousQB=CB[:7].copy()
                    GA=CA@globalA;GB=CA@globalB;GB[:,8*ci:8*ci+8]+=CB;globalmaps.append((GA,GB))
                cm=a['cycle_maps'][cycle_index];
                for key in ('A','B','cell_A','cell_B','defect','cell_defect','input'):close(cm[key],m[key],1e-12,'cycle/half2 '+key)
                for key in ('origin','cell_origin'):close(pack(cm[key]),pack(m[key]),0.,'cycle/half2 '+key)
                close(cm['cell_A'],CA,1e-12,'cycle endpoint cell A');close(cm['cell_B'],CB,1e-12,'cycle endpoint cell B');close(pack(cm['state']),pack(a['value']['cycle_end_states'][cycle_index]),0.,'cycle nominal state');priorA=CA;priorB=CB;orig=cm['state'];cycle_index+=1
            m=a['cell_maps'][ci];close(pack(m['state']),pack(orig),0.,'cell-map endpoint');close(m['input'],u,0.,'cell-map held input');close(m['A'],CA,1e-12,'cell cumulative map A');close(m['B'],CB,1e-12,'cell cumulative map B');close(pack(m['origin']),pack(cell_initial),0.,'cell-map origin');close(m['defect'],pack(m['state'])-CA@pack(cell_initial)-CB@u,1e-12,'cell-map matched defect');globalA=CA@globalA;globalB=CA@globalB;globalB[:,8*ci:8*ci+8]+=CB;cell_initial=orig
        if case['name'] in directions:
            nominal=lookup[case['name']+'_nominal'];need(a['value']=={key:val for key,val in nominal.items() if key!='name'},'frozen augmented value unchanged');epsreports=[]
            for ei,e in enumerate(EPS):
                errors=[]
                for di,(ci,j) in enumerate(directions[case['name']]):
                    names=[f'{case["name"]}_{ei}_{di}_{sign}' for sign in (-1,1)];minus,plus=[lookup[n] for n in names]
                    for n in names:need(sigs[n]==sigs[case['name']+'_nominal'],'all perturbed strict branches equal nominal')
                    for i,(GA,GB) in enumerate(globalmaps):
                        fdcol=(pack(point(plus['substeps'][i]))-pack(point(minus['substeps'][i])))/(2*e);col=GA[:,j] if ci=='state' else GB[:,8*ci+j];errors.append(compare(col,fdcol))
                epsreports.append(dict(epsilon=e,max_absolute=max(x['max_absolute'] for x in errors),max_gate_ratio=max(x['max_gate_ratio'] for x in errors)))
            reports.append(dict(name=case['name'],columns=len(directions[case['name']]),epsilons=epsreports))
    heldA=np.asarray(analytic[1]['cell_maps'][0]['A']);heldB=np.asarray(analytic[1]['cell_maps'][0]['B']);A=np.eye(30);B=np.zeros((30,8))
    for m in analytic[2]['cell_maps']:M=np.asarray(m['A']);A=M@A;B=M@B+np.asarray(m['B'])
    close(A,heldA,1e-12,'held split A equality');close(B,heldB,1e-12,'held split B equality');need(analytic[1]['value']['final_state']==analytic[2]['value']['final_state'],'held split value equality')
    for case,a in zip(negatives,analytic[4:]):
        need(a['sensitivity_success'] is False and bool(a['error']),'explicit uncertified')
        if case['name']=='root_future_progress_failure':need(a['value']['success'] is False and len(a['substep_maps'])==4 and len(a['cycle_maps'])==2 and len(a['cell_maps'])==0 and a['first_uncertified_substep']==4,'retained valid certified prefix without final cell')
        else:need(not a['substep_maps'] and not a['cycle_maps'] and not a['cell_maps'] and a['first_uncertified_substep']==0,'no fabricated matrices at unsupported initial')
        if case['name']=='root_invalid_q_dimension':need(a['value']['success'] is False,'invalid value')
        elif case['name']!='root_future_progress_failure':need(a['value']['success'] is True,'valid boundary forward value preserved')
    for q in owned:need(sha(q)==frozen[str(q)]['sha256'],'owned inputs unchanged')
    for q in sources:need(q.read_bytes()==snapshots[str(q)],'root audit sources unchanged')
    need(sha(args.freeze)==args.freeze_sha,'freeze unchanged');report=dict(decision='PASS_SELECTED_AUGMENTED_CYCLE_CELL_SENSITIVITIES',scope=__doc__,source_sha256=sha(Path(__file__)),binary_sha256=args.binary_sha,freeze_sha256=args.freeze_sha,value_binary_sha256=VALUE_SHA,base_binary_sha256=BASE_SHA,FD_value_calls=len(fd),strict_physical_diagnostic_calls=len(physical),positive_cases=4,unsupported_cases=4,invalid_cases=1,cases=reports,phase5='NOT_ACCEPTED',new_plant=False);dump(out/'audit.json',report);dump(out/'READY.json',{'files':{q.name:dict(sha256=sha(q),bytes=q.stat().st_size) for q in out.iterdir() if q.is_file()},'scope':__doc__});print(json.dumps(report))
if __name__=='__main__':main()
