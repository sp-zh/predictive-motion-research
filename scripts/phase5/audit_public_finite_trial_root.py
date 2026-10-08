#!/usr/bin/env python3
"""Independent fixed-roster finite-trial diagnostic audit, never a plant gate.

References are frozen original closed2fa self-rollouts, f1 nominal maps and
e2c point certificates. No producer verifier/diagnostic reconstruction import.
GLOBAL affine deviations never reset to actual trial cell origins. Separately
named LOCAL residuals verify the exact arithmetic relation to GLOBAL residuals.
Only syntax compilation is authorized at preparation; running requires the
root's frozen-input forecast authorization. No residual performance threshold.
"""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np

VALUE_SHA = '2fa952127cdd37ceb56396231e2972d50d36c94e9a19c341c9c17169442acf57'
EXTENSION_SHA = 'f1b7e6c7e4219fec2beb310540c725b448dcf021b3a95ddafc2922e8849bf1d6'
PHYSICAL_SHA = 'e2c75c09001ba354ca5371cbfc594a9765c62098d4cdb52e6a1442adc055c6a4'
PREDECLARED_SHA = '008af2b68152f7e611ed107a2d7a80b0d596ef752da082bdbd6db616733ea672'
CONSTANTS_SHA = 'd37c9a12539345fd1dbb6718cd273584140359ca2bd9834442bf2228e50f6bdd'
CLAIMS = ('certifies_connecting_segment', 'certifies_perturbation_ball',
          'certifies_admissibility', 'certifies_execution', 'certifies_safety',
          'certifies_uniform_error_bound', 'certifies_controller_readiness')
BLOCKS = (('q', 0, 7, 'rad'), ('v', 7, 7, 'rad/s'), ('C', 14, 7, 'rad'),
          ('w', 21, 7, 'rad/s'), ('s', 28, 1, 'dimensionless'), ('r', 29, 1, '1/s'))
BATCH = 96


