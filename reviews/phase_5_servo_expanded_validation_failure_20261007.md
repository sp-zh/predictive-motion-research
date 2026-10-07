# Phase 5 prospective expanded servo validation failure

Date: 2026-10-07, America/Toronto. Expanded validation decision: **FAIL**.
The smaller soft-v2 component remains accepted only for its independently
checked recorded-input scope. Phase 5 is unaccepted; main MPC was not changed.

The independent soft-v2 audit found that the earlier high-Q preparation leaves
the small model domain. Root therefore requested a prospective expanded
development waveform with unchanged coefficients and error thresholds. This
trial retains seed 91012 initialization and declares amplitude 0.008 rad,
frequency `0.50+0.067*j` Hz, phase `0.19*j`, 8 s excitation and the existing
0.8 s ramp/2 s warmup. No final/evaluation seeds or model refitting are used.

The original model SHA remains
`984ee85d086aeba7da8260a20b21b301e23dfd2c698a6c61ace0ff956bbec1bb` before
and after collection. Its original domain metadata is unchanged. A separate
prospective diagnostic box is declared before collection: training q-range
midpoint ±0.012 rad, |v|<=0.05 rad/s, and each target-minus-q axis centered at
`-frozen_bias/kp` ±0.022 rad. The target-error radius accounts for a 0.012 rad
physical-position radius, 0.008 target excitation and 0.002 reserve. It is a
prospective diagnostic box, not a mathematical invariant or robust error bound.
The prefrozen scorer retains every window and reports old/new domain failures.
Successful collection/scoring would still require independent review before
authorizing any domain extension.

The run is `servo-soft-friction-v2-expanded-validation`; it uses the exact
already-built validation-only binary. The existing velocity, acceleration,
jerk, true geometry, current-command age 50 ms, native SOLVED-only and original
SI acceptance guards are retained. All 187 frozen inputs are materialized.

Collection returns 1 after 2.797922 wall seconds with
`identification command PRIMAL_INFEASIBLE`. The last complete tick is 853,
virtual time 3.416 s, only 1.416 s into excitation. There are 1,708 substep
records, including 708 active records. No summary or completed-stop record
exists. The original fixture exception path exits the simulator process after
rejecting the command; it does not establish a controlled physical stop. No
hardware is involved. The common main-controller stop evidence is unchanged,
but it cannot be credited to this failed fixture.

The retained raw SHA is
`b913b712590be96eeec031a0b62a88e42d462ed2ac13d87ddf6b8a5d648a29e2`.
Recorded contacts are zero, and minimum recorded clearance is 0.0132673448 m.
These preceding observations do not prove feasibility of the rejected QP or
explain its failure. All seven joints have old-domain q/v/target-error violations;
counts and the last complete physical/accepted-command state are preserved in
`partial_trace_diagnostics.json`. The largest active physical speed reaches
0.0394417 rad/s, while accepted command-speed peaks reach 0.0456794 rad/s.

The fixed scorer writes `FAIL_GUARD_OR_INCOMPLETE_TRACE`; it does not convert a
partial run into expanded model acceptance. No threshold, amplitude or model
coefficient is changed after observing this trial. The three-panel actual-data
figure marks the last recorded command, explicitly says no successful bounded
stop exists, and distinguishes accepted target from physical motion. It was
visually inspected for readable labels, units and failure scope; no CAD/model
geometry units changed.

Next work must reconstruct or capture the failing command QP and identify
which original bounds/geometry rows conflict, or whether numerical failure
occurs despite independently demonstrated feasibility. Do not weaken guards
or accept PRIMAL_INFEASIBLE. Reconstructed data must be labeled as such, not
claimed as an original bit-exact runtime assembly. Verify failure-stop capture
with the shared bounded-stop policy in a new declared diagnostic; retain this
original incomplete trace. A guarded, complete expanded trace and independent
model/domain review remain necessary before main C++ contract integration.
