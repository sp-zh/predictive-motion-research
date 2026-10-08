# Fixed affine horizon and cost algebra review

The first frozen C++ algebra checks pass in their declared component scope. Producer validates 4 positive / 6 refused cases and 14 output mutation controls; root independently validates 4 positive / 8 refused cases and 23 controls. Three malformed-document processes each return exit 1 without creating an output. Inputs, reference formulas, arithmetic gates and compiled binary remain unchanged. No original Model, plant, solver, main controller or scorer is called. Phase5 remains **NOT_ACCEPTED**.

## What was verified

The separate namespace assembles z=[q,v,C,w,s,r] with 30 coordinates and distinct 8-coordinate [alpha,b] inputs per cell. For z_(k+1)=A_k z_k+B_k u_k+d_k, recursive offsets/control maps/initial sensitivities agree with independently pivoted lifted L/E/f/initial selector elimination. Every 2ms sample retains cumulative actual-coordinate propagation and initial sensitivity. Shifted initial coordinates never reset to source nominal future states.

Full factors over y=[z0…zN;U], factor offsets, linear terms and constants survive substitution y=T U+t. The factor, H/g/constant, direct value, gradient and Hessian checks include canonical ordered term sums, empty terms and cross blocks. Serialized raw H is preserved; derivative calculations use its symmetric part. These are declared algebra-test coefficients, not production research weights.

Cached public state/map carriers keep last-cycle-local fields distinct from wholecell cumulative fields. Actual native normalization matches the saved JSON matrices. This tests the archived carrier contract and never constructs or rolls out the physical Model. Authentic failed/unsupported source records retain original flags, values, prefixes and errors, with no fabricated complete future.

## Evidence and figures

[Root review and limits](evidence/public_affine_horizon_algebra_root_review_20261008.json), [root first-attempt audit](evidence/public_affine_horizon_root_audit_20261008.json), [producer verification](evidence/public_affine_horizon_producer_verification_20261008.json), [verified immutable checkpoint locations](evidence/public_affine_horizon_algebra_checkpoint_20261008.json).

[Figure provenance](evidence/public_affine_horizon_root_figures_20261008.json) records the exact validated data and renderer hashes. The inspected PNG/SVGs show check categories, distinct progress-acceleration columns in the 40ms nonuniform N4 mesh, and full-versus-condensed objective agreement. The initial crowded-axis rendering is retained as visual QA; only ticks changed in the final rendering. Neither rendering runs the kernel or a robot.

## Acceptance boundary

Public source fixtures cover N1/N4; generic fixtures cover N2/N3. This does not accept the project 20-cell / .8s / 1.5s horizon, a fresh nonlinear forecast, a finite perturbation radius, admissibility, safety, controller readiness, timing, stopping or a complete task. Root's negative initial progress-speed shift is an algebra coordinate, not a physically admitted state. The earlier finite-step friction-branch FD failure remains retained and is not replaced by these algebra results. Main physical/accepted-command integration and subsequent independent gates remain pending.
