# Predictive Redundancy-Aware Motion Control for 7-DoF Manipulators

Status: active development. No comparative research results yet. The complete user specification is preserved in [master_project_prompt.md](source/master_project_prompt.md).

## Research objective

Test whether finite-horizon redundancy selection coupled to online path-progress optimization reduces joint-limit, singularity and collision failures while preserving Cartesian pose accuracy and smooth motion. Success requires repeated, reproducible comparisons; connecting robotics libraries is infrastructure, not the contribution.

The primary application is constrained inspection with a long tool, a three-dimensional inspection curve and prescribed orientation. The primary robot is Franka FR3; first cross-validation robot is KUKA iiwa 14; Kinova Gen3 follows if the mandatory evidence is complete. No hardware motion is in scope.

## Scope and implementation policy

C++ owns rigid-body kinematics, collision queries, baseline controllers, optimization, retiming, simulation integration and ROS runtime. Python owns orchestration, configuration generation, statistics and figures. Robot geometry and physical constants come from versioned external model/configuration files. A model adapter may map names, but algorithm code must not branch on robot identity.

Mandatory comparison methods: Moore–Penrose, DLS, null-space IK, reactive constrained QP, MoveIt Servo, predictive controller with fixed path speed and full predictive controller with retiming. Ruckig smoothing and offline TOPPRA are explicitly separate comparison conditions. Moving obstacles are an extension after static Tier 1–3 validation.

The primary mathematical core must run in tests without ROS launch. Simulator-only contact truth belongs in evaluation and is excluded from controller inputs. Constraints must be evaluated independently against executed states, not merely against the optimizer's linear model.

## Time scales

Control period is 0.004 s (requested 250 Hz). Initial prediction period is 0.04 s, with 20 intervals and 0.8 s preview. The original prompt's 20-step horizon cannot cover 0.5–1 s if its interval is equated with the 4 ms control period. Both periods are separate configuration fields. Every horizon study records both interval count and actual preview duration.

Only the first 4 ms of the optimized input is executed before feedback/replanning. Coarser prediction requires checks/tightening for intersample constraint violations; this remains an explicit algorithm acceptance requirement. Solver timing and complete controller-cycle timing are recorded separately.

## Phase gates

| Gate | Required evidence before proceeding |
|---|---|
| 0: infrastructure | clean C++ build; pinned FR3 loads; simulation steps; deterministic reset; actual ROS state exchange; model visualization; basic CI commands pass locally; dependencies and fetch/build/reset documented |
| 1: kinematics | FK/reference-frame/TCP tests; at least 2,000 random valid Jacobian samples; translational and rotational finite differences; SE(3) log/sign/frame checks |
| 2: basic baselines | executed Moore–Penrose and DLS singularity cases; fair damping selection; logs of tracking and joint motion |
| 3: redundancy | null-space leakage tests; executed joint-margin and singularity cases; multiple indicators |
| 4: reactive control | QP feasibility/bounds/collision-gradient tests; executed constrained scenarios; matched MoveIt Servo protocol |
| 5: prediction and retiming | explicit coupled horizon optimization; numerical model agreement; constraints, failure behavior and intervention lead time measured |
| Research validation | multiple seeds, ablations, horizon study, iiwa validation, timing tails, clean rebuild and figure regeneration; independent audits |

Each gate has a review with scope, executable evidence, known issues, debt, scientific risks and exactly one PASS/FAIL decision. A FAIL blocks the next phase. Later report and final classification are written from actual evidence only. The final classification may be NOT READY, ENGINEERING DEMO, STRONG ENGINEERING PROJECT or RESEARCH-GRADE PROTOTYPE.

## Acceptance measures

Accuracy: position RMSE in metres and geodesic orientation RMSE in radians. Kinematics: scaled and unscaled Jacobian singular indicators and normalized joint margins. Safety: independent minimum self/environment distance, violations and actual contacts. Smoothness: executed velocity/acceleration/jerk, not only commanded quantities. Task: endpoint completion, time, speed, slowdowns and near-stops. Compute: mean, median, p95, p99, maximum and deadline miss rate for solver and full cycle, fallback count and failure codes.

Numerical limits, regression envelopes, sample sizes and baseline tuning budgets are frozen on a development set before held-out comparative trials. Do not choose thresholds or scenarios after looking at which method wins.

## Repository and execution locations

The existing `ros` repository is the project root; an extra `predictive_motion/` directory is unnecessary. Mac owns the canonical source/documentation copy. Dell runs Ubuntu/ROS builds from `/home/codextransfer/predictive_motion` on WSL's native filesystem. Large inputs, model cache and raw experiment outputs live under `D:\CodexTransfer\projects\predictive_motion` with SHA-256 manifests. Neither SSH secrets nor local absolute model/cache paths are part of the research repository.

The Windows D drive is data storage, not a substitute for Linux build storage. WSL virtual capacity is not additional physical free space. Transfer tools preserve partial copies; each result bundle is verified before analysis.
