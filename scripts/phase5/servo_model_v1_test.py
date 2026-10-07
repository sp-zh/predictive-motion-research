#!/usr/bin/env python3
"""Synthetic identification recovery and affine/held-target contract regressions."""
import unittest
import numpy as np
from servo_model_v1 import identify, matrices, step, N, DT


class ServoModelTest(unittest.TestCase):
    def fixture(self):
        rng = np.random.default_rng(91011)
        e = .15 * np.eye(N) + .002 * rng.normal(size=(N, N))
        v = .9 * np.eye(N) + .001 * rng.normal(size=(N, N))
        d = rng.normal(size=N) * 1e-4
        return rng, e, v, d

    def test_recovers_coupled_known_model(self):
        rng, e, v, d = self.fixture()
        q, vel, c = (rng.normal(size=(1000, N)) for _ in range(3))
        vn = (c - q) @ e.T + vel @ v.T + d
        ee, vv, dd, diag = identify(q, vel, c, vn)
        np.testing.assert_allclose(ee, e, atol=1e-14, rtol=0)
        np.testing.assert_allclose(vv, v, atol=1e-14, rtol=0)
        np.testing.assert_allclose(dd, d, atol=1e-14, rtol=0)
        self.assertEqual(diag['rank'], 15)

    def test_unexcited_data_rejected(self):
        z = np.zeros((100, N))
        with self.assertRaises(ValueError):
            identify(z, z, z, z)

    def test_rank_deficient_data_rejected(self):
        rng, _, _, _ = self.fixture()
        z = np.repeat(rng.normal(size=(100, 1)), N, axis=1)
        with self.assertRaises(ValueError):
            identify(z, z, 2 * z, z)

    def test_affine_translation_and_two_held_steps(self):
        rng, e, v, d = self.fixture()
        q, vel, c, shift = (rng.normal(size=N) for _ in range(4))
        p, b, f = matrices(e, v, d)
        q1, v1 = step(q, vel, c, e, v, d)
        np.testing.assert_allclose(np.r_[q1, v1], p @ np.r_[q, vel] + b @ c + f, atol=1e-14, rtol=0)
        qs, vs = step(q + shift, vel, c + shift, e, v, d)
        np.testing.assert_allclose(qs - shift, q1, atol=1e-14, rtol=0)
        np.testing.assert_allclose(vs, v1, atol=1e-14, rtol=0)
        q2, v2 = step(q1, v1, c, e, v, d)
        composed = p @ p @ np.r_[q, vel] + (p + np.eye(2 * N)) @ (b @ c + f)
        np.testing.assert_allclose(np.r_[q2, v2], composed, atol=1e-14, rtol=0)


if __name__ == '__main__':
    unittest.main()
