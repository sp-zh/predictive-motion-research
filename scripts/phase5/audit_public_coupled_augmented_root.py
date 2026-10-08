#!/usr/bin/env python3
"""Paired native transition audit plus independent rational C/w/s/r oracle.

Existing development initial states and synthetic component cases only.
No simulator, derivative, fitting or main-controller call.
"""
import argparse,copy,csv,hashlib,json,math,subprocess,sys
from pathlib import Path
from public_coupled_augmented_root_reference import exact_command_progress

BASE_BINARY_SHA='fa1a00344e73d8fe2266541ba4e2b34c362351b30a4f21dfa34c04867f585a04'
RAW_SHA='ea70d9e8b01bc6e44387e2f4701779243bb1b202020a61aef18312fac1c054e8'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def need(b,msg):
    if not b:raise AssertionError(msg)
def finite_vector(v,n):
    need(type(v) is list and len(v)==n,'vector dimensions')
    need(all(type(x) in (int,float) and math.isfinite(x) for x in v),'finite real vector')
def maxdiff(a,b):
    need(len(a)==len(b),'same dimensions');return max(abs(x-y) for x,y in zip(a,b))
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('output','binary','freeze','predeclared'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--binary-sha',required=True);p.add_argument('--freeze-sha',required=True)
    args=p.parse_args();out=args.output;out.mkdir(exist_ok=False,parents=True)
    root=Path('/home/codextransfer/predictive_motion');base=root/'build-public-coupled-cpp-v2/public_coupled_probe_v2';xml=root/'experiments/generated/inspection/inspection_fr3.xml';const=root/'results/phase5/development/public-coupled-servo-v1-training/public_constants.json';raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013/raw.csv')
    need(sha(base)==BASE_BINARY_SHA and sha(args.binary)==args.binary_sha and sha(args.freeze)==args.freeze_sha and sha(raw)==RAW_SHA,'fixed identities')
    frozen={x['path']:x for x in json.loads(args.freeze.read_text())['files']}
    owned=[args.binary,base,xml,const,raw]+list((root/'tools/phase5_public_coupled_cpp_v2').glob('*'))+list((root/'tools/phase5_public_coupled_augmented_cpp').glob('*'))
    for q in owned:need(str(q) in frozen and sha(q)==frozen[str(q)]['sha256'],'owned source frozen '+str(q))
    source=Path(__file__);source_bytes=source.read_bytes();reference=Path(__file__).with_name('public_coupled_augmented_root_reference.py');reference_bytes=reference.read_bytes();fixture=json.loads(args.predeclared.read_text());state={k:fixture[k] for k in ('q','v','C','w','s','r')}
    positives=[{'name':fixture['name'],'state':state,'cells':fixture['cells']}]
    held={'cycles':16,'alpha':[.07*(-1 if j%2 else 1) for j in range(7)],'b':.03}
    positives.append({'name':'root_one_held16cycle_cell','state':state,'cells':[held]})
    positives.append({'name':'root_split_held16cycles','state':state,'cells':[dict(held,cycles=n) for n in (1,10,3,2)]})
    positives.append({'name':'root_10cycle_nonzero_history','state':state,'cells':[dict(held,cycles=10)]})
    positives.append({'name':'root_zero_alpha_nonzero_w','state':state,'cells':[dict(held,cycles=3,alpha=[0.]*7,b=0.)]})
    with raw.open() as f:rows=list(csv.DictReader(f))
    v=lambda row,p:[float(row[p+str(j)]) for j in range(7)]
    i=1380;recorded_state={'q':v(rows[i],'q_before_'),'v':v(rows[i],'v_before_'),'C':v(rows[i-1],'target_'),'w':v(rows[i-1],'command_velocity_'),'s':.2,'r':.08}
    positives.append({'name':'root_recorded8cycles','state':recorded_state,'cells':[{'cycles':1,'alpha':v(rows[i+2*k],'command_acceleration_'),'b':0.} for k in range(8)]})
    c=json.loads(const.read_text());negative=[]
    def neg(name,change):
        x=copy.deepcopy(positives[0]);x['name']=name;change(x);negative.append(x)
    neg('root_q_dimension6',lambda x:x['state']['q'].pop())
    neg('root_w_dimension6',lambda x:x['state']['w'].pop())
    neg('root_C_nonfinite',lambda x:x['state']['C'].__setitem__(0,'.nan'))
    neg('root_C_outside_declared_controls',lambda x:x['state']['C'].__setitem__(0,c['control_range'][0]-.001))
    neg('root_w_over_command_V',lambda x:x['state']['w'].__setitem__(0,.1))
    neg('root_alpha_over_command_A',lambda x:x['cells'][0]['alpha'].__setitem__(0,1.1))
    neg('root_alpha_nonfinite',lambda x:x['cells'][0]['alpha'].__setitem__(0,'.nan'))
    neg('root_progress_negative',lambda x:x['state'].update(s=-.01))
    neg('root_progress_speed_over_domain',lambda x:x['state'].update(r=.3))
    neg('root_finite_velocity_arithmetic_failure',lambda x:x['state'].update(v=[1e308]*7))
    neg('root_future_progress_domain_failure',lambda x:x['cells'][0].update(b=1e308))
    for name,value in [('zero',0),('negative',-1),('fractional',.5),('bool',True),('nonfinite','.nan'),('quoted','1'),('too_many',6000)]:
        neg('root_cycles_'+name,lambda x,value=value:x['cells'][0].update(cycles=value))
    neg('root_empty_mesh',lambda x:x.update(cells=[]))
    neg('root_second_cycle_velocity_domain_failure',lambda x:(x['state'].update(w=[.060]*7),x.update(cells=[{'cycles':2,'alpha':[.5]*7,'b':0.}])))
    neg('root_second_cycle_progress_domain_failure',lambda x:(x['state'].update(r=.195),x.update(cells=[{'cycles':2,'alpha':[0.]*7,'b':1.}])))
    inputs={'scope':__doc__,'cases':positives+negative};dump(out/'cases.json',inputs)
    (out/'SOURCE_SNAPSHOT.py').write_bytes(source_bytes);(out/'REFERENCE_SNAPSHOT.py').write_bytes(reference_bytes);(out/'PREDECLARED_SNAPSHOT.json').write_bytes(args.predeclared.read_bytes())
    # Independent exact rational formulas produce every held target; no wrapper is used.
    reference_traces=[];base_cases=[]
    for case in positives:
        st=case['state'];trace=exact_command_progress(st['C'],st['w'],st['s'],st['r'],[(x['cycles'],x['alpha'],x['b']) for x in case['cells']]);reference_traces.append(trace)
        base_cases.append({'name':case['name'],'q':st['q'],'v':st['v'],'targets':[x['C'] for x in trace]})
    dump(out/'independent_held_targets.json',{'cases':base_cases,'box_cases':[]});dump(out/'command_progress_reference.json',reference_traces)
    def invoke(binary,inp,dest):
        result=subprocess.run([str(binary),str(xml),str(const),str(inp),str(dest)],capture_output=True,text=True)
        dest.with_suffix('.stdout').write_text(result.stdout);dest.with_suffix('.stderr').write_text(result.stderr);dest.with_suffix('.exit').write_text(str(result.returncode)+'\n');need(result.returncode==0,'native CLI return')
        return json.loads(dest.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
    augmented=invoke(args.binary,out/'cases.json',out/'augmented.json');physical=invoke(base,out/'independent_held_targets.json',out/'physical.json')
    need(augmented['model_success'] is True and physical['model_success'] is True,'model initialized')
    need(len(augmented['cases'])==len(inputs['cases']) and [x['name'] for x in augmented['cases']]==[x['name'] for x in inputs['cases']],'exact ordered augmented roster')
    need(len(physical['cases'])==len(positives) and [x['name'] for x in physical['cases']]==[x['name'] for x in positives],'exact ordered base roster')
    def finite_tree(value):
        if type(value) in (int,float):need(math.isfinite(value),'all native numeric outputs finite')
        elif type(value) is list:
            for x in value:finite_tree(x)
        elif type(value) is dict:
            for x in value.values():finite_tree(x)
    finite_tree(augmented);finite_tree(physical)
    reports=[];maxima={k:0. for k in ('q','v','C','w','s','r','elapsed_s')}
    for n,case in enumerate(positives):
        a=augmented['cases'][n];b=physical['cases'][n];need(type(a['success']) is bool and a['success'] is True and b['success'] is True,'positive outcomes')
        trace=a['substeps'];ref=reference_traces[n];need(len(trace)==len(ref)==len(b['trace']),'complete substep roster')
        local={k:0. for k in maxima}
        need(type(a['has_final_state']) is bool and a['has_final_state'] is True,'successful final state')
        cycle_counts=[x['cycles'] for x in case['cells']];total=sum(cycle_counts)
        need(len(a['cycle_end_states'])==total and len(a['cell_end_states'])==len(case['cells']),'complete cycle/cell states')
        cell_indices=[];offset=0
        for count in cycle_counts:offset+=count;cell_indices.append(offset-1)
        for cy,end in enumerate(a['cycle_end_states']):
            point=trace[2*cy+1];cp=ref[2*cy+1]
            for key in ('q','v','C','w'):finite_vector(end[key],7);need(end[key]==point[key],'cycle endpoint physical/command consistency')
            for key in ('s','r'):need(abs(end[key]-cp[key])<=2e-13,'cycle progress endpoint')
        for cell,index in enumerate(cell_indices):need(a['cell_end_states'][cell]==a['cycle_end_states'][index],'cell/cycle endpoint consistency')
        need(a['final_state']==a['cycle_end_states'][-1],'last complete state consistency')
        for idx,(ap,bp,cp) in enumerate(zip(trace,b['trace'],ref)):
            for key in ('q','v','C','w'):finite_vector(ap[key],7)
            for key in ('q','v'):local[key]=max(local[key],maxdiff(ap[key],bp[key]))
            for key in ('C','w'):local[key]=max(local[key],maxdiff(ap[key],cp[key]))
            for key,native_key in [('s','s_reference'),('r','r_reference'),('elapsed_s','elapsed_s')]:
                x=ap[native_key];need(type(x) in (int,float) and math.isfinite(x),'finite scalar');local[key]=max(local[key],abs(x-cp[key]))
            need(type(ap['half']) is int and ap['half']==idx%2+1,'two held substeps');
            finite_vector(ap['friction']['force'],7);need(type(ap['friction']['iterations']) is int and 1<=ap['friction']['iterations']<=100,'friction iteration type/range');need(0<=ap['friction']['original_KKT']<=1e-10,'friction KKT');
            if idx%2==1:need(ap['C']==trace[idx-1]['C'] and ap['w']==trace[idx-1]['w'],'same held target/command at both2ms points')
            need(ap['control_clips']==0 and ap['force_clips']==bp['force_clips'],'clip diagnostics')
        need(local['q']<=2e-12 and local['v']<=1e-10 and all(local[k]<=2e-13 for k in ('C','w','s','r','elapsed_s')),'declared component parity gates')
        if case['name']=='root_recorded8cycles':
            observed_q=observed_v=0.
            for k,point in enumerate(trace):
                observed_q=max(observed_q,maxdiff(point['q'],v(rows[i+k],'q_post_')));observed_v=max(observed_v,maxdiff(point['v'],v(rows[i+k],'v_post_')))
            need(observed_q<=1e-6 and observed_v<=1e-4,'tight recorded16substep component check');local['observed_q']=observed_q;local['observed_v']=observed_v
        for key in maxima:maxima[key]=max(maxima[key],local[key])
        reports.append({'name':case['name'],'substeps':len(trace),'maximum_differences':local})
    one=augmented['cases'][1];split=augmented['cases'][2]
    need(one['final_state']==split['final_state'],'held-input final state independent of cell subdivision')
    for a,b in zip(one['substeps'],split['substeps']):
        for key in ('q','v','C','w'):need(a[key]==b[key],'held-input physical/command substeps independent of cell subdivision')
    for case,answer in zip(negative,augmented['cases'][len(positives):]):
        need(type(answer['success']) is bool and answer['success'] is False and type(answer.get('error')) is str and bool(answer['error']),'explicit negative outcome')
        if case['name'].startswith('root_second_cycle_'):
            need(len(answer['substeps'])==2 and len(answer['cycle_end_states'])==1 and answer['has_final_state'] is True,'retained successful cycle before future domain failure')
            need(answer['final_state']==answer['cycle_end_states'][0],'last complete valid cycle retained')
        reports.append({'name':case['name'],'success':False,'error':answer['error']})
    need(source.read_bytes()==source_bytes and reference.read_bytes()==reference_bytes,'root source unchanged')
    for q in owned:need(sha(q)==frozen[str(q)]['sha256'],'owned source unchanged '+str(q))
    need(sha(args.freeze)==args.freeze_sha and sha(args.binary)==args.binary_sha,'freeze/binary unchanged')
    report={'decision':'PASS_PAIRED_AUGMENTED_COMPONENT_TRANSITION','scope':__doc__,'source_sha256':hashlib.sha256(source_bytes).hexdigest(),'reference_sha256':hashlib.sha256(reference_bytes).hexdigest(),'binary_sha256':args.binary_sha,'freeze_sha256':args.freeze_sha,'base_binary_sha256':BASE_BINARY_SHA,'raw_sha256':RAW_SHA,'cases':reports,'maximum_differences':maxima,'phase5':'NOT_ACCEPTED','new_plant':False};dump(out/'audit.json',report)
    files={x.name:{'sha256':sha(x),'bytes':x.stat().st_size} for x in out.iterdir() if x.is_file()};dump(out/'READY.json',{'files':files,'scope':__doc__});print(json.dumps({'positive':len(positives),'negative':len(negative),'maxima':maxima}))
if __name__=='__main__':main()
