# Phase 2 baseline acceptance protocol

Status: protocol prepared before baseline results. Implementation is blocked until Phase 1 review passes.

## Methods and numerical contracts

Implement model-independent C++ Moore–Penrose and fixed/adaptive DLS with Eigen SVD. An explicit relative SVD rank tolerance belongs in configuration and run metadata. At full rank, DLS uses gains sigma/(sigma squared + lambda squared); lambda=0 must use a separate thresholded pseudoinverse, not divide by zero at rank deficiency. Reject nonfinite, wrong-sized input and negative damping.

Validate Moore–Penrose identities, full-rank solution agreement, exact rank deficiency and a controlled singular-value sweep. Report raw requested joint speed before shared command limiting. DLS is bounded for positive lambda, but may retain task error; do not report bounded motion alone as successful tracking. The thresholded pseudoinverse is also finite at exact rank deficiency and cannot be honestly described as mathematically infinite there.

For real FR3 singularity cases, record the configuration-generation/search rule, seed, actual SVD and desired twist direction. Search a declared number of valid configurations and report the distribution and selected quantile, rather than editing a winning pose by hand. Distinguish unconstrained differential algebra from executed plant behavior.

## Tuning and executed trials

Use common 4 ms control, plant model, desired path, initial state and command adapter. Damping candidates initially span 0.001, 0.003, 0.01, 0.03 and 0.1 in the declared Jacobian scaling convention. Freeze these candidates and selection objective before observing held-out results; if development reveals the range is inappropriate, document the change and repeat the whole development search. A near singularity does not justify selecting an intentionally weak DLS setting.

The adapter records both unconstrained requested dq and accepted/executed motion. A common position/velocity guard may bound execution for both methods; report interventions explicitly so a raw pseudoinverse speed spike is not falsely presented as an unsafe physical command. Keep measured plant q/dq separate from integrated position targets. Initial pose, flange and TCP must match Phase 1 conventions.

Phase 2 is an unconstrained-IK comparison; it does not claim collision avoidance or acceleration/jerk feasibility. Record those gaps rather than silently implying later constraints exist. Model position limits are the common valid intersection of URDF and plant limits. Any velocity limit must have model/config provenance and must apply consistently.

## Gate evidence

- Unit tests for rank, tolerance, damping, dimensions, finite inputs and algebraic agreement.
- Recorded real-robot singularity sweep: sigma_min, condition number, requested joint speed, residual, damping and rank.
- Executed nominal and near-singular reference tracking with position and geodesic orientation error, requested/accepted/executed joint motion, interventions and run completion/failure codes.
- Development tuning table and frozen configuration, with separate evaluation seeds.
- Source/config/model/dependency hashes and actual CSVs, executable regeneration commands, reviewer checks and explicit PASS/FAIL review.

No Phase 2 evidence supports predictive, retiming, null-space or collision research claims.
