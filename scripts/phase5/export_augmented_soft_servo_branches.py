#!/usr/bin/env python3
"""Export fixed-oracle branch fixtures; model algebra only, never plant data."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ORACLE_SHA = 'c63f524d2002323ca635574addcf8ef04a498154ea171ac5a58deda088853710'
MODEL_SHA = '984ee85d086aeba7da8260a20b21b301e23dfd2c698a6c61ace0ff956bbec1bb'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.reference / 'SOURCE_SNAPSHOT.py'
    model_file = args.reference / 'MODEL_SNAPSHOT.json'
    assert sha(source) == ORACLE_SHA and sha(model_file) == MODEL_SHA
    own_source = Path(__file__).read_bytes()
    spec = importlib.util.spec_from_file_location('fixed_soft_oracle', source)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    frozen = json.loads(model_file.read_text())
    cases = []

    def add(name, model, state, threshold=False):
        n = len(model['mass_effective_kg_m2'])
        control = np.zeros(n + 1)
        value, branches = oracle.cycle_direct(state, control, model)
        a, b, defect = oracle.cycle_linearization(state, control, model)
        error = float(np.max(abs(value - a @ state - b @ control - defect)))
        assert error < 1e-12
        cases.append({'name': name, 'model': model, 'initial': state.tolist(),
                      'control': control.tolist(), 'dt_s': .004,
                      'next_state': value.tolist(), 'branches_2ms': branches,
                      'A': a.tolist(), 'B': b.tolist(), 'defect': defect.tolist(),
                      'affine_identity_error': error,
                      'exact_clip_threshold': threshold,
                      'derivative_scope': 'Declared saturated-side convention; no unique ordinary Jacobian' if threshold else 'Existing fixed-oracle smooth branch fixture'})

    for label, model in [('n1_synthetic', oracle.synthetic_model()), ('n7_frozen', frozen)]:
        n = len(model['mass_effective_kg_m2'])
        q = .5 * (np.array(model['local_box']['q_min']) + np.array(model['local_box']['q_max']))
        mass, bias, kp, damping, bound, impedance, decay = oracle.params(model)
        for level in [0., 1.5, -1.5]:
            state = np.r_[q, np.zeros(n), q - bias / kp + level * bound / (impedance * kp), np.zeros(n), .2, .01]
            add(f'{label}_level_{level}', copy.deepcopy(model), state)

    for sign in [1., -1.]:
        model = oracle.synthetic_model()
        model['mass_effective_kg_m2'] = [1.]
        model['bias_Nm'] = [0.]
        for key, value in [('kp_Nm_rad', 1.), ('damping_Nm_s_rad', 1.),
                           ('friction_bound_Nm', .5), ('impedance', .5),
                           ('reference_decay_s_inv', 1.)]:
            model['public_parameters'][key] = [value]
        # Synthetic threshold test only; these bounds do not change the FR3 box.
        model['local_box'] = {'q_min': [-2.], 'q_max': [2.], 'v_abs_max': .05,
                              'target_error_min': [-2.], 'target_error_max': [2.]}
        add(f'n1_exact_threshold_{sign}', model, np.array([0., 0., sign, 0., .2, .01]), True)
        assert cases[-1]['branches_2ms'][0] == [int(sign)]

    assert sha(source) == ORACLE_SHA and sha(model_file) == MODEL_SHA
    assert Path(__file__).read_bytes() == own_source
    args.output.mkdir(parents=True, exist_ok=False)
    packet = {'scope': __doc__, 'oracle_sha256': ORACLE_SHA,
              'frozen_model_sha256': MODEL_SHA,
              'exporter_sha256': hashlib.sha256(own_source).hexdigest(),
              'limits': ['No new oracle, fitting, plant or domain accuracy evidence',
                         'Six existing smooth branch fixtures and two synthetic exact clip thresholds',
                         'Synthetic threshold bounds do not enlarge the frozen FR3 model box'],
              'cases': cases}
    (args.output / 'branch_packet.json').write_text(json.dumps(packet, indent=2) + '\n')
    (args.output / 'SOURCE_SNAPSHOT.py').write_bytes(own_source)
    files = {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size} for p in args.output.iterdir()}
    (args.output / 'READY.json').write_text(json.dumps({'files': files,
        'oracle_sha256': ORACLE_SHA, 'frozen_model_sha256': MODEL_SHA}, indent=2) + '\n')
    print(json.dumps({'cases': len(cases), 'files': files}))


if __name__ == '__main__':
    main()
