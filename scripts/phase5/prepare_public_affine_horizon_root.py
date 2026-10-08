#!/usr/bin/env python3
"""Source-only prepared definition of a bounded independent affine batch.

When separately authorized, this stdlib-only script copies immutable recorded
sources and constructs algebra coefficients, never evaluates a model or matrix.
Preparation does not reverse the retained finite-step FD failure or establish
admissibility/physical/controller/Phase5 acceptance.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

BUNDLE_SHA = 'ce5731c49d4c4815d2e30d8079054310d1f73816d7906c607a1e76a4cf0c0a0c'
PLAN_SHA = '514bcc31b1bce001853c61e714b53802f2515a831762338baf0619f41bdc6518'
ARCHIVE_SHA = 'e42af2a0ca5a85047e371660f9fc565cdc0a28ace450235a1f3d6acb13d9de83'
F1_SHA = 'f1b7e6c7e4219fec2beb310540c725b448dcf021b3a95ddafc2922e8849bf1d6'
CERT = 'COMMAND_PROGRESS_EXTENSION_JACOBIAN_STRICT_PHYSICAL_V1'
CLAIMS = ('connecting_segment', 'ball', 'admissibility', 'execution', 'safety',
          'uniform_error_bound', 'controller_readiness')
LIMITS = dict(max_cases=32, max_cells=16, max_samples=512, max_nx=64, max_nu=16,
              max_terms=32, max_factor_rows=256, max_matrix_elements=2000000,
              max_document_bytes=67108864, max_problem_numeric_elements=8000000,
              max_cli_numeric_elements=16000000, arithmetic_abs=2e-13, arithmetic_rel=2e-13)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def packed(z):
    return z['q']+z['v']+z['C']+z['w']+[z['s'], z['r']]


def scope():
    return dict.fromkeys(CLAIMS, False)


def full_term(nx, nu, count):
    dy = nx*(count+1)+nu*count
    return dict(name='root_dense_crosscomponent_crosscell', units='declared_algebra',
                F=[[(((3*i+5*j+2*i*j) % 17)-8)/100 for j in range(dy)] for i in range(19)],
                f0=[.003*(-1)**i*(i+1) for i in range(19)],
                linear=[.001*(-1)**j/(j+1) for j in range(dy)], constant=.17, sample_additions=[])


def sample_term(nx, nu, count, sample_count):
    dy = nx*(count+1)+nu*count
    additions = [dict(sample_index=index,
        coefficient=[[(((i+1)*(j+3)+index) % 11-5)*.002 for j in range(nx)] for i in range(19)])
        for index in (0, sample_count-1)]
    return dict(name='root_explicit_sample_additions', units='declared_algebra',
                F=[[0.]*dy for _ in range(19)], f0=[.004*(-1)**i*(i+1) for i in range(19)],
                linear=[.0007*(-1)**j/(j+2) for j in range(dy)], constant=-.11,
                sample_additions=additions)


def progress_term(count):
    """Explicit nonzero progress coefficients for targeted omission controls."""
    dy = 30*(count+1)+8*count; linear = [0.]*dy
    for c in range(count+1):
        linear[30*c+28] = .17+.01*c; linear[30*c+29] = -.23-.01*c
    for c in range(count):
        linear[30*(count+1)+8*c+7] = .31+.02*c
    return dict(name='root_nonzero_progress_linear', units='declared_algebra',
                F=[[0.]*dy], f0=[.03], linear=linear, constant=.27, sample_additions=[])


def public_case(name, row, shifted=False, empty=False):
    inp = row['original_input']; count = len(inp['cells']); initial = packed(inp['state'])
    if shifted:
        for index, delta in ((0,2e-4),(9,-3e-5),(18,-1e-5),(24,2e-5),(28,4e-5),(29,-2e-6)):
            initial[index] += delta
    controls = [1e-4*(-1)**(c+j)*(c+1)*(j+1) if j < 7 else .002*(c+1)
                for c in range(count) for j in range(8)]
    terms = [] if empty else [full_term(30,8,count), sample_term(30,8,count,2*sum(c['cycles'] for c in inp['cells']))]
    if shifted:
        terms.append(progress_term(count))
    return dict(name=name, source=dict(kind='public_saved_json', artifact_id='root_archived_sources',
                roster='complete', row_name=row['name']), actual_initial=initial,
                terms=terms, evaluate_controls=controls, scope=scope())


def synthetic(plan):
    spec = plan['generic_synthetic']; nx, nu = spec['nx'], spec['nu']
    cycles = (1,3,2); cells = []; samples = []
    for c in range(3):
        A, B, d = spec['A'][c], spec['B'][c], spec['defect'][c]
        cells.append(dict(cycles=cycles[c], A=A, B=B, defect=d))
        samples.append(dict(cell=c, cycle=1, half=1,
            A=[[.7*A[i][j]+(.1 if i == j else 0) for j in range(nx)] for i in range(nx)],
            B=[[.6*v for v in row] for row in B], defect=[.2*v for v in d]))
        samples.append(dict(cell=c, cycle=cycles[c], half=2, A=A, B=B, defect=d))
    cross = [0.]*(nx*4+nu*3); cross[nx*4] = .3; cross[nx*4+1] = -.4
    cross_term = dict(name='root_explicit_control_cross', units='declared_algebra',
                      F=[cross], f0=[.021], linear=[0.]*len(cross), constant=-.02, sample_additions=[])
    return dict(name='root_affine_generic_nonsymmetric',
                source=dict(kind='generic_synthetic', nx=nx, nu=nu, cells=cells, samples=samples),
                actual_initial=spec['actual_initial'], terms=[full_term(nx,nu,3),cross_term],
                evaluate_controls=[.013,-.007,-.009,.021,.006,-.014], scope=scope())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('output','archived-sources','plan','schema'):
        parser.add_argument('--'+key, required=True, type=Path)
    parser.add_argument('--schema-sha', required=True)
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    src = Path(__file__); source_bytes = src.read_bytes()
    saved = {args.archived_sources: args.archived_sources.read_bytes(), args.plan: args.plan.read_bytes(),
             args.schema: args.schema.read_bytes()}
    for path, expected in ((args.archived_sources,BUNDLE_SHA),(args.plan,PLAN_SHA),(args.schema,args.schema_sha)):
        if digest(saved[path]) != expected:
            raise ValueError('immutable preparation identity '+str(path))
    (out/'SOURCE_SNAPSHOT.py').write_bytes(source_bytes)
    (out/'archived_sources.json').write_bytes(saved[args.archived_sources])
    (out/'ROOT_PLAN.json').write_bytes(saved[args.plan]); (out/'INTERFACE_SCHEMA.md').write_bytes(saved[args.schema])
    bundle = json.loads(saved[args.archived_sources]); plan = json.loads(saved[args.plan])
    complete = {row['name']:row for row in bundle['complete']}; refused = {row['name']:row for row in bundle['refused']}
    if len(complete) != 2 or len(refused) != 2:
        raise ValueError('exact original source roster')
    cases = [public_case('root_affine_public_startup',complete['root_trial_identity_start']),
             public_case('root_affine_public_nonuniform_shifted',complete['root_trial_nonuniform_finite_state_controls'],True),
             synthetic(plan), public_case('root_affine_public_empty_terms',complete['root_trial_identity_start'],empty=True)]
    positive = [case['name'] for case in cases]
    for name in ('future_nominal_original_prefix','initial_C_boundary_both'):
        row = refused[name]
        cases.append(dict(name='root_refuse_'+name, source=dict(kind='public_saved_json',artifact_id='root_archived_sources',
            roster='refused',row_name=name), actual_initial=packed(row['original_input']['state']), terms=[],
            evaluate_controls=[0.]*(8*len(row['original_input']['cells'])), scope=scope()))
    base = cases[2]
    def malformed(name):
        case = copy.deepcopy(base); case['name'] = name; cases.append(case); return case
    malformed('root_refuse_initial_shape')['actual_initial'].pop()
    malformed('root_refuse_boolean_scalar')['terms'][0]['F'][0][0] = True
    malformed('root_refuse_true_scope')['scope']['execution'] = True
    del malformed('root_refuse_missing_scope')['scope']['ball']
    malformed('root_refuse_noninteger_mesh')['source']['cells'][0]['cycles'] = 1.5
    # F finite, with coefficient on a literal control column; F*T is >=1e308
    # in that entry, so its squared condensed Hessian must overflow/refuse.
    malformed('root_refuse_derived_H_overflow')['terms'][0]['F'][0][12] = 1e308
    expectations = [dict(name=case['name'],success=case['name'] in positive) for case in cases]
    policy = dict(schema_version=1,limits=LIMITS,scope=scope(),artifacts=[dict(id='root_archived_sources',
        path=str(out/'archived_sources.json'),sha256=BUNDLE_SHA,source_binary_sha256=F1_SHA,
        certificate_name=CERT,archive_sha256=ARCHIVE_SHA)])
    write(out/'policy.json',policy); write(out/'inputs.json',dict(schema_version=1,cases=cases))
    write(out/'expected.json',dict(cases=expectations,output_abs=1e-11,output_rel=1e-10,
        source_arithmetic_abs=2e-13,source_arithmetic_rel=2e-13,helper_symmetry_abs=1e-12,
        schema_sha256=args.schema_sha,
        native_bridge='Successful public CLI cases must exercise archived Result carrier normalization; no Model constructor/forward call',
        refusal_codes=dict(authentic_public='SOURCE_INCOMPLETE_OR_UNSUPPORTED',other='INVALID_SOURCE_SHAPE_OR_RESOURCE'),
        retained_FD_gate='FAIL_RETAINED_IMMUTABLE',scope=__doc__))
    for path, data in saved.items():
        if path.read_bytes() != data:
            raise ValueError('preparation source changed '+str(path))
    if src.read_bytes() != source_bytes:
        raise ValueError('preparation generator source changed')
    write(out/'READY.json',dict(files={p.name:dict(sha256=digest(p.read_bytes()),bytes=p.stat().st_size)
          for p in out.iterdir() if p.is_file()},scope=__doc__))


if __name__ == '__main__':
    main()
