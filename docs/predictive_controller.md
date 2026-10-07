# Finite-horizon controller: development, acceptance pending

This describes the preserved kinematic core through the 2026-10-07 executor handoff. Its acceleration forecast is not a validated model of the shared position servo (CTRL-001). The command/physical-state correction, separate model validation and current acceptance scope are tracked in [Phase5 status](phase5_development_status.md) and the [independent contract review](../reviews/evidence/predictive_math_specialist_20261007.md). Historical tests below do not establish physical preview accuracy.

The installed `predictive_motion_control::predictive_controller` is model independent C++/Eigen/OSQP. It optimizes every horizon input jointly; it is not repeated reactive IK. For arbitrary n, x=[q(n),v(n),s,r] and u=[a(n),b]. The default mesh is 20 intervals of40ms; feedback/virtual command interval is4ms. Positive nonuniform meshes use their actual durations.

## Exact condensation and objective

Each state is exposed as c_k+M_k z for the entire stacked z=[u_0,...,u_(N-1)]. Condensation eliminates exact affine dynamics, rather than relaxing or ignoring them. Rollout and affine maps are both exposed. Task inputs are explicit scaled SE3 residual, A_q and A_s at each nominal state. Angular residual/Jacobian/path-derivative rows are multiplied by0.3m/rad. Optional local scalar penalties/constraints contain explicit values and gradients. No plant future state is passed to the predictive core.

Stage squared task residual, v, a, jerk and posture terms are accumulated with declared interval weights; initial/intermediate stage k uses h_k, terminal uses h_last. This is the declared discrete node objective, not a claimed exact quadrature. Stage multipliers permit explicit terminal-only analytic fixtures. Progress reward is -w_p*s_N; terminal soft progress cost is w_t*(s_N-1)^2. Terminal v_N=0,r_N=0 is configurable. Every quadratic term H,g,constant and every constraint row label is exposed. No hard s_N=1 assumption makes an unreachable endpoint artificially infeasible.

## Histories, bounds and warm reconstruction

The initial model q/v is measured; persistent accepted q/v is kept separately. The endpoint request is v_measured+dt*a_0. Its actual command acceleration is a_0+(v_measured-v_accepted_previous)/dt. Thus the previous applied model acceleration and previous accepted command acceleration have separate histories, resets and updates. Both nominal jerk and actual command-history jerk are bounded. Direct command acceleration/jerk rows in their own units avoid amplifying a velocity-row acceptance tolerance by1/dt². Accepted history is never reset to measured velocity to erase a violation.

All preview velocities use the same0.0625rad/s software cap as the command supervisor; official physical URDF limits remain separately monitored. Bounds include q/v/a/jerk, monotone0<=s<=1,r>=0, progress speed/acceleration/jerk, local distance/sigma constraints and trust regions. Continuous q/s quadratic extrema are checked exactly. Quadratic Bernstein control points provide conservative interval position bounds; scalar endpoint and midpoint rows use the same local affine distance model. This only certifies that affine model, not true nonlinear geometry.

Warm controls are shifted by actual elapsed virtual command time, e.g.4ms through a40ms cell. Overlap integrals compute mean acceleration over each new interval. States are reconstructed from fresh measurement. The mean preserves velocity increments but generally not the exact old position moment across a switch; the independent analytic case differs by0.000144rad. No entire prediction cell is discarded per feedback tick. Invalid/expired mesh, dimensions or nonfinite controls reset the primal seed. The optional workspace reuses matching sparse structures, updates numerical matrices, and maps finite dual seeds by semantic row identity. A changed structure rebuilds the solver. Such dual seeds are approximate initial guesses; every new problem is re-solved and verified in original units. Failure and explicit supervisor resets discard the workspace.

## Sequential convexification and nonlinear checks

Configured maximum iterations, step termination, trust shrink/minimum and solver/wall/stale limits are explicit. Each candidate is independently checked against exact modeled bounds and true geometry. Rejections shrink joint/progress trust; failure returns no usable controls. The default still retains50ms planner/stale budgets. Solver-only timing is not a command/deadline guarantee.

The adapter uses full original arm hulls and all five tool primitives, four fixtures and floor. An independent Phase5 eight-mm cell/axial cover encloses every original tool primitive with271 spheres; the accepted Phase4 cover/assets remain unchanged. Cell/cap enclosure, source/true-geometry identities, all81 common path poses, point/distance derivatives and its own radial/cap/cell inflation are retained before comparison. The lever bound is recomputed, including cover inflation.

