#!/usr/bin/env python3
"""Synthetic public-box optimality, causal transition tangent and parameter recovery."""
import unittest
import numpy as np
from scipy.optimize import minimize_scalar
from servo_model_soft_friction_v2 import identify, step, tangent, N, DT


class SoftServoTest(unittest.TestCase):
    def fixture(self):
        public = {'kp_Nm_rad': [1000.+100*j for j in range(N)], 'damping_Nm_s_rad': [100.+10*j for j in range(N)],
                  'friction_bound_Nm': [.3+.03*j for j in range(N)], 'impedance': [.9]*N, 'reference_decay_s_inv': [100.]*N}
        model = {'public_parameters': public, 'mass_effective_kg_m2': [.2+.1*j for j in range(N)], 'bias_Nm': [.01*j for j in range(N)]}
        return np.random.default_rng(91011), model

    def test_matches_independent_scalar_box_minimization(self):
        rng, model = self.fixture()
        for _ in range(30):
            q = rng.normal(size=N) * .001
            v = rng.normal(size=N) * .002
            c = q + rng.normal(size=N) * .0004
            qp, vp = step(q, v, c, model)
            for j in range(N):
                mass = model['mass_effective_kg_m2'][j]
                bias = model['bias_Nm'][j]
                p = model['public_parameters']
                kp, damping, eta, imp, decay = [p[k][j] for k in ['kp_Nm_rad', 'damping_Nm_s_rad', 'friction_bound_Nm', 'impedance', 'reference_decay_s_inv']]
                smooth_force = kp*(c[j]-q[j])-damping*v[j]+bias
                regularizer = (1-imp)/(imp*mass)
                obj = lambda force: .5*(1/mass+regularizer)*force**2 + (smooth_force/mass+decay*v[j])*force
                result = minimize_scalar(obj, bounds=(-eta, eta), method='bounded', options={'xatol': 1e-13})
                forces = [-eta, eta, result.x]
                force = min(forces, key=obj)
                predicted_v = v[j] + DT/(mass+DT*damping)*(smooth_force+force)
                self.assertAlmostEqual(vp[j], predicted_v, delta=1e-10)
                self.assertAlmostEqual(qp[j], q[j]+DT*predicted_v, delta=1e-12)

    def test_affine_tangent_and_finite_difference_both_regimes(self):
        rng, model = self.fixture()
        for multiplier in [0., 5.]:
            q, v, c = np.zeros(N), np.zeros(N), np.ones(N)*multiplier*.001
            p, b, f = tangent(q, v, c, model)
            actual = np.r_[*step(q, v, c, model)]
            np.testing.assert_allclose(actual, p@np.r_[q,v]+b@c+f, atol=1e-14, rtol=0)
            h=1e-8
            for j in range(3*N):
                plus=np.r_[q,v,c];minus=plus.copy();plus[j]+=h;minus[j]-=h
                fd=(np.r_[*step(plus[:N],plus[N:2*N],plus[2*N:],model)]-np.r_[*step(minus[:N],minus[N:2*N],minus[2*N:],model)])/(2*h)
                expected = p[:,j] if j<2*N else b[:,j-2*N]
                np.testing.assert_allclose(fd, expected, atol=1e-9, rtol=0)

    def test_recovers_known_effective_parameters(self):
        rng, model = self.fixture()
        q = rng.normal(size=(1500,N))*.001
        v = rng.normal(size=(1500,N))*.002
        c = q+rng.normal(size=(1500,N))*.0005
        _, vn = step(q,v,c,model)
        mass,bias,diagnostics = identify(q,v,c,vn,model['public_parameters'])
        np.testing.assert_allclose(mass,model['mass_effective_kg_m2'],atol=1e-7,rtol=0)
        np.testing.assert_allclose(bias,model['bias_Nm'],atol=1e-8,rtol=0)
        self.assertTrue(all(d['response_jacobian_rank']==2 for d in diagnostics))

    def test_no_excitation_fails_identification(self):
        _, model = self.fixture()
        z=np.zeros((100,N))
        with self.assertRaises(ValueError):
            identify(z,z,z,z,model['public_parameters'])


if __name__ == '__main__':
    unittest.main()
