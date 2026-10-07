#!/usr/bin/env python3
"""Synthetic exact first-order position-servo contract counterexample; no robot trial."""
import argparse
import json
import math
from pathlib import Path


def run(dt=0.004, duration=0.4, pole=10.0, acceleration=1.0):
    n = round(duration / dt)
    z = math.exp(-pole * dt)
    q = v = c = 0.0
    qc = vc = cc = w = 0.0
    for _ in range(n):
        # Current measured-state adapter, held position target during physics.
        c += dt * (v + dt * acceleration)
        q = z * q + (1 - z) * c
        v = pole * (c - q)
        # Recommended command-acceleration contract plus explicit servo lag.
        w += dt * acceleration
        cc += dt * w
        qc = z * qc + (1 - z) * cc
        vc = pole * (cc - qc)
    exact_c = 0.5 * (duration * duration + duration * dt) * acceleration
    assert abs(cc - exact_c) < 1e-13
    assert abs(q - 0.5 * duration * duration * acceleration) > 0.05
    return {
        "dt_s": dt,
        "duration_s": duration,
        "position_servo_pole_per_s": pole,
        "input_acceleration": acceleration,
        "kinematic_prediction": {"q": 0.5 * duration**2 * acceleration,
                                 "v": duration * acceleration},
        "measured_state_adapter_servo": {"q": q, "v": v, "position_target": c},
        "command_acceleration_with_servo_model": {
            "q": qc, "v": vc, "position_target": cc, "command_velocity": w,
            "closed_form_target_error": abs(cc - exact_c)},
        "scope": "Synthetic scalar lag fixture only. The pole is a declared example,"
                 " not identified FR3 dynamics; no MuJoCo or robot run.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Refuse overwrite")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(run(), indent=2) + "\n")
    print("SYNTHETIC_SERVO_CONTRACT_REFERENCE_PASS")


if __name__ == "__main__":
    main()