def need(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def finite_tree(value):
    if type(value) in (int, float):
        need(math.isfinite(value), 'nonfinite JSON number')
    elif type(value) is dict:
        for item in value.values():
            finite_tree(item)
    elif type(value) is list:
        for item in value:
            finite_tree(item)


def array(value, shape):
    def numeric(item):
        if type(item) is list:
            return all(numeric(x) for x in item)
        return type(item) in (int, float) and math.isfinite(item)
    need(type(value) is list and numeric(value), 'typed finite array')
    result = np.asarray(value, dtype=float)
    need(result.shape == shape, 'array shape ' + str(shape))
    return result


def close(actual, expected, label, tolerance=1e-12):
    a, b = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
    need(a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all(), label + ' finite/shape')
    need(float(np.max(np.abs(a-b), initial=0.)) <= tolerance, label)


def pack(state):
    parts = [array(state[key], (7,)) for key in ('q', 'v', 'C', 'w')]
    need(all(type(state[k]) in (int, float) and math.isfinite(state[k]) for k in ('s', 'r')), 'typed progress')
    return np.r_[*parts, state['s'], state['r']]


def point(row):
    return dict(q=row['q'], v=row['v'], C=row['C'], w=row['w'],
                s=row['s_reference'], r=row['r_reference'])


def flags(node):
    for key in CLAIMS:
        need(node.get(key) is False, 'false scope claim ' + key)


def boolean(node, key, expected):
    need(type(node[key]) is bool and node[key] == expected, 'typed bool ' + key)


def timing(row):
    need(all(type(row[k]) is int for k in ('cell', 'cycle', 'half')), 'typed timing')
    return row['cell'], row['cycle'], row['half']


def topology(side):
    return tuple(cell['cycles'] for cell in side['cells'])


def check_value(value, side):
    need(type(value['success']) is bool and type(value['has_final_state']) is bool, 'typed forward flags')
    expected = [(c, k, half) for c, cell in enumerate(side['cells'])
                for k in range(1, cell['cycles']+1) for half in (1, 2)]
    rows = value['substeps']
    need(type(rows) is list and len(rows) <= len(expected), 'bounded actual trace')
    for i, row in enumerate(rows):
        need(timing(row) == expected[i], 'actual trace exact prefix/order')
        close(row['elapsed_s'], .002*(i+1), 'actual 2ms timestamp')
        pack(point(row))
    cycles = value['cycle_end_states']; cells = value['cell_end_states']
    need(len(cycles) <= len(rows)//2 and len(cells) <= len(side['cells']), 'bounded endpoint prefix')
    for state in cycles + cells:
        pack(state)
    if value['has_final_state']:
        pack(value['final_state'])
    if value['success']:
        need(value['has_final_state'] and len(rows) == len(expected), 'no complete flag with missing tail')
        need(len(cycles) == sum(topology(side)) and len(cells) == len(side['cells']), 'complete endpoints')
        need(value['final_state'] == cells[-1], 'literal complete final state')
    else:
        need(type(value.get('error')) is str and value['error'], 'explicit forward failure')


def signature(reference):
    """Use frozen e2c's actual point output; do not recreate its clamp math."""
    need(type(reference['value_success']) is bool and type(reference['jacobian_success']) is bool,
         'typed original point certificate flags')
    d = reference['diagnostics']
    boolean(d, 'complete', reference['jacobian_success'])
    roster = []
    for key in ('control', 'actuator', 'joint_force'):
        clips = d[key]
        need(type(clips) is list and len(clips) == 7, 'full per-joint clip signature')
        sides = []
        for clip in clips:
            need(type(clip['enabled']) is bool and type(clip['side']) is int and clip['side'] in (-1, 0, 1), 'typed clip side')
            need(all(type(clip[k]) in (int, float) and math.isfinite(clip[k])
                     for k in ('input', 'output', 'lower', 'upper', 'margin', 'slope')), 'finite full clip record')
            sides.append((clip['enabled'], clip['side']))
        roster.append(sides)
    box = reference['value']['friction']; array(box['force'], (7,))
    need(type(box['iterations']) is int and box['iterations'] > 0, 'typed box iterations')
    need(type(box['original_KKT']) in (int, float) and 0 <= box['original_KKT'] <= 1e-10,
         'original KKT retained')
    friction = box['branches']
    need(type(friction) is list and len(friction) == 7 and
         all(type(x) is int and x in (-1, 0, 1, 2) for x in friction), 'exact friction labels')
    return roster + [friction]


def checked_maps(extension, side):
    """Check all saved nominal maps, including available failed prefixes."""
    value = extension['value']; check_value(value, side)
    need(type(extension['extension_jacobian_success']) is bool, 'typed extension flag')
    need(extension['certifies_two_sided_admissible_neighborhood'] is False, 'extension scope')
    rows = value['substeps']; sm = extension['substep_maps']
    need(len(sm) <= len(rows), 'no fabricated nominal substep map')
    origins = [side['state']] + value['cell_end_states']
    for i, m in enumerate(sm):
        need(timing(m) == timing(rows[i]), 'certified map exact actual prefix')
        need(m['certificate_name'] == 'COMMAND_PROGRESS_EXTENSION_JACOBIAN_STRICT_PHYSICAL_V1' and
             m['certifies_two_sided_admissible_neighborhood'] is False, 'prefix extension certificate')
        c = m['cell']; u = np.r_[array(side['cells'][c]['alpha'], (7,)), side['cells'][c]['b']]
        need(c < len(origins), 'available nominal cell origin')
        close(pack(m['state']), pack(point(rows[i])), 'map actual endpoint', 0.)
        close(pack(m['cell_origin']), pack(origins[c]), 'map actual cell origin', 0.)
        close(array(m['input'], (8,)), u, 'map held input', 0.)
        A, B = array(m['A'], (30, 30)), array(m['B'], (30, 8))
        CA, CB = array(m['cell_A'], (30, 30)), array(m['cell_B'], (30, 8))
        close(array(m['defect'], (30,)), pack(m['state'])-A@pack(m['origin'])-B@u, 'local map defect')
        close(array(m['cell_defect'], (30,)), pack(m['state'])-CA@pack(m['cell_origin'])-CB@u, 'prefix defect')
    for kind, endpoints in (('cycle_maps', value['cycle_end_states']), ('cell_maps', value['cell_end_states'])):
        need(len(extension[kind]) <= len(endpoints), 'bounded nominal endpoint maps')
        for i, m in enumerate(extension[kind]):
            close(pack(m['state']), pack(endpoints[i]), 'certified endpoint state', 0.)
            array(m['A'], (30, 30)); array(m['B'], (30, 8)); array(m['defect'], (30,))
            if kind == 'cycle_maps':
                array(m['cell_A'], (30, 30)); array(m['cell_B'], (30, 8)); array(m['cell_defect'], (30,))
    if extension['extension_jacobian_success']:
        need(value['success'] and len(sm) == len(rows) and
             len(extension['cycle_maps']) == len(value['cycle_end_states']) and
             len(extension['cell_maps']) == len(value['cell_end_states']), 'full certificate no missing tail')
        need(extension['first_uncertified_substep'] == -1, 'complete certificate index')
    else:
        need(extension['first_uncertified_substep'] == len(sm) and 'certificate_name' not in extension,
             'partial certificate exact prefix index/no full claim')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('output', 'binary', 'freeze', 'predeclared'):
        parser.add_argument('--'+key, required=True, type=Path)
    for key in ('binary-sha', 'freeze-sha'):
        parser.add_argument('--'+key, required=True)
    args = parser.parse_args(); out = args.output; out.mkdir(parents=True, exist_ok=False)
    source = Path(__file__); source_bytes = source.read_bytes()
    (out/'SOURCE_SNAPSHOT.py').write_bytes(source_bytes)
    predeclared = args.predeclared.read_bytes(); freeze_bytes = args.freeze.read_bytes()
    need(hashlib.sha256(predeclared).hexdigest() == PREDECLARED_SHA, 'fixed 13-pair predeclaration')
    need(hashlib.sha256(freeze_bytes).hexdigest() == args.freeze_sha, 'freeze identity')
    (out/'PREDECLARED.json').write_bytes(predeclared); (out/'FROZEN_INPUTS.json').write_bytes(freeze_bytes)
    pairs = json.loads(predeclared)['cases']; need(len(pairs) == 13 and len({p['name'] for p in pairs}) == 13, 'exact unique 13 pairs')
    root = Path('/home/codextransfer/predictive_motion')
    value = root/'build-public-coupled-augmented-cpp-v1/public_coupled_augmented_probe'
    extension = root/'build-public-coupled-augmented-extension-cpp-v1/public_coupled_augmented_extension_probe'
    physical = root/'build-public-coupled-derivative-cpp-v1/public_coupled_derivative_probe'
    xml = root/'experiments/generated/inspection/inspection_fr3.xml'
    constants = root/'results/phase5/development/public-coupled-servo-v1-training/public_constants.json'
    for path, expected in ((value, VALUE_SHA), (extension, EXTENSION_SHA), (physical, PHYSICAL_SHA),
                           (args.binary, args.binary_sha), (constants, CONSTANTS_SHA)):
        need(sha(path) == expected, 'pinned identity '+str(path))
    frozen = {x['path']: x for x in json.loads(freeze_bytes)['files']}
    owned = [value, extension, physical, args.binary, xml, constants]
    for directory in ('phase5_public_coupled_cpp_v2', 'phase5_public_coupled_augmented_cpp',
                      'phase5_public_coupled_derivative_cpp', 'phase5_public_coupled_augmented_extension_cpp',
                      'phase5_public_coupled_finite_trial_cpp'):
        owned += [p for p in (root/'tools'/directory).glob('*') if p.is_file()]
    need((root/'tools/phase5_public_coupled_finite_trial_cpp').is_dir(), 'owned producer source directory')
    for path in owned:
        need(str(path) in frozen and sha(path) == frozen[str(path)]['sha256'], 'frozen owned input '+str(path))
    dump(out/'PRE_FORECAST_DECLARATION.json', dict(pairs=pairs, scope=__doc__,
         numerical_identity_tolerance=1e-12, residual_performance_threshold=None,
         roster='all13 retained; no prospective branch outcome hardcoded',
         dependency_scope='owned source/binaries/XML/constants checked here; full transitive closure belongs root freeze audit'))

    def invoke(binary, roster, name):
        src = out/(name+'_inputs.json'); dst = out/(name+'.json'); dump(src, {'cases': roster})
        result = subprocess.run([str(binary), str(xml), str(constants), str(src), str(dst)], capture_output=True, text=True)
        dst.with_suffix('.stdout').write_text(result.stdout); dst.with_suffix('.stderr').write_text(result.stderr)
        dst.with_suffix('.exit').write_text(str(result.returncode)+'\n'); need(result.returncode == 0, name+' process return')
        data = json.loads(dst.read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        finite_tree(data); need(data['model_success'] is True, name+' model initialized')
        need(len(data['cases']) == len(roster) and [x['name'] for x in data['cases']] == [x['name'] for x in roster], name+' exact ordered roster')
        return data

    sides = [dict(name=p['name']+'__'+key, **p[key]) for p in pairs for key in ('nominal', 'trial')]
    original = invoke(value, sides, 'original_closed_bothsides')['cases']
    closed = {x['name']: {k: v for k, v in x.items() if k != 'name'} for x in original}
    nominal_roster = [dict(name=p['name'], **p['nominal']) for p in pairs]
    refs = invoke(extension, nominal_roster, 'original_nominal_maps')['cases']
    actual = invoke(args.binary, pairs, 'new_finite_trial')
    flags(actual['policy']); need(actual['policy']['name'] == 'FINITE_CLOSED_TRIAL_SAMPLED_BRANCH_DIAGNOSTIC_V1', 'policy name')
    need(actual['policy']['cycle_dt'] == .004 and actual['policy']['substep_dt'] == .002 and
         actual['policy']['state_rows'] == 30 and actual['policy']['cell_input_columns'] == 8, 'fixed policy clock/shape')
    inspections = []; inspect_inputs = {}
    for p in pairs:
        for key in ('nominal', 'trial'):
            forward = closed[p['name']+'__'+key]; check_value(forward, p[key]); previous = p[key]['state']
            for i, row in enumerate(forward['substeps']):
                entry = dict(name=p['name']+'__'+key+'__p'+str(i), q=previous['q'], v=previous['v'], C=row['C'])
                inspections.append(entry); inspect_inputs[entry['name']] = entry; previous = point(row)
    physical_refs = {}
    for offset in range(0, len(inspections), BATCH):
        batch = invoke(physical, inspections[offset:offset+BATCH], 'original_physical_'+str(offset//BATCH))
        for entry in batch['cases']:
            physical_refs[entry['name']] = entry
    limits = np.asarray(json.loads(constants.read_text())['control_range']).reshape(7, 2)
    reports = []; local_records = []
    for p, new, ext in zip(pairs, actual['cases'], refs):
        flags(new); nominal = closed[p['name']+'__nominal']; trial = closed[p['name']+'__trial']
        ext_without_name = {k: v for k, v in ext.items() if k != 'name'}
        need(ext['value'] == nominal and new['nominal'] == ext_without_name and new['trial'] == trial, 'exact old values/maps/errors/prefixes')
        checked_maps(ext, p['nominal'])
        side_data = {}
        for key, forward in (('nominal', nominal), ('trial', trial)):
            rows = forward['substeps']; inspected = new[key+'_inspections']; need(len(inspected) == len(rows), 'all actual point inspections')
            data = []
            for i, (row, ins) in enumerate(zip(rows, inspected)):
                flags(ins); refname = p['name']+'__'+key+'__p'+str(i); ref = physical_refs[refname]; inp = inspect_inputs[refname]
                need(ref['value_success'] is True, 'actual physical value available')
                val = ref['value']; diag = ref['diagnostics']; sig = signature(ref)
                need(timing(ins) == timing(row) and ins['elapsed_s'] == row['elapsed_s'], 'inspection timestamp')
                close(ins['q_before'], inp['q'], 'own physical input q', 0.); close(ins['v_before'], inp['v'], 'own physical input v', 0.)
                close(ins['C'], inp['C'], 'actual latched physical target', 0.)
                close(val['q'], row['q'], 'original physical endpoint q', 0.); close(val['v'], row['v'], 'original physical endpoint v', 0.)
                small_value = {k: val[k] for k in ('q', 'v', 'control_clips', 'force_clips', 'friction')}
                need(ins['physical_value'] == small_value, 'preserved independent physical value')
                for k in ('control', 'actuator', 'joint_force', 'solve_conditions', 'solve_residuals'):
                    need(ins[k] == diag[k], 'full original point diagnostic '+k)
                for k in ('friction_gradient', 'friction_margin'):
                    need(ins[k] == diag.get(k, []), 'original point diagnostic '+k)
                boolean(ins, 'exact_value_parity', True); boolean(ins, 'value_success', True)
                boolean(ins, 'jacobian_success', ref['jacobian_success']); boolean(ins, 'signature_complete', True)
                C = array(ins['C'], (7,)); strict_C = bool(((C-limits[:, 0]) > 1e-8).all() and ((limits[:, 1]-C) > 1e-8).all())
                boolean(ins, 'strict_C', strict_C)
                if ref['jacobian_success']:
                    close(array(ins['jacobian'], (14, 21)), array(ref['jacobian'], (14, 21)), 'original point Jacobian', 0.)
                else:
                    need('jacobian' not in ins and ins.get('error') == ref.get('error'), 'unsupported exact original error/no matrix')
                data.append(dict(strict=strict_C and ref['jacobian_success'], signature=sig))
            side_data[key] = data
        mesh = topology(p['nominal']) == topology(p['trial'])
        complete = nominal['success'] and trial['success']
        ns, ts = side_data['nominal'], side_data['trial']
        strict = bool(complete and ns and len(ns) == len(ts) and all(x['strict'] for x in ns+ts))
        comparisons = []
        if mesh:
            for i in range(min(len(ns), len(ts))):
                row = nominal['substeps'][i]; trow = trial['substeps'][i]
                need(timing(row) == timing(trow) and row['elapsed_s'] == trow['elapsed_s'], 'paired exact timestamp')
                comparisons.append(dict(cell=row['cell'], cycle=row['cycle'], half=row['half'], elapsed_s=row['elapsed_s'],
                     nominal_strict=ns[i]['strict'], trial_strict=ts[i]['strict'], signatures_available=True,
                     branches_equal=ns[i]['signature'] == ts[i]['signature']))
        need(len(new['comparisons']) == len(comparisons), 'complete/partial comparison roster')
        for got, expected in zip(new['comparisons'], comparisons):
            flags(got)
            for k, v in expected.items():
                if type(v) is bool:
                    boolean(got, k, v)
                else:
                    need(got[k] == v and type(got[k]) is type(v), 'typed comparison '+k)
        changed = any(not c['branches_equal'] for c in comparisons)
        equal = bool(mesh and complete and ns and len(ns) == len(ts) and all(c['branches_equal'] for c in comparisons))
        for k, expected in (('mesh_matches', mesh), ('all_forward_complete', complete), ('all_sampled_strict', strict),
                            ('sampled_branch_change', changed), ('all_sampled_signatures_equal', equal)):
            boolean(new, k, expected)
        outcome = ('mesh_mismatch' if not mesh else 'forward_failed' if not complete else
                   'unsupported' if not strict or not ext['extension_jacobian_success'] else
                   'sampled_branch_changed' if changed else 'sampled_strict_branches_unchanged')
        need(new['outcome'] == outcome and 'error' not in new and 'affine_error' not in new, 'independent outcome/no diagnostic error')
        expected_residuals = []; maximum = 0.; identity_maximum = 0.
        block_maxima = {key: dict(units=unit, max_absolute=0.) for key, _, _, unit in BLOCKS}
        if mesh and ext['substep_maps'] and trial['substeps']:
            deviation = pack(p['trial']['state'])-pack(p['nominal']['state'])
            trial_points = {timing(row): point(row) for row in trial['substeps']}
            trial_origins = [p['trial']['state']] + trial['cell_end_states']
            for c, cell in enumerate(p['nominal']['cells']):
                prefix = [m for m in ext['substep_maps'] if m['cell'] == c]
                if not prefix or not any(key[0] == c for key in trial_points):
                    break
                need(c < len(trial_origins), 'actual trial origin available for local arithmetic')
                du = np.r_[array(p['trial']['cells'][c]['alpha'], (7,))-array(cell['alpha'], (7,)), p['trial']['cells'][c]['b']-cell['b']]
                schedule = [('substep', m, trial_points.get(timing(m))) for m in prefix]
                for m in ext['cycle_maps']:
                    if m['cell'] == c:
                        index = sum(topology(p['nominal'])[:c])+m['cycle']-1
                        schedule.append(('cycle', m, trial['cycle_end_states'][index] if index < len(trial['cycle_end_states']) else None))
                end = next((m for m in ext['cell_maps'] if m['cell'] == c), None)
                if end is not None:
                    schedule.append(('cell', end, trial['cell_end_states'][c] if c < len(trial['cell_end_states']) else None))
                for kind, m, real in schedule:
                    if real is None:
                        continue
                    A = array(m['A'] if kind == 'cell' else m['cell_A'], (30, 30))
                    B = array(m['B'] if kind == 'cell' else m['cell_B'], (30, 8))
                    origin = m['origin'] if kind == 'cell' else m['cell_origin']
                    linear = A@deviation+B@du; prediction = pack(m['state'])+linear; residual = pack(real)-prediction
                    actual_deviation = pack(trial_origins[c])-pack(origin)
                    local = pack(real)-pack(m['state'])-A@actual_deviation-B@du
                    origin_global_error = actual_deviation-deviation
                    identity = residual-local-A@origin_global_error
                    close(identity, np.zeros(30), 'GLOBAL=LOCAL+A*origin GLOBAL error')
                    maximum = max(maximum, float(np.max(abs(residual)))); identity_maximum = max(identity_maximum, float(np.max(abs(identity))))
                    for key, offset, size, _ in BLOCKS:
                        block_maxima[key]['max_absolute'] = max(block_maxima[key]['max_absolute'],
                            float(np.max(abs(residual[offset:offset+size]))))
                    expected_residuals.append(dict(endpoint=kind, cell=c, cycle=m['cycle'], half=m['half'], nominal_state=m['state'],
                         trial_state=real, nominal_cell_origin=origin, cell_origin_deviation=deviation.copy(), input_deviation=du,
                         linear_deviation=linear, prediction=prediction, residual=residual))
                    local_records.append(dict(name=p['name'], endpoint=kind, cell=c, cycle=m['cycle'], half=m['half'],
                         local_residual=local.tolist(), actual_cell_origin_deviation=actual_deviation.tolist(),
                         global_origin_error=origin_global_error.tolist(), identity_error=identity.tolist()))
                if end is None:
                    break
                deviation = array(end['A'], (30, 30))@deviation+array(end['B'], (30, 8))@du
                need(np.isfinite(deviation).all(), 'propagated GLOBAL deviation finite')
        need(len(new['residuals']) == len(expected_residuals), 'exact available GLOBAL residual roster')
        for got, expected in zip(new['residuals'], expected_residuals):
            flags(got)
            for k in ('endpoint', 'cell', 'cycle', 'half'):
                need(got[k] == expected[k] and type(got[k]) is type(expected[k]), 'typed residual timing '+k)
            for k in ('nominal_state', 'trial_state', 'nominal_cell_origin'):
                close(pack(got[k]), pack(expected[k]), 'residual actual state '+k, 0.)
            for k in ('cell_origin_deviation', 'linear_deviation', 'prediction', 'residual'):
                close(array(got[k], (30,)), expected[k], 'GLOBAL residual '+k)
            close(array(got['input_deviation'], (8,)), expected['input_deviation'], 'distinct cell input deviation', 0.)
            need(set(got['block_residuals']) == {x[0] for x in BLOCKS}, 'all SI residual blocks')
            for key, offset, size, unit in BLOCKS:
                block = got['block_residuals'][key]; need(block['units'] == unit, 'block units')
                need(type(block['max_absolute']) in (int, float) and math.isfinite(block['max_absolute']), 'typed finite block max')
                close(block['max_absolute'], np.max(abs(expected['residual'][offset:offset+size])), 'block SI max')
        # A declared negative against aggregate-only signatures, not a model gate.
        if p['name'] == 'root_trial_equal_clip_counts_changed_sides':
            need(nominal['substeps'][0]['force_clips'] == trial['substeps'][0]['force_clips'] and
                 ns[0]['signature'] != ts[0]['signature'], 'equal clip counts do not replace signed signatures')
        reports.append(dict(name=p['name'], outcome=outcome, nominal_forward_complete=nominal['success'],
             trial_forward_complete=trial['success'], nominal_half_count=len(nominal['substeps']), trial_half_count=len(trial['substeps']),
             nominal_certified_prefix=len(ext['substep_maps']), comparison_count=len(comparisons), residual_count=len(expected_residuals),
             global_residual_mixed_units_max_diagnostic_only=maximum, global_residual_SI_blocks=block_maxima,
             local_global_identity_max=identity_maximum))
    dump(out/'INDEPENDENT_LOCAL_RESIDUAL_IDENTITIES.json', local_records)
    for path in owned:
        need(sha(path) == frozen[str(path)]['sha256'], 'owned input unchanged '+str(path))
    need(source.read_bytes() == source_bytes and args.predeclared.read_bytes() == predeclared and
         args.freeze.read_bytes() == freeze_bytes, 'startup snapshots unchanged before READY')
    report = dict(decision='PASS_SELECTED_FINITE_TRIAL_DIAGNOSTIC_ARITHMETIC', scope=__doc__,
         source_sha256=hashlib.sha256(source_bytes).hexdigest(), binary_sha256=args.binary_sha, freeze_sha256=args.freeze_sha,
         predeclared_sha256=PREDECLARED_SHA, original_closed_sha256=VALUE_SHA, nominal_map_sha256=EXTENSION_SHA,
         physical_certificate_sha256=PHYSICAL_SHA, pairs=reports, physical_point_calls=len(inspections),
         residual_performance_gate=False, new_plant=False, phase5='NOT_ACCEPTED')
    dump(out/'audit.json', report)
    dump(out/'READY.json', dict(files={q.name: dict(sha256=sha(q), bytes=q.stat().st_size)
         for q in out.iterdir() if q.is_file()}, scope=__doc__))
    print(json.dumps(report, allow_nan=False))


if __name__ == '__main__':
    main()
