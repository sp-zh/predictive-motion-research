#!/usr/bin/env python3
"""Complete fixed-roster saved-output review after a retained FD branch failure.

No new extension predictor call, fitting or changed FD input/epsilon/gate.
Complete12 originally declared2fa domain controls and2 frozen-e2c nominal
component diagnostics for the failed case; no plant or new protocol execution.
"""
import argparse,json,hashlib,subprocess
from pathlib import Path
import numpy as np
from audit_public_augmented_sensitivity_root import pack,point,close,BASE_SHA,VALUE_SHA,H
from audit_public_physical_derivative_root import need,numbers,compare
from public_augmented_map_root_checks import maps,prefix,CERT
EPS=(1e-6,3e-7)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('saved','output','freeze'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--freeze-sha',required=True);args=p.parse_args();saved=args.saved;out=args.output;out.mkdir(parents=True,exist_ok=False);root=Path('/home/codextransfer/predictive_motion');base=root/'build-public-coupled-cpp-v2/public_coupled_probe_v2';value=root/'build-public-coupled-augmented-cpp-v1/public_coupled_augmented_probe';derivative=root/'build-public-coupled-derivative-cpp-v1/public_coupled_derivative_probe';xml=root/'experiments/generated/inspection/inspection_fr3.xml';const=root/'results/phase5/development/public-coupled-servo-v1-training/public_constants.json';need(sha(base)==BASE_SHA and sha(value)==VALUE_SHA and sha(derivative)=='e2c75c09001ba354ca5371cbfc594a9765c62098d4cdb52e6a1442adc055c6a4' and sha(args.freeze)==args.freeze_sha,'original frozen component identities')
    source=Path(__file__);source_bytes=source.read_bytes();(out/'SOURCE_SNAPSHOT.py').write_bytes(source_bytes);files={str(f):dict(sha256=sha(f),bytes=f.stat().st_size) for f in saved.iterdir() if f.is_file()};dump(out/'SAVED_INPUT_IDENTITIES.json',files)
    cases=json.loads((saved/'cases.json').read_text())['cases'];analytic=json.loads((saved/'analytic.json').read_text())['cases'];lookup=json.loads((saved/'extension_oracle_values.json').read_text());roster=json.loads((saved/'extension_FD_roster.json').read_text())['cases'];nominals=json.loads((saved/'closed_nominal_000.json').read_text())['cases'];diagnosis=json.loads((saved/'BRANCH_GATE_FAILURE_DIAGNOSIS.json').read_text());reports=[]
    for case,a,n in zip(cases[:6],analytic[:6],nominals[:6]):
        need(a['value']=={k:v for k,v in n.items() if k!='name'},'original nominal unchanged');gm=maps(case,a);dirs=[('state',j) for j in range(30)]+[(i,j) for i in range(len(case['cells'])) for j in range(8)];epsreports=[]
        ref=lookup[case['name']+'_nominal']['substeps'];need(len(ref)==len(a['value']['substeps']),'complete nominal oracle')
        for p,q in zip(a['value']['substeps'],ref):close(p['q'],q['q'],1e-12,'nominal oracle q');close(p['v'],q['v'],1e-11,'nominal oracle v');close(pack(point(p))[14:],pack(point(q))[14:],2e-13,'nominal polynomial oracle')
        for ei,e in enumerate(EPS):
            maxabs=maxratio=0.;failed_entries=0
            for di,(ci,j) in enumerate(dirs):
                minus,plus=[lookup[f'{case["name"]}_{ei}_{di}_{sign}']['substeps'] for sign in (-1,1)]
                for i,(A,B) in enumerate(gm):
                    fd=(pack(point(plus[i]))-pack(point(minus[i])))/(2*e);col=A[:,j] if ci=='state' else B[:,8*ci+j];error=abs(col-fd);ratio=error/(5e-7+5e-6*abs(col));need(np.isfinite(ratio).all(),'finite FD metrics');maxabs=max(maxabs,float(error.max()));maxratio=max(maxratio,float(ratio.max()));failed_entries+=int((ratio>1).sum())
            issues=[x for x in diagnosis['issues'] if x['case']==case['name'] and x['probe'].startswith(case['name']+'_'+str(ei)+'_')];epsreports.append(dict(epsilon=e,max_absolute=maxabs,max_gate_ratio=maxratio,entry_gate_pass=bool(failed_entries==0),failed_entry_comparisons=failed_entries,changed_branch_probes=sorted({x['probe'] for x in issues}),same_branch_gate_pass=not issues))
        passed=all(x['entry_gate_pass'] and x['same_branch_gate_pass'] for x in epsreports);reports.append(dict(name=case['name'],columns=len(dirs),all_structural_checks_pass=True,all_requested_two_epsilon_gates_pass=passed,epsilons=epsreports))
    for case,a,n in zip(cases[6:],analytic[6:],nominals[6:]):
        need(a['value']=={k:v for k,v in n.items() if k!='name'} and a['extension_jacobian_success'] is False and a['certifies_two_sided_admissible_neighborhood'] is False and 'certificate_name' not in a and bool(a['error']),'original failed value/no fullcertificate');prefix(case,a)
        if case['name']=='root_extension_future_r_failure':need(len(a['value']['substeps'])==len(a['substep_maps'])==4 and len(a['cycle_maps'])==2 and not a['cell_maps'] and a['first_uncertified_substep']==4,'exact failedforward actualprefix')
        else:need(not a['substep_maps'] and not a['cycle_maps'] and not a['cell_maps'] and a['first_uncertified_substep']==0,'uncertified initial no maps')
    start=cases[0];chosen=[];ids=[]
    for ei,e in enumerate(EPS):
        for di in (28,29,37):
            for sign in (-1,1):name=f'{start["name"]}_{ei}_{di}_{sign}';chosen.append(next(x for x in roster if x['name']==name));ids.append((e,di,sign,name))
    # New diagnostic calls are declared here and do not rerun the extension.
    bad=next(i for i,c in enumerate(cases[:6]) if c['name']=='root_boundary_initial_w_plusV');case=cases[bad];ans=analytic[bad];phys=[];previous=case['state']
    for i,t in enumerate(ans['value']['substeps']):phys.append(dict(name='failed_case_nominal_half'+str(i+1),q=previous['q'],v=previous['v'],C=t['C']));previous=point(t)
    need(len(phys)==2,'only2 nominal components');dump(out/'PRE_CALL_DECLARATION.json',dict(scope=__doc__,closed_controls=chosen,physical_nominal_inputs=phys,frozen_derivative_sha256=sha(derivative),unchanged_epsilons=EPS,unchanged_entry_gate='5e-7+5e-6*abs(analytic)'))
    def invoke(binary,inputs,stem):
        src=out/(stem+'_inputs.json');dest=out/(stem+'.json');dump(src,{'cases':inputs});r=subprocess.run([str(binary),str(xml),str(const),str(src),str(dest)],capture_output=True,text=True);dest.with_suffix('.stdout').write_text(r.stdout);dest.with_suffix('.stderr').write_text(r.stderr);dest.with_suffix('.exit').write_text(str(r.returncode)+'\n');need(r.returncode==0,'diagnostic returncode');j=json.loads(dest.read_text());numbers(j);need(j['model_success'] is True and len(j['cases'])==len(inputs) and [x['name'] for x in j['cases']]==[x['name'] for x in inputs],'complete diagnostic roster');return j['cases']
    original=invoke(value,chosen,'closed_direction_controls');gm=maps(start,analytic[0]);onesided=[]
    for (e,di,sign,name),a in zip(ids,original):
        need(type(a['success']) is bool and a['success']==(sign==1),'selected exteriorminus refused/feasibleplus admits in original model domain')
        if sign<0:need(type(a['error']) is str and bool(a['error']),'explicit original closed rejection');continue
        need(a['has_final_state'] is True and len(a['substeps'])==len(gm)==2*sum(x['cycles'] for x in start['cells']),'complete selectedplus timestamps');er=[]
        for i,q in enumerate(a['substeps']):close(pack(point(q)),pack(point(lookup[name]['substeps'][i])),2e-13,'selectedplus parity');A,B=gm[i];col=A[:,di] if di<30 else B[:,di-30];er.append(compare(col,(pack(point(q))-pack(point(analytic[0]['value']['substeps'][i])))/e))
        onesided.append(dict(epsilon=e,direction_column=di,max_gate_ratio=max(x['max_gate_ratio'] for x in er)))
    ds=invoke(derivative,phys,'failed_case_nominal_physical_components');J=[]
    for d,t in zip(ds,ans['value']['substeps']):need(d['value_success'] is True and d['jacobian_success'] is True,'strict nominal physical component remains certified');close(d['value']['q'],t['q'],0.,'nominal component q parity');close(d['value']['v'],t['v'],0.,'nominal component v parity');J.append(np.asarray(d['jacobian']))
    P=J[1][:,:14]@J[0][:,:14];Q=J[1][:,:14]@J[0][:,14:]+J[1][:,14:]
    for m,physical in zip(ans['substep_maps'],(J[0],np.c_[P,Q])):A=np.asarray(m['A']);B=np.asarray(m['B']);close(A[:14,:14],physical[:,:14],1e-12,'independent frozen nominal P');close(A[:14,14:21],physical[:,14:],1e-12,'independent frozen nominal Q');close(A[:14,21:28],H*physical[:,14:],1e-12,'independent nominal hQ');close(B[:14,:7],H*H*physical[:,14:],1e-12,'independent nominal h²Q')
    for n,e in files.items():need(sha(Path(n))==e['sha256'],'original saved evidence unchanged')
    need(source.read_bytes()==source_bytes and sha(args.freeze)==args.freeze_sha,'review source/freeze unchanged');record=dict(decision='PARTIAL_SELECTED_EXTENSION_VALIDATION_WITH_RETAINED_FD_BRANCH_FAILURE',scope=__doc__,source_sha256=sha(source),original_failed_audit_source_sha256=sha(saved/'SOURCE_audit_public_augmented_extension_root.py'),prefix_expectation_repair='Initial saved-review incorrectly expected5halfsteps; original2fa prechecks fullcycle endpoint beforeanyhalf, so correct4halves/2cycles/firstuncertified4. Failed original source/output preserved, no model/gate/epsilon change.',first_audit_outcome='FAIL_DECLARED_SAME_BRANCH_FD_GATE; never relabeledPASS',all_original_cases_retained=True,changed_probe_count=diagnosis['changed_probe_count'],changed_cases=diagnosis['changed_cases'],all_case_structure_and_prefix_checks_pass=True,cases=reports,all_two_epsilon_pass_cases=sum(x['all_requested_two_epsilon_gates_pass'] for x in reports),original_closed_direction_calls=12,selected_original_model_admissible_one_sided=onesided,extra_original_nominal_physical_derivative_calls=2,failed_case_nominal_chain_exact=True,mathematical_interpretation='Nominal strict certificate is infinitesimal; neither its margins nor a successful smaller epsilon guarantee a finite branch-preserving radius. Original two-epsilon samebranch/entry gates remain failed for this predeclaredfixture. No safety/main/task or uniform-domain claim.',phase5='NOT_ACCEPTED',new_plant=False);dump(out/'audit.json',record);dump(out/'READY.json',{'files':{q.name:dict(sha256=sha(q),bytes=q.stat().st_size) for q in out.iterdir() if q.is_file()},'scope':__doc__});print(json.dumps(record))
if __name__=='__main__':main()
