#!/usr/bin/env python3
"""Independent command/progress-extension Jacobian audit, not admissibility.

Closed nominal2fa values remain exact; independent rational command/progress
plus originalfa1 physical rollouts supply mathematical exterior FD probes.
"""
import argparse,copy,hashlib,json,math,subprocess
from pathlib import Path
import numpy as np
from audit_public_physical_derivative_root import signature,compare,numbers,need
from audit_public_augmented_sensitivity_root import pack,point,close,H,DT,BATCH,BASE_SHA,VALUE_SHA
from public_coupled_augmented_root_reference import exact_command_progress
from public_augmented_map_root_checks import maps,metadata,prefix,CERT
EPS=(1e-6,3e-7)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('output','binary','freeze','predeclared'):p.add_argument('--'+k,type=Path,required=True)
    for k in ('binary-sha','freeze-sha'):p.add_argument('--'+k,required=True)
    args=p.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
    root=Path('/home/codextransfer/predictive_motion');base=root/'build-public-coupled-cpp-v2/public_coupled_probe_v2';value=root/'build-public-coupled-augmented-cpp-v1/public_coupled_augmented_probe';xml=root/'experiments/generated/inspection/inspection_fr3.xml';const=root/'results/phase5/development/public-coupled-servo-v1-training/public_constants.json';prior=root/'results/phase5/development/public-coupled-derivative-cpp-v1/inputs/cases.json'
    need(sha(base)==BASE_SHA and sha(value)==VALUE_SHA and sha(args.binary)==args.binary_sha and sha(args.freeze)==args.freeze_sha,'pinned native identities');frozen={x['path']:x for x in json.loads(args.freeze.read_text())['files']};owned=[base,value,args.binary,xml,const,prior]
    for directory in ('phase5_public_coupled_cpp_v2','phase5_public_coupled_augmented_cpp','phase5_public_coupled_derivative_cpp','phase5_public_coupled_augmented_sensitivity_cpp','phase5_public_coupled_augmented_extension_cpp'):owned+=list((root/'tools'/directory).glob('*'))
    for q in owned:need(str(q) in frozen and sha(q)==frozen[str(q)]['sha256'],'owned source frozen '+str(q))
    sources=[Path(__file__)]+[Path(__file__).with_name(n) for n in ('public_augmented_map_root_checks.py','audit_public_augmented_sensitivity_root.py','audit_public_physical_derivative_root.py','public_coupled_augmented_root_reference.py')];snapshots={str(q):q.read_bytes() for q in sources}
    for q in sources:(out/('SOURCE_'+q.name)).write_bytes(snapshots[str(q)])
    (out/'PREDECLARED.json').write_bytes(args.predeclared.read_bytes());positives=json.loads(args.predeclared.read_text())['cases'];need(len(positives)==6,'all6 predeclared cases retained');c=json.loads(const.read_text());negatives=[]
    def neg(name,change):
        x=copy.deepcopy(positives[0]);x['name']=name;change(x);negatives.append(x)
    neg('root_extension_C_boundary',lambda x:x['state']['C'].__setitem__(0,c['control_range'][0]))
    weak=next(x for x in json.loads(prior.read_text())['cases'] if x['name']=='weak_lower_zero_gradient')
    neg('root_extension_weak_physical',lambda x:x['state'].update(q=weak['q'],v=weak['v'],C=weak['C']))
    neg('root_extension_future_r_failure',lambda x:(x['state'].update(s=.2,r=.199),x.update(cells=[dict(cycles=4,alpha=[0.]*7,b=.1)])))
    neg('root_extension_invalid_q',lambda x:x['state']['q'].pop())
    neg('root_extension_invalid_s',lambda x:x['state'].update(s=-.01))
    cases=positives+negatives;dump(out/'cases.json',{'cases':cases});dump(out/'PRE_FORECAST_DECLARATION.json',dict(cases=cases,epsilons=EPS,absolute_per_entry=5e-7,relative_per_entry=5e-6,structural=1e-12,nominal_oracle_q=1e-12,nominal_oracle_v=1e-11,nominal_oracle_command_progress=2e-13,batch_cap=BATCH,scope=__doc__))
    def invoke(binary,inp,dest):
        r=subprocess.run([str(binary),str(xml),str(const),str(inp),str(dest)],capture_output=True,text=True);dest.with_suffix('.stdout').write_text(r.stdout);dest.with_suffix('.stderr').write_text(r.stderr);dest.with_suffix('.exit').write_text(str(r.returncode)+'\n');need(r.returncode==0,'native returncode');data=json.loads(dest.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)));numbers(data);need(data['model_success'] is True,'model initialized');return data
    def batches(binary,roster,prefix,physical=False):
        answers=[]
        for k in range(0,len(roster),BATCH):
            inp={'cases':roster[k:k+BATCH]}
            if physical:inp['box_cases']=[]
            src=out/f'{prefix}_{k//BATCH:03d}_inputs.json';dump(src,inp);r=invoke(binary,src,out/f'{prefix}_{k//BATCH:03d}.json');need(len(r['cases'])==len(inp['cases']) and [x['name'] for x in r['cases']]==[x['name'] for x in inp['cases']],'exact batch roster');answers+=r['cases']
        need(len({x['name'] for x in answers})==len(answers),'unique roster');return answers
    fd=[];directions={}
    for case in positives:
        dirs=[('state',j) for j in range(30)]+[(i,j) for i in range(len(case['cells'])) for j in range(8)];directions[case['name']]=dirs;n=copy.deepcopy(case);n['name']=case['name']+'_nominal';fd.append(n)
        for ei,e in enumerate(EPS):
            for di,(ci,j) in enumerate(dirs):
                for sign in (-1,1):
                    x=copy.deepcopy(case);x['name']=f'{case["name"]}_{ei}_{di}_{sign}'
                    if ci=='state':
                        if j<28:x['state'][('q','v','C','w')[j//7]][j%7]+=sign*e
                        else:x['state'][('s','r')[j-28]]+=sign*e
                    elif j<7:x['cells'][ci]['alpha'][j]+=sign*e
                    else:x['cells'][ci]['b']+=sign*e
                    fd.append(x)
    need(len(fd)==1014,'predeclared extension roster');dump(out/'extension_FD_roster.json',dict(cases=fd,scope='Mathematical command/progress extension; exterior states/controls are not admissible histories.'))
    references={};physical_rollouts=[]
    for x in fd:
        z=x['state'];ref=exact_command_progress(z['C'],z['w'],z['s'],z['r'],[(y['cycles'],y['alpha'],y['b']) for y in x['cells']]);references[x['name']]=ref;physical_rollouts.append(dict(name=x['name'],q=z['q'],v=z['v'],targets=[y['C'] for y in ref]))
    dump(out/'extension_targets_precomputed.json',{'cases':physical_rollouts,'box_cases':[]})
    model=invoke(args.binary,out/'cases.json',out/'analytic.json');policy=model['policy'];need(policy['certificate_name']==CERT and policy['certifies_two_sided_admissible_neighborhood'] is False and policy['control_margin']==1e-8,'extension policy explicit');analytic=model['cases'];need(len(analytic)==len(cases) and [x['name'] for x in analytic]==[x['name'] for x in cases],'complete analytic roster');nominals=batches(value,cases,'closed_nominal')
    rolled=batches(base,physical_rollouts,'extension_physical_value',True);lookup={};physical=[];exterior=0
    for x,a in zip(fd,rolled):
        ref=references[x['name']];need(a['success'] is True and len(a['trace'])==len(ref),'complete original self-propagated physical extension rollout');trace=[];previous=x['state'];outside=not(0<=previous['s']<=1 and 0<=previous['r']<=.2 and max(abs(v) for v in previous['w'])<=.0625) or any(max(abs(v) for v in cell['alpha'])>1 for cell in x['cells'])
        for i,(q,cp) in enumerate(zip(a['trace'],ref)):
            t=dict(q=q['q'],v=q['v'],C=cp['C'],w=cp['w'],s_reference=cp['s'],r_reference=cp['r'],friction=q['friction'],control_clips=q['control_clips'],force_clips=q['force_clips']);trace.append(t);outside=outside or not(0<=cp['s']<=1 and 0<=cp['r']<=.2 and max(abs(v) for v in cp['w'])<=.0625)
            physical.append(dict(name=f'{x["name"]}_p{i}',q=previous['q'],v=previous['v'],targets=[cp['C']]));previous=point(t)
        lookup[x['name']]=dict(substeps=trace,mathematical_extension_exterior=outside);exterior+=int(outside)
    dump(out/'extension_oracle_values.json',lookup);need(exterior>0,'explicit exterior extension probes present');diagnostics=batches(base,physical,'strict_physical_diagnostic',True);plookup={x['name']:x for x in physical};dlookup={x['name']:x for x in diagnostics};signatures={}
    for x in fd:
        ss=[]
        for i,q in enumerate(lookup[x['name']]['substeps']):
            name=f'{x["name"]}_p{i}';a=dlookup[name];need(a['success'] is True and len(a['trace'])==1,'strict diagnostic success');a=a['last'];close(a['q'],q['q'],0.,'original physical q parity');close(a['v'],q['v'],0.,'original physical v parity');inp=plookup[name];sig=signature(dict(q=inp['q'],v=inp['v'],C=q['C']),a,c);ss.append(sig)
            limits=np.asarray(c['control_range']).reshape(7,2);C=np.asarray(q['C']);need(((C-limits[:,0])>1e-8).all() and ((limits[:,1]-C)>1e-8).all(),'strict physical C even at exterior probes')
            qlimits=np.asarray(c['joint_range']).reshape(7,2)
            for pose in (inp['q'],q['q']):pose=np.asarray(pose);need((pose>qlimits[:,0]).all() and (pose<qlimits[:,1]).all(),'strict initial/generated physical q support')
            need(0<=a['friction']['original_KKT']<=1e-10,'original physical friction KKT gate')
            M=np.asarray(a['M']);K=M+DT*np.diag(np.asarray(c['passive_damping'])-np.asarray(c['biasprm']).reshape(7,10)[:,2]);S=(np.asarray(a['H'])+np.asarray(a['H']).T)/2;matrices=[M,K,S];free=np.flatnonzero(np.asarray(a['friction']['branches'])==0)
            if len(free):matrices.append(S[np.ix_(free,free)])
            for mat in matrices:ev=np.linalg.eigvalsh(mat);need(ev[0]>0 and ev[-1]/ev[0]<=1e12,'strict perturbed M/K/H/Hff support')
        signatures[x['name']]=ss
    reports=[]
    for case,a,n in zip(positives,analytic[:6],nominals[:6]):
        need(a['value']=={key:val for key,val in n.items() if key!='name'},'exact original closed nominal values');gm=maps(case,a);ref=lookup[case['name']+'_nominal']['substeps'];need(len(ref)==len(a['value']['substeps']),'complete nominal oracle')
        for p,q in zip(a['value']['substeps'],ref):close(p['q'],q['q'],1e-12,'nominal rational/physical q');close(p['v'],q['v'],1e-11,'nominal rational/physical v');close(pack(point(p))[14:],pack(point(q))[14:],2e-13,'nominal rational command/progress')
        er=[]
        for ei,e in enumerate(EPS):
            errors=[]
            for di,(ci,j) in enumerate(directions[case['name']]):
                names=[f'{case["name"]}_{ei}_{di}_{sign}' for sign in (-1,1)];minus,plus=[lookup[n]['substeps'] for n in names]
                for n in names:need(signatures[n]==signatures[case['name']+'_nominal'],'same strict branches at every exterior/interior perturbation')
                for i,(A,B) in enumerate(gm):fdcol=(pack(point(plus[i]))-pack(point(minus[i])))/(2*e);col=A[:,j] if ci=='state' else B[:,8*ci+j];errors.append(compare(col,fdcol))
            er.append(dict(epsilon=e,max_absolute=max(x['max_absolute'] for x in errors),max_gate_ratio=max(x['max_gate_ratio'] for x in errors)))
        reports.append(dict(name=case['name'],columns=len(directions[case['name']]),epsilons=er))
    for case,a,n in zip(negatives,analytic[6:],nominals[6:]):
        need(a['extension_jacobian_success'] is False and a['certifies_two_sided_admissible_neighborhood'] is False and 'certificate_name' not in a and bool(a['error']),'explicit noncertified without fullcertificate');need(a['value']=={key:val for key,val in n.items() if key!='name'},'retained original negative/prefix values')
        prefix(case,a)
        if case['name']=='root_extension_future_r_failure':need(a['value']['success'] is False and len(a['value']['substeps'])==4 and len(a['substep_maps'])==4 and len(a['cycle_maps'])==2 and len(a['cell_maps'])==0 and a['first_uncertified_substep']==4,'valid boundary half retained before original forward failure')
        else:need(not a['substep_maps'] and not a['cycle_maps'] and not a['cell_maps'] and a['first_uncertified_substep']==0,'no fabricated initial matrices')
    # Original closed2fa must still reject inadmissible directions. Selected
    # plus directions stay valid at everytimestamp, so also verify one-sided FD.
    chosen=[];chosen_ids=[];start=positives[0]
    for ei,e in enumerate(EPS):
        for di in (28,29,37):
            for sign in (-1,1):
                name=f'{start["name"]}_{ei}_{di}_{sign}';chosen.append(next(x for x in fd if x['name']==name));chosen_ids.append((ei,e,di,sign,name))
    original=batches(value,chosen,'closed_direction_controls');startmaps=maps(start,analytic[0]);onesided=[]
    for (ei,e,di,sign,name),a in zip(chosen_ids,original):
        need(a['success']==(sign==1),'old closed domain rejects exterior minus, admits full valid plus direction')
        if sign<0:continue
        need(a['has_final_state'] is True and len(a['substeps'])==2*sum(x['cycles'] for x in start['cells'])==len(startmaps),'complete valid-direction timestamp roster')
        er=[]
        for i,q in enumerate(a['substeps']):
            close(pack(point(q)),pack(point(lookup[name]['substeps'][i])),2e-13,'valid one-sided original parity');A,B=startmaps[i];col=A[:,di] if di<30 else B[:,di-30];er.append(compare(col,(pack(point(q))-pack(point(analytic[0]['value']['substeps'][i])))/e))
        onesided.append(dict(epsilon=e,direction_column=di,max_gate_ratio=max(x['max_gate_ratio'] for x in er)))
    for q in owned:need(sha(q)==frozen[str(q)]['sha256'],'owned source unchanged')
    for q in sources:need(q.read_bytes()==snapshots[str(q)],'root sources unchanged')
    need(sha(args.freeze)==args.freeze_sha,'freeze unchanged');report=dict(decision='PASS_SELECTED_COMMAND_PROGRESS_EXTENSION_JACOBIANS',scope=__doc__,certificate_name=CERT,certifies_two_sided_admissible_neighborhood=False,source_sha256=sha(Path(__file__)),helper_sha256=sha(Path(__file__).with_name('public_augmented_map_root_checks.py')),binary_sha256=args.binary_sha,freeze_sha256=args.freeze_sha,extension_value_calls=len(fd),strict_physical_diagnostics=len(physical),closed_nominal_calls=len(cases),closed_direction_calls=len(chosen),exterior_extension_rollouts=exterior,positive_cases=6,physical_or_C_uncertified=2,future_failed=1,invalid=2,cases=reports,selected_admissible_one_sided_checks=onesided,phase5='NOT_ACCEPTED',new_plant=False);dump(out/'audit.json',report);dump(out/'READY.json',{'files':{q.name:dict(sha256=sha(q),bytes=q.stat().st_size) for q in out.iterdir() if q.is_file()},'scope':__doc__});print(json.dumps(report))
if __name__=='__main__':main()
