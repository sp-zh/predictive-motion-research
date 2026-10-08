#!/usr/bin/env python3
"""Independent bounded affine-kernel CLI audit, source-only until authorization.

One kernel batch, no original model/physical binary calls. The frozen root helper
independently assembles and pivots L. Retained source nominal values never reset
actual-coordinate propagation. Output mutation controls make no binary calls.
Native proof covers archived Result carrier normalization only, no real Model
construction/forward call. No model accuracy, admissibility or Phase5 claim.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import subprocess
from pathlib import Path

import numpy as np

HELPER_SHA = '4b8f0328125e8e797ddafcc4ae0e6e0572f65ca2fc5f0336a25b3d25b00b4e84'
BUNDLE_SHA = 'ce5731c49d4c4815d2e30d8079054310d1f73816d7906c607a1e76a4cf0c0a0c'
PLAN_SHA = '514bcc31b1bce001853c61e714b53802f2515a831762338baf0619f41bdc6518'
ARCHIVE_SHA = 'e42af2a0ca5a85047e371660f9fc565cdc0a28ace450235a1f3d6acb13d9de83'
F1_SHA = 'f1b7e6c7e4219fec2beb310540c725b448dcf021b3a95ddafc2922e8849bf1d6'
CERT = 'COMMAND_PROGRESS_EXTENSION_JACOBIAN_STRICT_PHYSICAL_V1'
ABS = 1e-11; REL = 1e-10
CLAIMS = ('connecting_segment','ball','admissibility','execution','safety','uniform_error_bound','controller_readiness')
LIMITS = dict(max_cases=32,max_cells=16,max_samples=512,max_nx=64,max_nu=16,max_terms=32,max_factor_rows=256,
              max_matrix_elements=2000000,max_document_bytes=67108864,max_problem_numeric_elements=8000000,
              max_cli_numeric_elements=16000000,arithmetic_abs=2e-13,arithmetic_rel=2e-13)


def need(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def load(path):
    return json.loads(Path(path).read_text(),parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def finite_tree(value):
    if type(value) in (int,float):
        need(math.isfinite(value),'finite JSON number')
    elif type(value) is list:
        for item in value:
            finite_tree(item)
    elif type(value) is dict:
        for item in value.values():
            finite_tree(item)


def array(value, shape):
    def numeric(x):
        return all(numeric(i) for i in x) if type(x) is list else type(x) in (int,float) and math.isfinite(x)
    need(type(value) is list and numeric(value),'typed numeric array')
    if shape and shape[0] == 0 and value == []:
        return np.zeros(shape)
    a = np.asarray(value,float); need(a.shape == shape,'shape '+str(shape)); return a


def check(actual, expected, label):
    e = np.asarray(expected,float)
    a = array(actual,e.shape) if e.ndim else actual
    if not e.ndim:
        need(type(a) in (int,float) and math.isfinite(a),'typed scalar '+label)
    a = np.asarray(a,float)
    need(np.isfinite(e).all() and np.isfinite(a).all(),'finite '+label)
    need((abs(a-e) <= ABS+REL*abs(e)).all(),label)


def scope(value):
    need(type(value) is dict and set(value) == set(CLAIMS),'exact scope roster')
    need(all(value[k] is False for k in CLAIMS),'no unsupported scope claims')


def packed(z):
    return np.r_[*[array(z[k],(7,)) for k in ('q','v','C','w')],z['s'],z['r']]


def point(p):
    return dict(q=p['q'],v=p['v'],C=p['C'],w=p['w'],s=p['s_reference'],r=p['r_reference'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('output','binary','freeze','prepared'):
        parser.add_argument('--'+key,required=True,type=Path)
    for key in ('binary-sha','freeze-sha','prepared-ready-sha','input-sha','policy-sha','schema-sha'):
        parser.add_argument('--'+key,required=True)
    args = parser.parse_args(); out = args.output; out.mkdir(parents=True,exist_ok=False)
    source = Path(__file__); helper_path = source.with_name('public_affine_horizon_root_reference.py')
    prepared = args.prepared; inputs_path = prepared/'inputs.json'; policy_path = prepared/'policy.json'
    need(sha(helper_path) == HELPER_SHA and sha(args.binary) == args.binary_sha and sha(args.freeze) == args.freeze_sha,'pinned runtime/source identities')
    need(sha(prepared/'READY.json') == args.prepared_ready_sha and sha(inputs_path) == args.input_sha and sha(policy_path) == args.policy_sha,'frozen prepared identities')
    manifest = load(prepared/'READY.json')['files']; retained = [source,helper_path,args.binary,args.freeze,prepared/'READY.json']
    for name, info in manifest.items():
        p = prepared/name; need(sha(p) == info['sha256'] and p.stat().st_size == info['bytes'],'closed prepared payload '+name); retained.append(p)
    need(sha(prepared/'archived_sources.json') == BUNDLE_SHA and sha(prepared/'ROOT_PLAN.json') == PLAN_SHA and
         sha(prepared/'INTERFACE_SCHEMA.md') == args.schema_sha,'frozen source bundle/plan/schema')
    startup = {str(p):sha(p) for p in retained}
    (out/'SOURCE_SNAPSHOT.py').write_bytes(source.read_bytes()); (out/'HELPER_SNAPSHOT.py').write_bytes(helper_path.read_bytes())
    for name in ('inputs.json','policy.json','expected.json','ROOT_PLAN.json','INTERFACE_SCHEMA.md','READY.json'):
        (out/('PREPARED_'+name)).write_bytes((prepared/name).read_bytes())
    (out/'FROZEN_INPUTS.json').write_bytes(args.freeze.read_bytes())
    frozen = {x['path']:x for x in load(args.freeze)['files']}
    for p in (source,helper_path,args.binary,inputs_path,policy_path,prepared/'archived_sources.json'):
        need(str(p) in frozen and sha(p) == frozen[str(p)]['sha256'],'selected execution input frozen '+str(p))
    policy = load(policy_path); inp = load(inputs_path); expected = load(prepared/'expected.json'); bundle = load(prepared/'archived_sources.json')
    need(policy['schema_version'] == 1 and policy['limits'] == LIMITS,'exact frozen source arithmetic/resource policy'); scope(policy['scope'])
    need(len(policy['artifacts']) == 1,'fixed artifact roster'); artifact = policy['artifacts'][0]
    need(artifact['id'] == 'root_archived_sources' and artifact['sha256'] == BUNDLE_SHA and
         artifact['source_binary_sha256'] == F1_SHA and artifact['certificate_name'] == CERT and
         artifact['archive_sha256'] == ARCHIVE_SHA and
         Path(artifact['path']).resolve() == (prepared/'archived_sources.json').resolve(),'policy source binding')
    need(sha(artifact['path']) == BUNDLE_SHA,'policy actual artifact bytes')
    need(expected['output_abs'] == ABS and expected['output_rel'] == REL and expected['helper_symmetry_abs'] == 1e-12,'preregistered checker gate')
    need(expected['schema_sha256'] == args.schema_sha and expected['refusal_codes'] ==
         dict(authentic_public='SOURCE_INCOMPLETE_OR_UNSUPPORTED',other='INVALID_SOURCE_SHAPE_OR_RESOURCE'),'locked schema/refusal contract')
    cases = inp['cases']; need(inp['schema_version'] == 1 and [c['name'] for c in cases] == [c['name'] for c in expected['cases']],'fixed input roster')
    need(len({c['name'] for c in cases}) == len(cases),'unique names')
    # Import the hash-locked independent helper only AFTER startup guards.
    spec = importlib.util.spec_from_file_location('root_frozen_affine_reference',helper_path)
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    complete = {r['name']:r for r in bundle['complete']}; refused = {r['name']:r for r in bundle['refused']}
    originals = dict(complete,**refused); cache = {}

    def public_normalized(case):
        row = complete[case['source']['row_name']]; initial = row['original_input']; recorded = row['original_output']
        value = recorded['value']; N = len(initial['cells']); cycles = [x['cycles'] for x in initial['cells']]
        need(recorded['extension_jacobian_success'] is True and value['success'] is True and value['has_final_state'] is True and
             recorded['first_uncertified_substep'] == -1 and recorded['certificate_name'] == CERT and
             recorded['certifies_two_sided_admissible_neighborhood'] is False,'full original source certificate')
        need(len(recorded['cell_maps']) == N and len(recorded['cycle_maps']) == sum(cycles) and
             len(recorded['substep_maps']) == len(value['substeps']) == 2*sum(cycles) and
             len(value['cycle_end_states']) == sum(cycles) and len(value['cell_end_states']) == N,'full original roster')
        cells = []; samples = []; cell_res = []; sample_res = []
        literal_origins = [initial['state']] + value['cell_end_states'][:-1]
        previous=initial['state']; global_cycle=0
        for c,n in enumerate(cycles):
            for k in range(1,n+1):
                m=recorded['cycle_maps'][global_cycle]
                need(all(type(m[key]) is int for key in ('cell','cycle','half')) and
                     (m['cell'],m['cycle'],m['half']) == (c,k,2),'all original cycle topology')
                need(m['certificate_name'] == CERT and m['certifies_two_sided_admissible_neighborhood'] is False and
                     m['origin'] == previous and m['cell_origin'] == literal_origins[c] and
                     m['state'] == value['cycle_end_states'][global_cycle] and
                     m['input'] == initial['cells'][c]['alpha']+[initial['cells'][c]['b']],'literal cycle source records')
                A=array(m['A'],(30,30)); B=array(m['B'],(30,8)); d=array(m['defect'],(30,))
                target=packed(m['state']); prediction=A@packed(previous)+B@array(m['input'],(8,))+d
                need((abs(target-prediction) <= 2e-13+2e-13*abs(target)).all(),'source nominal cycle-local identity')
                previous=m['state']; global_cycle+=1
        for c, m in enumerate(recorded['cell_maps']):
            need(all(type(m[key]) is int for key in ('cell','cycle','half')) and
                 (m['cell'],m['cycle'],m['half']) == (c,cycles[c],2),'original wholecell topology')
            need(m['certificate_name'] == CERT and m['certifies_two_sided_admissible_neighborhood'] is False,'wholecell source certificate')
            need(m['origin'] == literal_origins[c] and m['state'] == value['cell_end_states'][c] and
                 m['input'] == initial['cells'][c]['alpha']+[initial['cells'][c]['b']],'literal wholecell records')
            A=array(m['A'],(30,30)); B=array(m['B'],(30,8)); d=array(m['defect'],(30,))
            target=packed(m['state']); prediction=A@packed(m['origin'])+B@array(m['input'],(8,))+d
            need((abs(target-prediction) <= 2e-13+2e-13*abs(target)).all(),'source nominal affine cell gate')
            cell_res.append(float(np.max(abs(target-prediction)))); cells.append(dict(A=A,B=B,d=d))
        timing = [(c,k,h) for c,n in enumerate(cycles) for k in range(1,n+1) for h in (1,2)]
        for i, (m,p) in enumerate(zip(recorded['substep_maps'],value['substeps'])):
            c,k,h = timing[i]; need((m['cell'],m['cycle'],m['half']) == (p['cell'],p['cycle'],p['half']) == (c,k,h),'all original 2ms topology')
            need(all(type(row[key]) is int for row in (m,p) for key in ('cell','cycle','half')) and
                 type(p['elapsed_s']) in (int,float) and abs(p['elapsed_s']-.002*(i+1)) <= 2e-13,'typed original lattice timestamps')
            need(m['certificate_name'] == CERT and m['certifies_two_sided_admissible_neighborhood'] is False,'sample source certificate')
            need(m['cell_origin'] == literal_origins[c] and m['state'] == point(p) and
                 m['input'] == initial['cells'][c]['alpha']+[initial['cells'][c]['b']],'literal sample originals')
            A=array(m['cell_A'],(30,30)); B=array(m['cell_B'],(30,8)); d=array(m['cell_defect'],(30,))
            target=packed(m['state']); prediction=A@packed(m['cell_origin'])+B@array(m['input'],(8,))+d
            need((abs(target-prediction) <= 2e-13+2e-13*abs(target)).all(),'source nominal affine sample gate')
            sample_res.append(float(np.max(abs(target-prediction))))
            samples.append(dict(cell=c,A=A,B=B,d=d,cycle=k,half=h))
        return 30,8,cells,samples,cycles,cell_res,sample_res,packed(initial['state'])

    def reference(case):
        if case['source']['kind'] == 'public_saved_json':
            nx,nu,cells,samples,cycles,cr,sr,nominal_initial = public_normalized(case)
        else:
            s=case['source']; nx=s['nx']; nu=s['nu']; cycles=[c['cycles'] for c in s['cells']]
            cells=[dict(A=c['A'],B=c['B'],d=c['defect']) for c in s['cells']]
            samples=[dict(cell=p['cell'],cycle=p['cycle'],half=p['half'],A=p['A'],B=p['B'],d=p['defect']) for p in s['samples']]
            cr=[]; sr=[]; nominal_initial=None
        ref=helper.lifted_reference(nx,nu,case['actual_initial'],cells,samples)
        recursive=helper.recurrence_reference(nx,nu,case['actual_initial'],cells,samples)
        check(recursive['state_offsets'].tolist(),ref['state_offsets'],'independent reference recurrence offset')
        check(recursive['state_control_maps'].tolist(),ref['state_control_maps'],'independent reference recurrence M')
        check(recursive['state_initial_maps'].tolist(),ref['state_initial_maps'],'independent reference recurrence P')
        terms=[]; dy=ref['embedding_offset'].size; du=ref['embedding_map'].shape[1]
        for term in case['terms']:
            rows=len(term['F']); F=array(term['F'],(rows,dy)).copy(); f0=array(term['f0'],(rows,)).copy(); linear=array(term['linear'],(dy,))
            for addition in term['sample_additions']:
                sample=ref['samples'][addition['sample_index']]; coef=array(addition['coefficient'],(rows,nx))
                F=F+coef@sample['lifted_map']; f0=f0+coef@sample['lifted_offset']
            q=helper.substitute_objective(F,f0,linear,term['constant'],ref['embedding_offset'],ref['embedding_map'])
            q.update(name=term['name'],units=term['units']); terms.append(q)
        total=dict(name='sum',units='declared_terms',full_factor=np.zeros((0,dy)),full_offset=np.zeros(0),full_linear=np.zeros(dy),
                   full_constant=0.,factor=np.zeros((0,du)),offset=np.zeros(0),H=np.zeros((du,du)),g=np.zeros(du),constant=0.)
        for term in terms:
            for key in ('full_factor','factor'): total[key]=np.vstack((total[key],term[key]))
            for key in ('full_offset','offset'): total[key]=np.r_[total[key],term[key]]
            for key in ('full_linear','full_constant','H','g','constant'): total[key]=total[key]+term[key]
        return dict(ref=ref,terms=terms,total=total,nx=nx,nu=nu,cycles=cycles,source_cell_residuals=cr,
                    source_sample_residuals=sr,nominal_initial=nominal_initial,sample_descriptors=samples)

    for case, exp in zip(cases,expected['cases']):
        if exp['success']:
            cache[case['name']] = reference(case)
    write(out/'PRE_EXECUTION_DECLARATION.json',dict(scope=__doc__,input_sha256=args.input_sha,policy_sha256=args.policy_sha,
        binary_sha256=args.binary_sha,helper_sha256=HELPER_SHA,output_abs=ABS,output_rel=REL,
        source_abs=2e-13,source_rel=2e-13,helper_symmetry_abs=1e-12,schema_sha256=args.schema_sha,
        native_bridge_scope='archived Result carrier normalization only; no real Model call',
        expected_roster=expected['cases'],retained_FD_gate='FAIL_RETAINED_IMMUTABLE',kernel_calls=1))
    dest=out/'kernel_once.json'
    process=subprocess.run([str(args.binary),'--policy',str(policy_path),str(inputs_path),str(dest)],capture_output=True,text=True)
    (out/'kernel_once.stdout').write_text(process.stdout); (out/'kernel_once.stderr').write_text(process.stderr)
    (out/'kernel_once.exit').write_text(str(process.returncode)+'\n'); need(process.returncode == 0,'one kernel process success')
    result=load(dest)

    def validate(output):
        finite_tree(output); need(type(output['schema_version']) is int and output['schema_version'] == 1,'output schema')
        meta=output['metadata']; scope(meta['scope']); need(meta['namespace'] == 'phase5_public_affine_horizon' and
             meta['policy_sha256'] == args.policy_sha and meta['limits'] == LIMITS,'exact kernel metadata')
        need(all(type(meta['limits'][key]) is type(value) for key,value in LIMITS.items()),'typed integer/arithmetic metadata')
        need(len(output['cases']) == len(cases) and [r['name'] for r in output['cases']] == [c['name'] for c in cases],'complete ordered output roster')
        summary=[]
        for case,exp,got in zip(cases,expected['cases'],output['cases']):
            scope(got['scope']); need(type(got['success']) is bool and got['success'] == exp['success'],'expected typed outcome')
            if not exp['success']:
                need(type(got.get('error')) is str and got['error'] and type(got.get('refusal_code')) is str and got['refusal_code'],'explicit refusal reason/code')
                need(all(k not in got for k in ('assembly','objective','evaluation','native_bridge')),'no partial/fabricated failure matrices/proof')
                if case['source']['kind'] == 'public_saved_json':
                    original=originals[case['source']['row_name']]['original_output']; diagnostic=got['source_diagnostic']
                    need(got['refusal_code'] == 'SOURCE_INCOMPLETE_OR_UNSUPPORTED' and diagnostic == original,
                         'authentic refused original full flags/value/prefix/error preserved without wrapper')
                else:
                    need(got['refusal_code'] == 'INVALID_SOURCE_SHAPE_OR_RESOURCE' and got['source_diagnostic'] == {},
                         'locked generic refusal code/empty source diagnostic')
                summary.append(dict(name=case['name'],success=False,refusal_code=got['refusal_code'])); continue
            need(got['error'] == '','success without stale error'); record=cache[case['name']]; r=record['ref']; nx=record['nx']; nu=record['nu']; N=len(record['cycles']); du=nu*N; dx=nx*(N+1); dy=dx+du
            source_identity=got['source']; need(source_identity['kind'] == case['source']['kind'],'source kind')
            need(type(source_identity['full_nominal_source_certified']) is bool and type(source_identity['actual_initial_shifted']) is bool,'typed source flags')
            if record['nominal_initial'] is not None:
                need(source_identity['artifact_id'] == 'root_archived_sources' and source_identity['file_sha256'] == BUNDLE_SHA and
                     source_identity['row_name'] == case['source']['row_name'] and source_identity['source_binary_sha256'] == F1_SHA and
                     source_identity['certificate_name'] == CERT and source_identity['full_nominal_source_certified'] is True and
                     source_identity['actual_initial_shifted'] == bool(np.any(np.asarray(case['actual_initial']) != record['nominal_initial'])),'full public original identity/initial shift')
            else:
                need(source_identity['certificate_name'] == '' and source_identity['file_sha256'] == '' and
                     source_identity['full_nominal_source_certified'] is False and source_identity['actual_initial_shifted'] is False,'generic no physical certificate')
            bridge=got['native_bridge']
            bridge_bools=('used_native_normalization','matched_json_cumulative_fields','multicycle_local_cumulative_distinct')
            need(set(bridge) == set(bridge_bools+('source_file_sha256','source_binary_sha256','cell_count','sample_count')),'exact bridge proof field roster')
            need(all(type(bridge[k]) is bool for k in bridge_bools) and
                 all(type(bridge[k]) is str for k in ('source_file_sha256','source_binary_sha256')) and
                 all(type(bridge[k]) is int for k in ('cell_count','sample_count')),'typed native bridge proof')
            if record['nominal_initial'] is not None:
                need(bridge['used_native_normalization'] is True and bridge['matched_json_cumulative_fields'] is True and
                     bridge['multicycle_local_cumulative_distinct'] == any(n > 1 for n in record['cycles']) and
                     bridge['source_file_sha256'] == BUNDLE_SHA and bridge['source_binary_sha256'] == F1_SHA and
                     bridge['cell_count'] == N and bridge['sample_count'] == len(r['samples']),
                     'actual archived-carrier native normalization/cumulative distinction proof')
            else:
                need(all(bridge[k] is False for k in bridge_bools) and bridge['source_file_sha256'] == '' and
                     bridge['source_binary_sha256'] == '' and bridge['cell_count'] == bridge['sample_count'] == 0,
                     'generic has no native public bridge proof')
            assembly=got['assembly']; need(all(type(assembly[k]) is int for k in ('nx','nu','N')) and
                 (assembly['nx'],assembly['nu'],assembly['N']) == (nx,nu,N) and assembly['cycles'] == record['cycles'] and
                 all(type(x) is int for x in assembly['cycles']),'typed assembly dimensions/mesh')
            need(len(assembly['recursive_states']) == N+1,'all recursive state views')
            for i,state in enumerate(assembly['recursive_states']):
                for key,expected_value in (('offset',r['state_offsets'][i]),('control',r['state_control_maps'][i]),('initial',r['state_initial_maps'][i])):
                    check(state[key],expected_value,'state '+key)
            lift=assembly['lifted']
            fields=dict(L=r['L'],E=r['E'],f=r['f'],initial_selector=r['initial_injection'],X_control=r['state_control_maps'].reshape(dx,du),
                        X_offset=r['state_offsets'].ravel(),X_initial=r['state_initial_maps'].reshape(dx,nx),T=r['embedding_map'],t=r['embedding_offset'])
            for key,val in fields.items(): check(lift[key],val,'independent pivoted lifted '+key)
            check(assembly['nominal_cell_defect_residual_max'],record['source_cell_residuals'],'source cell residual reports')
            check(assembly['nominal_sample_defect_residual_max'],record['source_sample_residuals'],'source sample residual reports')
            need(len(assembly['samples']) == len(r['samples']),'all sample views')
            for got_sample, rs, descriptor in zip(assembly['samples'],r['samples'],record['sample_descriptors']):
                need(all(type(got_sample[k]) is int for k in ('cell','cycle','half')) and
                     all(got_sample[k] == descriptor[k] for k in ('cell','cycle','half')),'exact sample roster/timing')
                check(got_sample['lifted_factor'],rs['lifted_map'],'actual sample lifted expression'); check(got_sample['lifted_offset'],rs['lifted_offset'],'sample defect')
                # Independent initial projection through lifted state block.
                eliminated_P=rs['lifted_map'][:,:dx]@r['state_initial_maps'].reshape(dx,nx)
                check(eliminated_P.tolist(),rs['initial_map'],'sample initial propagation vs lifted selector')
                for view in ('recursive','eliminated'):
                    for key,refkey in (('offset','offset'),('control','control_map'),('initial','initial_map')):
                        check(got_sample[view][key],rs[refkey],'sample '+view+' '+key)
            objective=got['objective']; evaluation=got['evaluation']; check(evaluation['controls'],case['evaluate_controls'],'exact evaluation controls')
            need(len(objective['terms']) == len(evaluation['terms']) == len(record['terms']),'all objective/evaluation terms')
            pairs=list(zip(objective['terms'],evaluation['terms'],record['terms']))+[(objective['sum'],evaluation['sum'],record['total'])]
            U=array(case['evaluate_controls'],(du,)); y=r['embedding_offset']+r['embedding_map']@U
            for term,ev,q in pairs:
                need(term['name'] == q['name'] and term['units'] == q['units'] and ev['name'] == q['name'],'ordered term identity')
                for key,refkey in (('used_F','full_factor'),('used_f0','full_offset'),('used_linear','full_linear'),('used_constant','full_constant'),
                                   ('factor','factor'),('offset','offset'),('H','H'),('g','g'),('constant','constant')):
                    check(term[key],q[refkey],'complete objective '+key)
                direct=helper.direct_objective(q['full_factor'],q['full_offset'],q['full_linear'],q['full_constant'],y)
                quad=helper.quadratic_objective(q['H'],q['g'],q['constant'],U)
                check(ev['lifted_value'],direct['value'],'literal full objective'); check(ev['condensed_value'],quad['value'],'literal quadratic objective')
                check(ev['lifted_chain_gradient'],r['embedding_map'].T@direct['gradient'],'full objective chain gradient')
                raw_H=array(term['H'],(du,du)); raw_g=array(term['g'],(du,)); Hs=.5*(raw_H+raw_H.T)
                check(ev['condensed_gradient'],Hs@U+raw_g,'literal serialized H gradient'); check(ev['condensed_hessian'],Hs,'literal serialized H Hessian')
                full_H=r['embedding_map'].T@q['full_factor'].T@q['full_factor']@r['embedding_map']
                check(ev['lifted_chain_hessian'],full_H,'independent factor chain Hessian')
                check(ev['condensed_gradient'],quad['gradient'],'independent condensed gradient')
                check(ev['condensed_hessian'],full_H,'Hessian alternate FP path')
                check(ev['condensed_value'],direct['value'],'full/condensed value equivalence')
            summary.append(dict(name=case['name'],success=True,samples=len(r['samples']),terms=len(record['terms'])))
        return summary

    summary=validate(result)
    mutation_records=[]
    def altered(name, change):
        trial=copy.deepcopy(result); change(trial)
        try:
            validate(trial)
        except (AssertionError,ValueError,TypeError,KeyError) as error:
            mutation_records.append(dict(name=name,rejected=True,error=str(error))); return
        raise AssertionError('altered output falsely accepted '+name)
    def case_output(data,name): return next(c for c in data['cases'] if c['name'] == name)
    n4='root_affine_public_nonuniform_shifted'; generic='root_affine_generic_nonsymmetric'
    original=complete['root_trial_nonuniform_finite_state_controls']['original_output']
    last=next(m for m in original['cycle_maps'] if m['cell'] == 3 and m['cycle'] == 4)
    def last_cycle(data):
        L=case_output(data,n4)['assembly']['lifted']['L']
        for i in range(30): L[120+i][90:120]=[-v for v in last['A'][i]]
    altered('last_cycle_local_not_wholecell',last_cycle)
    def tied(data):
        M=case_output(data,n4)['assembly']['lifted']['X_control']
        for row in M: row[8:16]=row[:8]
    altered('tied_distinct_cell_controls',tied)
    altered('nominal_future_reset',lambda d:case_output(d,n4)['assembly']['recursive_states'][2].update(offset=packed(original['value']['cell_end_states'][1]).tolist()))
    altered('missing_initial_P',lambda d:case_output(d,n4)['assembly']['recursive_states'][0]['initial'][0].__setitem__(0,0.))
    altered('missing_sample_P',lambda d:case_output(d,n4)['assembly']['samples'][0]['eliminated']['initial'][0].__setitem__(0,0.))
    altered('half_square_factor_error',lambda d:case_output(d,generic)['objective']['terms'][1]['H'][0].__setitem__(0,.045))
    altered('missing_control_cross',lambda d:case_output(d,generic)['objective']['terms'][1]['H'][0].__setitem__(1,0.))
    def progress(d):
        term=next(t for t in case_output(d,n4)['objective']['terms'] if t['name'] == 'root_nonzero_progress_linear')
        term['g']=[0.]*32
    altered('missing_nonzero_progress_linear',progress)
    def constant(d):
        term=next(t for t in case_output(d,n4)['objective']['terms'] if t['name'] == 'root_nonzero_progress_linear')
        term['used_constant']=0.
    altered('missing_explicit_constant',constant)
    def condensed_constant(d):
        term=next(t for t in case_output(d,n4)['objective']['terms'] if t['name'] == 'root_nonzero_progress_linear')
        term['constant']=0.
    altered('missing_condensed_constant',condensed_constant)
    altered('missing_sample_addition',lambda d:case_output(d,n4)['objective']['terms'][1]['used_F'][0].__setitem__(0,999.))
    altered('missing_tail',lambda d:case_output(d,n4)['assembly']['samples'].pop())
    altered('fabricated_extra_case',lambda d:d['cases'].append(copy.deepcopy(d['cases'][0])))
    altered('false_scope',lambda d:case_output(d,n4)['scope'].__setitem__('execution',True))
    altered('missing_scope',lambda d:case_output(d,n4)['scope'].pop('ball'))
    altered('bad_shape',lambda d:case_output(d,n4)['assembly']['lifted']['X_initial'].pop())
    altered('boolean_matrix_entry',lambda d:case_output(d,n4)['assembly']['lifted']['L'][0].__setitem__(0,True))
    altered('nonfinite_matrix_entry',lambda d:case_output(d,n4)['assembly']['lifted']['L'][0].__setitem__(0,float('nan')))
    altered('failed_packet_fake_assembly',lambda d:next(c for c in d['cases'] if not c['success']).__setitem__('assembly',{}))
    altered('missing_native_normalization_proof',lambda d:case_output(d,n4)['native_bridge'].__setitem__('used_native_normalization',False))
    altered('missing_multicycle_native_distinction',lambda d:case_output(d,n4)['native_bridge'].__setitem__('multicycle_local_cumulative_distinct',False))
    altered('wrong_native_source_hash',lambda d:case_output(d,n4)['native_bridge'].__setitem__('source_file_sha256',''))
    altered('generic_false_native_claim',lambda d:case_output(d,generic)['native_bridge'].__setitem__('used_native_normalization',True))
    write(out/'OUTPUT_MUTATION_CONTROLS.json',mutation_records)
    for path, old in startup.items(): need(sha(path) == old,'frozen execution identity unchanged '+path)
    report=dict(decision='PASS_PREDECLARED_AFFINE_KERNEL_CLI_ALGEBRA',cases=summary,mutation_controls=mutation_records,
        source_sha256=startup[str(source)],helper_sha256=HELPER_SHA,binary_sha256=args.binary_sha,freeze_sha256=args.freeze_sha,
        input_sha256=args.input_sha,policy_sha256=args.policy_sha,output_abs=ABS,output_rel=REL,kernel_calls=1,
        schema_sha256=args.schema_sha,original_model_calls=0,native_bridge_validated=True,
        native_bridge_public_success_cases=sum(c['success'] and c['name'] != generic for c in summary),
        native_bridge_scope='archived Result carrier normalization only; no real Model constructor/forward call',
        refusal_codes_static_freeze='SOURCE_INCOMPLETE_OR_UNSUPPORTED; INVALID_SOURCE_SHAPE_OR_RESOURCE',retained_FD_gate='FAIL_RETAINED_IMMUTABLE',
        phase5='NOT_ACCEPTED',scope=__doc__)
    write(out/'audit.json',report)
    write(out/'READY.json',dict(files={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in out.iterdir() if p.is_file()},scope=__doc__))


if __name__ == '__main__':
    main()
