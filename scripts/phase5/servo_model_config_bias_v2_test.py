#!/usr/bin/env python3
"""Synthetic configuration-bias affine recovery and reference/hold regressions."""
import unittest
import numpy as np
from servo_model_config_bias_v2 import identify, matrices, step, N


class ConfigBiasTest(unittest.TestCase):
    def fixture(self):
        rng = np.random.default_rng(91011)
        e = .15 * np.eye(N) + .002 * rng.normal(size=(N, N))
        v = .9 * np.eye(N) + .001 * rng.normal(size=(N, N))
        g = .005 * rng.normal(size=(N, N))
        d = rng.normal(size=N) * 1e-4
        reference = rng.normal(size=N)
        return rng, e, v, g, d, reference

    def test_known_nonzero_configuration_bias_recovered(self):
        rng, e, v, g, d, reference = self.fixture()
        q, vel, c = (rng.normal(size=(2000, N)) for _ in range(3))
        vn = (c - q) @ e.T + vel @ v.T + (q - reference) @ g.T + d
        ee, vv, gg, dd, diag = identify(q, vel, c, vn, reference)
        for actual, expected in [(ee, e), (vv, v), (gg, g), (dd, d)]:
            np.testing.assert_allclose(actual, expected, atol=1e-14, rtol=0)
        self.assertEqual(diag['rank'], 22)

    def test_unexcited_and_rank_deficient_data_rejected(self):
        rng, _, _, _, _, reference = self.fixture()
        zero = np.zeros((100, N))
        repeat = np.repeat(rng.normal(size=(100, 1)), N, axis=1)
        for z in [zero, repeat]:
            with self.assertRaises(ValueError):
                identify(z, z, 2 * z, z, reference)

    def test_reference_origin_reparameterization(self):
        rng, e, v, g, d, reference = self.fixture()
        q, vel, c, shift = (rng.normal(size=N) for _ in range(4))
        qn, vn = step(q, vel, c, e, v, g, d, reference)
        qn2, vn2 = step(q, vel, c, e, v, g, d + g @ shift, reference + shift)
        np.testing.assert_allclose(qn2, qn, atol=1e-14, rtol=0)
        np.testing.assert_allclose(vn2, vn, atol=1e-14, rtol=0)

    def test_direct_and_composed_affine_hold(self):
        rng, e, v, g, d, reference = self.fixture()
        q, vel, c = (rng.normal(size=N) for _ in range(3))
        p, b, f = matrices(e, v, g, d, reference)
        state = np.r_[q, vel]
        for _ in range(20):
            q, vel = step(q, vel, c, e, v, g, d, reference)
            state = p @ state + b @ c + f
            np.testing.assert_allclose(state, np.r_[q, vel], atol=1e-13, rtol=0)


if __name__ == '__main__':
    unittest.main()
