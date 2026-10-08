# Public coupled affine horizon integration contract

Decision: source contract reviewed; implementation and numerical verification
PENDING. Phase5 NOT_ACCEPTED; Phase6 NOT_STARTED. Prerequisite backup is
d756b8ee662b190010c73637ec05db22b42649e1. This review made no build, model,
forecast or plant call. Existing main and frozen models remain unchanged.

## Existing source findings

Installed predictive.hpp:7–11,45–62 and predictive.cpp:58–75,121–143,198–215
hardcode x=[q,v,s,r], nx=2n+2 and double-integrator A/B. There is no external
general-affine transition API. Generic elimination/full-cost substitution in
scripts/phase5/augmented*_reference.py are mathematical references only.
A separate general-affine library and explicit public-model adapter are needed;
passing n=14 to the old PreviewState would mislabel C/w and preserve wrong dynamics.

Native extension::Map (hpp:10–13) retains both cycle-local and cell-prefix
fields. Result.cell_maps (cpp:60–64) stores the final cycle Map, so .A/.B/
.defect/.origin are last-cycle-local, even in a completed cell entry. Use
.cell_A/.cell_B/.cell_defect/.cell_origin for wholecell transitions and samples.
Probe mapNode(m,true):81/99 normalizes those fields into serialized JSON
A/B/defect/origin. The native and JSON schemas must not be confused.

## Explicit coordinates and provenance

z=[q7,v7,C7,w7,s,r], u=[alpha7,b], nx30, nu8. Each cell has positive integer
cycles m and duration0.004*m seconds, with exactly2*m physical samples.
q/C rad, v/w rad/s, s dimensionless, r1/s; alpha rad/s² and b1/s².
Each cell has its own8 input variables. Measured physical state and accepted
command history are distinct. Alpha is command acceleration, never a renamed
physical acceleration. Full forward/extension success, complete exact roster,
first_uncertified_substep=-1 and nominal map origin/input/endpoint/defect
consistency are prerequisites for a whole-horizon public adapter.
Any failed or unsupported prefix stays diagnostic and refuses full assembly.
No fabricated tail, partial-to-success conversion or double-integrator fallback.
Original source/policy/archived map identity must be pinned in numerical fixtures.
Generic synthetic affine algebra is separately labeled and carries no physical
certificate. Local nominal physical support implies no finite trust radius.

## Actual-coordinate assembly

For cell c: z_next=A_c*z_c+B_c*u_c+d_c, with cumulative cell fields above.
Verify barz_next=A_c*barz_c+B_c*baru_c+d_c with a declared finite arithmetic
tolerance, preserving any discrepancy. Do not silently replace a nonzero
inconsistency with zero. Fixed actual initial state x0 gives o0=x0,M0=0,P0=I.
Let E_c select cell c's8 controls from U. Then
o_next=A_c*o_c+d_c; M_next=A_c*M_c+B_c*E_c; P_next=A_c*P_c.
State z_c=o_c+M_c*U; P is the independent initial sensitivity.
Samples use exactly their cell-prefix A/B/d and the corresponding cell origin:
o_sample=A_prefix*o_c+d_prefix; M_sample=A_prefix*M_c+B_prefix*E_c.
Never compose a cycle-local half map from an arbitrary cell origin, tie controls
across cells, substitute nominal future q/v or reset from nonlinear trial origins.

For X=[z0;...;zN], lifted dynamics L*X=E*U+f have diagonal I, subdiagonal
-A_c, row c+1/control c block B_c and f=[x0;d0;...]. Independent pivoted
elimination must agree with recursive condensed maps and initial sensitivities.
Actual coordinates are authoritative; nominal-centered variables require all
initial, control, residual, linear and constant shifts explicitly retained.

## Complete objective substitution

Use y=[X;U] and y=T*U+t, T=[L^-1*E;I], t=[L^-1*f;0]. A full square-factor
objective is J=.5*||F*y+f0||²+ell^T*y+c0. Rectangular F may contain dense
state/control, crosscomponent and crosscell terms. Let Fc=F*T,fc=F*t+f0.
H=Fc^T*Fc; g=Fc^T*fc+T^T*ell; constant=.5*fc^T*fc+ell^T*t+c0.
Each individual term and the summed objective must retain H/g/constant and
factor/offset. Direct lifted and condensed values, gradients, Hessians and
initial-shift behavior must agree. Comparing only Hessians is insufficient.
Halfstep features first use the exact cell-prefix affine sample expression in
lifted coordinates, then the same embedding. Factors/time weights remain
explicit data, not an implicit retuning or a claim of actual nonlinear cost accuracy.

Future task linearization uses q/s only: ebar+Jq*(q-qbar)+Js*(s-sbar).
Physical velocity uses v; command regularization uses C/w; command acceleration
uses alpha. Actual physical sampled acceleration, if requested, is a v-difference
over0.002s and must be separately labeled. A held alpha changes at cell boundaries
on the actual4ms command lattice; boundary jump jerk divides by0.004s, not a
coarse cell duration. Integration weights are declared for each factor.
The old physical q Bernstein quadratic enclosure does not apply to this
coupled implicit transition. Geometry/intersample bounds, physical effort and
continuation need separate evidence. Terminal v=w=r=0 alone is not stationary
physical equilibrium when C differs from an equilibrium target.

## Frozen numerical verification plan

Before any new adapter numerical output: separate source/build namespace, exact
fixtures/policy/source/binary/compiler/dependency hashes, empty-schema preflight,
then immutable snapshot. Use archived certified startup/nonzero/nonuniform
public maps without new nonlinear model/plant calls, and explicit synthetic
affine fixtures. At least one multicyle cell must detect accidental last-cycle
fields; distinct percell controls must detect tied inputs. Nonzero initial/
nominal/control/desired/history offsets, all state components, rectangular
dense offdiagonal/crosscell factors and linear progress terms must detect
dropped gradient/constants. Keep independent initial perturbations and all
available actual halfsample expressions. Refuse incomplete/uncertified source
packets, inconsistent map origins/defects, malformed shapes/nonfinite/overflow
and falsely asserted scope flags. Freeze exact rosters/types and reject omitted
or fabricated outputs. Root reconstructs lifted elimination and fullcost using
a separate implementation; negative controls include last-cycle substitution,
nominal-reset/tied controls, omitted cross terms/constant/initial shift and fake
full assembly from a failed prefix. No epsilon or outcome tuning after results.

This algebra unit adds no solver/SCP iteration, real command, trust-region
admission, geometry rows, physical feasibility, plant run, untouched holdout,
main integration, task video or timing result. All connecting-segment/ball,
admissibility/execution/safety/uniform-error/controller claims remain false.
The earlier finite-step FD failure remains immutable.

## Producer cross-review clarifications

The independent source writer agrees with this contract. Each sampled initial
sensitivity must also be explicit: P_sample=A_prefix*P_cell_origin. Algebraic
initial shifts leave saved nominal origins/defects and certificate provenance
fixed; a shifted initial is never relabeled physically certified.

If an existing PreviewAssembly::Term is ever imported, its square convention
is w*||m*z+c||² and its stored factor m is unweighted. The new half-square
convention uses F=sqrt(2*w)*m, f0=sqrt(2*w)*c, with linear rewards separate.
No production weights are imported or tuned in this isolated algebra unit.
Command alpha/b boundary history must be the previously accepted alpha/b,
not the old previous_model_acceleration field.
