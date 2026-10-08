# Root predeclaration: augmented cycle/cell sensitivities

Scope:30-state command/physical/progress cycle/cell reference only, before
horizon planner/cost/main-controller integration or new plant execution. Last
physical derivative unit1df837310697ae7f129b74dd3b42c97eb1d15ce7 is remotely
verified. No new composed sensitivity numerical calls have run by root.

State z=(q7,v7,C7,w7,s,r), input u=(alpha7,b). h=.004. J1 is evaluated at the
initial physical state and already updated held C_next; J2 uses its own2ms
physical state and the same target. P=J2_y*J1_y and Q=J2_y*J1_C+J2_C.
The cycle physical A blocks are P,Q,hQ and input-alpha B=h²Q; command C has
A_C=I,A_w=hI,B_alpha=h²I, command w A_w=I,B_alpha=hI. Progress A=[[1,h],[0,1]]
and B_b=[.5h²,h]. Half physical uses J1; command C/w are already fully latched
while progress uses the exact t=.002 reference. This half tuple is diagnostic,
not an ordinary new4ms initial state.

For held u within a cell, start A=I,B=0 and compose A_new=A_cycle*A_old,
B_new=A_cycle*B_old+B_cycle. Half prefixes compose analogously. Every defect
uses its own declared nominal output, original initial state and held input:
defect=z_nominal_output-A*z_original-B*u. Cell-local B describes only that
cell's control; different cells' B values cannot be simply added as one input.
Root will independently multiply returned cell matrices into selected full
nonuniform rollout initial/control sensitivities; no horizon planner is delivered.

A complete derivative requires every physical substep certified and all products
finite. Keep original complete/failed forward outputs and explicit certified
prefix times. Omit full uncertified A/B/defect instead of filling zeros or reusing
stale matrices. Closed-domain boundaries may have algebraic derivatives but lack
a two-sided admissible neighborhood. The proposed reference deliberately omits
boundary certification; common task start s=0,r=0 is outside this support.
Do not shift actual progress/history to epsilon to bypass it. Future main
integration needs independently validated boundary/feasible-direction or canonical
extension semantics. No nondifferentiability/safety theorem follows from omission.

Root's prospective interior case uses a known frozen nominal q/v=0 and C_eq
from current public gravity bias/affine actuator law, accepted w alternating
1e-4rad/s (distinct from physical v), s=.2,r=.08. Nonuniform cycle counts
[1,3,2,4], alpha scalars [.003,-.002,.001,0] with alternating joint signs,
and b=[.01,-.005,.002,0] are declared before sensitivity tests. All30 initial
state directions and8 cell-control directions use both fixed epsilon1e-6
and3e-7. Each perturbation must retain original domain and physical/clip strict
branches. Independent command/progress derivatives use closed-form sums.

Important additional identities avoid hiding tiny alpha columns behind a loose
absolute FD gate: every physical half has Aq=previous_Aq+.002*current_Av and
Bq=previous_Bq+.002*current_Bv. Command/progress block coefficients are checked
against exact closed forms, not only FD. Matrices can have mixed SI derivative
units; per-entry absolute+relative gates and roundoff scope must be explicit.
The old augmented value CLI accepts at most128 cases; preserve all requested
FD rosters through deterministic batches, never silently truncate. A full
4cell independent chain has30 initial plus32 distinct control directions,
249 old-value cases including nominal across both signed epsilon steps.

The read-only math specialist confirms these equations and semantics, without
new files, builds or numerical tests. Component checks do not establish command
jerk/progress slew, physical stopping/geometry, accuracy domain, runtime, task
success or Phase5 acceptance.

Root audit implementation is `scripts/phase5/audit_public_augmented_sensitivity_root.py`.
Additional declared cases:1cycle, held10 cycles and equal-control split[1,3,2,4].
Single/held cases have38 independent state/control directions; the nonuniform
case has62 directions. Both signed perturbations at both epsilons plus each
nominal give555 old2fa value calls, in batches≤96. Original fa1 single-step
current diagnostics are evaluated at every returned perturbation halfstep,
using the previous physical q/v and its actual held target. These serve only
strict branch/clip/condition verification, never future plant observations.
All M,K,Hsym positive-definite condition limits and strict initial/generated
C/w/s/r plus held alpha domain margins are independently checked. Every
perturbation must match its nominal trajectory's branch signature at every step.

Explicit negative roster:initial s=0, initial r=0, alpha0=1, future progress
speed domain failure from r=.199/b=.1 over4cycles, and q dimension6. Valid
initial-boundary forward values are retained without fabricated matrices;
the future failure must retain certified completed cycles but no final cell map.
Read-only audit identified and corrected omitted M-condition and initial-domain
checks before any root numerical call; model source, parameters and policy
were unchanged. No model numerical call was used to select these corrections.