Candidate collision intervals use signed true and conservative cover queries. The global relative point-motion Lipschitz bound is2R*sum(maxabs(v endpoints)); nearest subdivision-node spacing is h/(2*parts), giving a distance deduction R*sum(maxabs(v endpoints))*h/parts, plus explicit roundoff margin. Subdivision refines up to a declared cap and otherwise rejects. Neighboring intervals reuse identical endpoint queries. This does not certify execution/hardware continuous collision safety.

Weighted sigma_min/condition and repeated-minimum/rank flags are logged over the horizon. Classical finite-difference gradients are used only outside the declared nonsmooth region; there the scalar gradient is zero and the soft ascent term is omitted, with the flag retained. True sigma floor checks are sampled and do not claim a continuous singularity certificate. Cartesian and joint-defined path derivatives are independently checked with central finite differences.

## Plant diagnostics and timing

The unchanged common MuJoCo CAD/payload plant is advanced twice at2ms per4ms virtual command. The independent scratch-copy/forward observer checks integration-state immutability, all arm frames/TCP alignment, contacts, clearance, physical q/v/acceleration/jerk after each substep. Model request, persistent accepted target/velocity, both acceleration histories and executed state are distinct columns.

Predictive failure uses the same constrained minimum-velocity stop and validated geometry; a fresh measured capture is taken before its decision. Infeasible/stale/invalid stopping issues no new command and explicitly ends simulation, potentially while still moving. Progress deceleration also preserves its own acceleration/jerk/history/bounds. No universal or hardware stop guarantee is made.

Full-cycle wall timing covers fresh observer/FK, horizon linearization/geometry/SVD derivatives, assembly/setup/solve/validation, command projection/stop/commit, both physics/observers, raw writes, SCP/preview diagnostic writes and stream flush. Final cycles.csv publication is batched after the run and excluded from control-loop timing. This adapter does not run ROS; the ROS-time field is explicitly zero. Deadline misses compare full wall cost with4ms; virtual simulation time does not prove real-time execution.

Paired component methods use the same scene, cap, limit/stop supervision and initial seeds. Predictive progress is adaptive; reactive progress uses a predeclared bounded ramp toward the same maximum speed. The unconstrained quadratic trace is an optimizer diagnostic, not a reactive/fixed-speed trajectory or evidence of reactive superiority. Genuine lead/intervention claims require the separately executed reactive trace and actual future/physical risk evidence. The three-second component duration does not claim full inspection-path completion. Final research seeds0–9 and100–119 remain untouched.

## Executed development evidence so far

Twenty-one predictive tests plus29 prior control cases passed after distinct acceleration histories were introduced. Independent installed consumers validate affine maps and complete costs, separately from production tests.72 adapter derivative checks have maximum joint residual error1.531e-10, path residual error2.309e-10 and sigma directional error2.880e-11; the earlier validation temporary-expression failure is retained.

Online development epochs plant-v1/v2/v3 all retained a first-attempt TIME_LIMIT, feasible common stop and zero progress. Their source/config/binary identities and original source snapshots are preserved. These are real negative results; they are not passed motion trials. Phase5 acceptance and final research/real-time/environment claims remain open.

Coverage qualification: the4mm and8mm grids/slices are not nested. Neither union is asserted to contain the other or to be uniformly more conservative. Each independently encloses the same full physical primitives; cap/radial inflation and distance results must be reported for that cover.

Convexity certificate qualification: a checked Gram factor verifies the actual upper-triangle symmetric solver Hessian with normalized stable Frobenius residual<=1e-12, bounding spectral residual independently of dimension. Per-entry tolerance was unsafe:128/496-dimensional counterexamples are retained and rejected by the corrected guard.

Persistent OSQP workspace now reuses compatible CSC structure, updates numerical matrices/vector data and maps finite prior duals by unique semantic row identity. Failed solver/nonlinear/stale cases reset it. The4ms fractional primal reconstruction remains unchanged; the adapter explicitly clears duals at each feedback advance, rather than claiming an exact fractional dual shift, while retaining compatible matrix storage.


Local model consistency can terminate SCP with a model-consistent feasible
iterate. It does not certify nonlinear stationarity or optimization convergence.
The result and SCP diagnostics identify the termination reason and actual
iteration count; max_iterations is only a ceiling. Preview viability rows and
validation at the issued prefix and terminal separately check fine-feedback
speed continuation. A coarse prediction jerk bound alone is insufficient.

The preserved v14 development motion prefix violates the declared10mm Cartesian
position envelope; see reviews/phase_5_accuracy_qualification.md. Local model
agreement, actual motion and Cartesian tracking accuracy are separate results.
