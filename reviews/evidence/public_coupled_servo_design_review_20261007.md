# Public dynamics availability and coupled servo design

Verdict: **PUBLIC_MODEL_ROUTE_AVAILABLE; PREDICTION_ACCURACY_UNVALIDATED**. A reproducible, current-state causal coupled candidate can be built from the public simulation MJCF and static compiled parameters. This review does not expand soft-v2's domain or reverse its retained failures. The reported v3 reference/stop success and short-horizon prediction failure remain distinct; v3 and previously seen 91012 outputs cannot become a fresh holdout by changing the predictor. No fitting, `mjData`, `mj_forward`, `mj_step`, plant commands, or prediction accuracy scan occurred here.

## Actual available entry point

On Dell, source `/opt/ros/jazzy/setup.bash` before importing `pinocchio`; unsourced system Python cannot find it. Version 4.1.0 provides `buildModelFromMJCF` and the corresponding C++ parser. Direct import of `/home/codextransfer/predictive_motion/experiments/generated/inspection/inspection_fr3.xml` succeeded with seven hinge coordinates/velocities and named joints in command order. The importer exposes armature, damping, friction and merges the fixed inspection tool into joint 7: inertial mass increases from `.627143` to `1.077143` kg. Its public parser describes these fields. [Pinocchio 4.1 parser](https://github.com/stack-of-tasks/pinocchio/blob/v4.1.0/include/pinocchio/src/parsers/mjcf/mjcf-graph.hxx).

The existing `RobotKinematics::Impl` instead privately builds/reduces the arm URDF and exposes poses/Jacobians, without a public M/g/bias API. Current configuration has `fixed_joint_positions: {}` and retains all seven arm joints. Other URDF variants require explicit finger lock positions, with locked inertias included in reduction. `world_T_base` and `flange_T_tcp` are geometric transforms; the TCP offset does not append payload inertia. Current arm URDF has zero armature and no inspection tool. The hand URDF would add a different inertial assembly. It is unsuitable as a silent substitute for simulation dynamics.

Prefer an independent dynamics object imported from the simulation's MJCF, not changing common physics. `pin.crba(model,data,q)` already adds `model.armature` in the installed 4.1 header; symmetrize its upper triangle and **do not add armature again**. `computeGeneralizedGravity` and `nonLinearEffects` evaluate public nominal dynamics. World gravity/base orientation, joint ordering, locked coordinates, inertial transforms and actual payload must match. The imported model is an available candidate representation; no state-dependent MuJoCo mass-matrix equality was checked because future/state-derived MuJoCo calls were prohibited.

## One public nominal calculation

The [read-only audit](../../scripts/phase5/audit_public_coupled_servo_model.py) loads only `mjModel` constants through `mj_loadXML`, and separately evaluates Pinocchio M/g/bias at public home `q=(0,0,0,-1.57079,0,1.57079,-.7853)` and a declared small nominal velocity. It never creates `mjData`. Actual source hashes and full arrays are retained in [JSON](public_coupled_servo_design_review_20261007.json).

Compiled model: MuJoCo 3.3.7, 2 ms, implicitfast, Newton, 100 iterations, tolerance `1e-8`, gravity `(0,0,-9.81)`, no disabled physics flags, zero body gravity compensation. Armature is `(.195,.195,.195,.195,.074,.074,.074)`, passive damping `.21`; friction bounds are `(1.137,1.137,1.137,1.137,.763,.44,.248)` N·m. Direct actuator gear is one; gains are `(4500,4500,3500,3500,2000,2000,2000)` and velocity bias gains `(450,450,350,350,200,200,200)`. Joint actuator force bounds are ±87 N·m on joints 1–4 and ±12 on 5–7. Read current compiled control ranges rather than assuming unconstrained target input.

At this one nominal configuration, inspection-MJCF M has eigenvalues `.0742563…3.5387014`, maximum off-diagonal `1.3390674` kg·m²; inverse M maximum off-diagonal is `2.1838950`. Its maximum absolute M difference from arm URDF is `.3495983`, from vendor MJCF without the inspection payload `.1545972`. Tool gravity changes joint 2 from about `-25.99966` to `-28.44750` N·m. These are public-model algebra differences, not observed prediction improvements.

## Coupled equations and engine order

Let `M(q)` include armature, `W=M^-1`, `tau_smooth` include actuator force, passive damping, negative rigid-body bias, and any declared applied force. In the contact/limit/equality-free regime with seven dof-friction rows, constraint Jacobian is identity. Frozen default friction parameters give impedance `d=.9`, `solref=(.02,1)`, `solimp=(.9,.95,.001,.5,2)` and `B=2/(.95*.02)=105.2631579 s^-1`. The friction regularizer uses **static `dof_invweight0`**, not the current diagonal of W and not scalar fitted masses:

\[
R_i=\max(mjMINVAL, (1-d_i)/d_i\;invweight0_i),\quad
H=W+\operatorname{diag}(R),\quad
\ell=W\tau_{smooth}+Bv,
\]
\[
f^*=\arg\min_{-\eta\le f\le\eta}\tfrac12 f^THf+\ell^Tf.
\]

`f` has torque units; `Hf` and `ell` have acceleration units. The nominal H is positive definite, eigenvalues `.4057551…14.9630800`; this checks a well-defined local box QP, not model accuracy. Off-diagonal W requires a coupled solve: clipping seven unconstrained components independently generally fails KKT. The regularizer, friction reference acceleration and box branches follow [3.3.7 constraint source](https://github.com/google-deepmind/mujoco/blob/3.3.7/src/engine/engine_core_constraint.c), with solver force semantics in [3.3.7 solver source](https://github.com/google-deepmind/mujoco/blob/3.3.7/src/engine/engine_solver.c).

The subsequent velocity update uses `M-h*qDeriv`, **not** the mass matrix in the friction QP. For the present direct affine position actuators/passive damping and no other velocity-dependent passive effects, implicitfast yields `qDeriv=-diag(kv+.21)` while excluding the velocity derivative of rigid-body bias. Thus

\[
v^+=v+h(M+hD)^{-1}(\tau_{smooth}+f^*),\quad q^+=q+hv^+.
\]

`tau_smooth` itself still includes full current rigid-body bias, including Coriolis. Force/control clipping must match the actual interface. The 3.3.7 actuator derivative routine directly uses the affine `biasprm[2]` even when forces are clamped: matching that integrator approximation must not silently replace it with the ordinary derivative of a clipped-force function. Constraint forces are solved before integration, and their derivative is absent from this implicit matrix. [3.3.7 forward/integration source](https://github.com/google-deepmind/mujoco/blob/3.3.7/src/engine/engine_forward.c), [3.3.7 velocity derivative source](https://github.com/google-deepmind/mujoco/blob/3.3.7/src/engine/engine_derivative.c).

This is a candidate contact-free equation sequence consistent with those engine components, not an exact-engine claim. Other constraints change J/H; finite Newton termination and warmstart can change numerical results. Parser/compiler inertia differences, omitted forces, saturation semantics and state acquisition can also remain relevant. A coupled physical surrogate must declare these assumptions rather than rename the old scalar empirical formula “exact”.

For derivatives within a fixed friction active set, saturated `f_B` is fixed and `H_FF f_F=-ell_F-H_FB f_B`; differentiating this linear system preserves coupling. Active-set boundaries do not have a unique ordinary derivative. Freeze a branch convention and check sensitivities independently before MPC use.

## Causal state and identifiability limits

The forecast needs measured q/v at its start, accepted target c and command histories w/alpha, joint/base mapping, payload, force/control limits and public model identity. For these instantaneous position actuators no latent activation state is indicated by the XML; a changed actuator/filter would require its observable initial state. Unknown applied/contact forces cannot be replaced by privileged future `mjData`. Subsequent M/bias computations may use the predictor's own q/v, and each 4 ms accepted command target is held for two 2 ms physical-model updates. No future measured q/v may reset intermediate predictions.

A defensible next step is to freeze public coupled M/bias and the measured actuator/passive/friction constants, then inspect residuals on **old training only** for small explicitly declared mismatch terms. Narrow, low-speed single-pose excitation cannot identify arbitrary coupled inertia, gravity, damping and friction corrections independently: saturated friction often identifies a bound, while interior behavior combines M and R. Avoid replacing physical inertia with seven free effective scalars or using validation failure to tune correction order. Any eventual fitting needs training-only model selection and a separately frozen fresh prospective protocol/holdout. This design review establishes availability and equations only; it neither predicts that the new candidate will pass nor authorizes domain enlargement.
