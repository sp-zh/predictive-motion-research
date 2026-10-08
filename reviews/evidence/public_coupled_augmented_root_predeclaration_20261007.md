# Root predeclaration: coupled augmented transition

Scope: isolated transition only. No Jacobian, cost, optimization, new plant,
parameter fitting, main-controller integration or Phase5 acceptance. The frozen
C++ v2 checkpoint b1d5c2f034735b3955255f16c0c9b8ac86c7ca49 is already backed
up and independently matched to the private remote before this unit.

The physical q/v, accepted C/w and progress s/r are separate states. For each
4ms cycle, update w first by .004 alpha, C by .004 times the updated w, then
hold that C over two .002 physical steps. Physical q/v propagate from the
previous predicted physical state. The progress reference at each2ms point
uses the initial progress state and exact constant-b trajectory.

The independent command oracle uses rational closed-form sums. For m held
cycles and H=.004m, C_H=C0+H*w0+.5*(H²+H*.004)*alpha and w_H=w0+H*alpha.
Progress is s_H=s0+H*r0+.5H²*b, r_H=r0+H*b. A40ms cell with zero C/w and
alpha=1 must reach C=.00088 rather than the single-update shortcut .0016.
Splitting one held16cycle input into1/10/3/2cycles must preserve all32
intermediate command/progress states. These algebra checks ran without any
physical model call before augmented-model forecasts.

Root's planned separate physical checks use existing development seed91013
initial q/v at tick690, synthetic C=q+2e-4rad and w=v+1e-4rad/s, s=.2/r=.08.
Mesh cells contain1/10/3/2cycles with alpha scalars .07/-.04/.02/0 and alternating
joint signs, progress b=.03/-.01/.02/0. Derived held targets will be sent to the
unchanged frozen v2 physical probe; its every2ms result will be compared with
the new wrapper. This is a paired component check, not a new physical accuracy
claim. Additional measured-target compatibility checks use the recorded prior
accepted target/velocity and alpha columns, never measured physical acceleration.
Eight consecutive recorded command formulas at ticks690..697 already match
targets exactly, with at most1.13e-20rad/s accepted-velocity rounding difference.

Support and negative cases must cover positive integer4ms meshes, explicit
cycle limits, finite/dimension/derived-overflow checks and published command,
progress and existing physical domains. No fractional command-clock policy may
be silently invented. The state excludes previous alpha/b; no command jerk or
progress slew certificate follows. Zero command velocity and physical velocity
alone do not prove stationary equilibrium with a mismatched held target. The
math specialist supplied read-only contract review and no new executions.

Reference source: scripts/phase5/public_coupled_augmented_root_reference.py.
Its pre-forecast source snapshot, rational trace and raw identity are preserved
under results/phase5-reference/root-public-coupled-augmented-predeclaration-20261007.
The forthcoming unit checkpoint must archive and verify this evidence on both
hosts and back up source/review/figures before declaring this unit complete.
