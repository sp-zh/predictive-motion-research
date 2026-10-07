# MASTER PROJECT PROMPT

## Predictive Redundancy-Aware Motion Control for 7-DoF Manipulators

You are acting as the lead robotics research engineer, control engineer, simulation engineer, and independent technical reviewer for this project.

Your task is to build a complete, research-grade, reproducible robotics project centered on:

**Predictive redundancy resolution, future constraint prediction, and online motion retiming for redundant manipulators.**

This must NOT become a simple ROS / MoveIt / MuJoCo integration demo.

The project must contain:

- professional robot models;
- parametric CAD;
- robot kinematics;
- differential inverse kinematics;
- redundancy resolution;
- singularity analysis;
- joint-limit handling;
- collision constraints;
- real-time constrained optimization;
- predictive motion control;
- online trajectory retiming;
- ROS 2 integration;
- MuJoCo simulation;
- systematic benchmarks;
- quantitative comparisons;
- ablation studies;
- cross-robot validation;
- automated testing;
- continuous integration;
- reproducible experiments;
- scientific and engineering review.

The final repository must be credible as both:

1. a high-quality robotics engineering portfolio project;
2. the basis of a research paper or undergraduate research project.

---

# 0. PROJECT PRINCIPLE

The core contribution is NOT:

- FK;
- IK;
- using MoveIt;
- using MuJoCo;
- using Pinocchio;
- using Ruckig;
- using OSQP;
- connecting ROS packages.

Those are infrastructure.

The project's own contribution must be centered around:

## Core contribution A
**Predictive redundancy resolution**

Instead of selecting joint motion only from the current robot configuration, predict a finite future horizon and choose redundancy configurations that reduce future risk.

## Core contribution B
**Future constraint prediction**

Predict impending:

- joint-limit violations;
- singularity proximity;
- self-collision;
- environment collision;
- velocity-limit violations;
- acceleration-limit violations;
- jerk-limit violations.

The controller should take preventive action BEFORE these constraints become critical.

## Core contribution C
**Online path-progress / motion retiming**

The controller should optimize not only robot posture but also how quickly the robot progresses along the task path.

When risk increases:

- reduce path speed smoothly;
- use redundancy to recover a better configuration;
- restore speed when conditions improve.

The system should avoid unnecessary stopping whenever feasible.

## Core contribution D
**Reproducible benchmark framework**

The project must provide a standardized way to quantitatively compare:

- pseudoinverse IK;
- damped least-squares IK;
- null-space redundancy control;
- reactive constrained QP;
- MoveIt Servo;
- predictive controller;
- full proposed predictive + retiming method.

---

# 1. RESEARCH QUESTION

The main research question is:

> Can predictive redundancy resolution and online path retiming reduce singularity, joint-limit, and collision failures while maintaining smooth and accurate Cartesian motion compared with reactive kinematic controllers?

Secondary research questions:

### RQ1
Does predictive redundancy resolution reduce joint-limit and singularity failures compared with reactive methods?

### RQ2
Can redundancy resolution and path retiming be jointly optimized while preserving Cartesian tracking accuracy?

### RQ3
Does previewing future constraints reduce emergency slowdown and unnecessary stopping?

### RQ4
How much additional computation does predictive control require compared with reactive QP and MoveIt Servo?

### RQ5
Does the method generalize across multiple 7-DoF manipulators?

---

# 2. ROBOTS

Primary robot:

**Franka FR3**

Cross-validation robots:

- KUKA iiwa 14
- Kinova Gen3

Prefer high-quality open robot descriptions, including official descriptions or MuJoCo Menagerie where appropriate.

Do not manually recreate robot geometry if a trustworthy open-source model already exists.

The algorithm must be robot-agnostic.

Robot-specific constants must come from configuration/model files rather than hard-coded logic.

The controller must not contain logic such as:

```cpp
if (robot == "fr3") {
    ...
}
```

unless there is a genuinely unavoidable hardware-specific adapter layer.

---

# 3. SOFTWARE STACK

Prefer open-source professional robotics tools.

Target stack:

- Ubuntu 24.04
- ROS 2
- MuJoCo
- Pinocchio
- MoveIt 2
- MoveIt Servo
- OSQP
- Ruckig
- TOPPRA
- FreeCAD
- RViz
- rosbag2
- Eigen
- C++
- Python
- NumPy
- Pandas
- Matplotlib
- pytest
- GTest
- Docker / Dev Container
- GitHub Actions

Before implementation:

1. inspect the current environment;
2. verify currently supported mutually compatible versions;
3. document selected versions;
4. prefer stable combinations over blindly choosing the newest release;
5. pin important dependencies where practical.

Create:

`docs/dependency_matrix.md`

It must describe:

- selected version;
- reason;
- compatibility;
- source;
- known limitations.

Do not silently change major dependencies later.

---

# 4. LANGUAGE POLICY

Use C++ for runtime robotics components:

- kinematics;
- SE(3) operations;
- Jacobian computation;
- QP;
- predictive control;
- trajectory control;
- ROS runtime nodes;
- collision processing;
- real-time loop.

Use Python primarily for:

- benchmark orchestration;
- scenario generation;
- offline analysis;
- statistics;
- plotting;
- experiment aggregation;
- notebooks where useful.

Do not implement the entire robotics stack in Python merely because it is faster to prototype.

---

# 5. APPLICATION SCENARIO

The primary scenario is:

## Constrained Robotic Inspection

The robot carries a relatively long inspection tool.

The tool tip must follow a prescribed three-dimensional surface or inspection curve while maintaining a required tool orientation.

Reference path:

\[
T_d(s)\in SE(3),\quad s\in[0,1]
\]

where \(s\) is path progress.

The robot must track:

- TCP position;
- TCP orientation.

The environment includes fixtures/workpieces that create realistic geometric constraints.

This application should naturally generate:

- redundancy decisions;
- elbow-clearance problems;
- wrist singularity risks;
- joint-limit traps;
- collision risks;
- varying feasible motion speeds.

Do not make the benchmark only consist of an unconstrained robot drawing a circle in empty space.

---

# 6. PARAMETRIC CAD

Use FreeCAD or its Python API to create a project-specific parametric inspection tool and test workpiece.

Do not redesign the FR3 itself.

Create:

## Tool

A modular inspection tool including:

- robot flange adapter;
- elongated tool shaft;
- sensor/tool body;
- tool tip;
- optional camera/sensor bracket;
- simplified collision geometry.

Parameterize at least:

- tool length;
- shaft radius;
- sensor-body dimensions;
- TCP offset.

Example parameters:

```yaml
tool:
  length: 0.30
  shaft_radius: 0.015
  tcp_offset: [0.0, 0.0, 0.32]
```

## Workpiece

Create a simple but meaningful inspection fixture/workpiece with:

- narrow regions;
- nearby obstacles;
- regions that constrain elbow posture;
- a defined inspection path.

Prefer generating CAD reproducibly through scripts when possible.

Export:

- STEP;
- STL or other mesh;
- collision mesh;
- visual mesh.

Store source CAD/scripts in:

`cad/`

Do not commit only exported STL files without parametric source.

---

# 7. REPOSITORY STRUCTURE

Create or migrate toward a structure similar to:

```text
predictive_motion/
├── README.md
├── LICENSE
├── CITATION.cff
├── THIRD_PARTY_NOTICES.md
│
├── docs/
│   ├── project_spec.md
│   ├── architecture.md
│   ├── mathematics.md
│   ├── dependency_matrix.md
│   ├── experiment_protocol.md
│   ├── benchmark_definition.md
│   └── report.md
│
├── cad/
│   ├── source/
│   ├── scripts/
│   ├── step/
│   └── meshes/
│
├── src/
│   ├── predictive_motion_description/
│   ├── predictive_motion_sim/
│   ├── predictive_motion_kinematics/
│   ├── predictive_motion_baselines/
│   ├── predictive_motion_qp/
│   ├── predictive_motion_predictive/
│   ├── predictive_motion_retiming/
│   ├── predictive_motion_tasks/
│   ├── predictive_motion_benchmark/
│   └── predictive_motion_bringup/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   └── numerical/
│
├── benchmarks/
│   ├── configs/
│   ├── scenarios/
│   ├── seeds/
│   └── reference/
│
├── experiments/
│   └── generated/
│
├── analysis/
│   ├── scripts/
│   └── notebooks/
│
├── figures/
├── results/
├── reviews/
├── docker/
└── .github/
    └── workflows/
```

Adjust only where there is a clear architectural justification.

---

# 8. SYSTEM ARCHITECTURE

Target architecture:

```text
Task / Inspection Path
          |
          v
SE(3) Reference Generator
          |
          v
Predictive Motion Controller
 ├── task tracking
 ├── redundancy resolution
 ├── future joint-limit prediction
 ├── future singularity prediction
 ├── future collision prediction
 └── path-progress optimization
          |
          v
Joint command trajectory
          |
          v
MuJoCo plant
          |
          +------------------+
          |                  |
          v                  v
      joint state      collision state
          |                  |
          +---------+--------+
                    |
                    v
             controller
```

Keep these layers clearly separated:

- robot model;
- simulation plant;
- controller model;
- reference generation;
- benchmark orchestration;
- metrics;
- visualization.

Do not let the controller read privileged simulator information that would not realistically be available from a robot model/state estimator.

---

# 9. CONTROL FREQUENCY

Initial runtime target:

**250 Hz**

Target control period:

\[
\Delta t = 4\,ms
\]

Do not claim real-time performance merely because the mean solve time is under 4 ms.

Report at least:

- mean;
- median;
- p95;
- p99;
- maximum;
- deadline miss rate.

If 250 Hz proves unrealistic for the predictive controller, investigate and optimize before lowering the target.

If the final system must use a lower frequency, document the reason quantitatively.

---

# 10. PHASE 0 — ENVIRONMENT AND REPRODUCIBILITY

Before algorithm development:

- create build instructions;
- create container/devcontainer where practical;
- establish ROS workspace;
- integrate FR3 model;
- launch MuJoCo;
- visualize model;
- confirm joint state exchange;
- establish reproducible simulation reset;
- establish deterministic random seeds.

Create:

`docs/reproducibility.md`

A fresh environment must be able to reproduce the core benchmark following documented steps.

### Phase 0 acceptance gate

Do not proceed until:

- repository builds;
- robot model loads;
- simulation runs;
- deterministic reset works;
- basic CI works;
- dependencies are documented.

Create:

`reviews/phase_0_review.md`

with explicit:

`PASS` or `FAIL`.

---

# 11. PHASE 1 — KINEMATICS VALIDATION

Implement / integrate:

- forward kinematics;
- frame transforms;
- Jacobian;
- joint limits;
- SE(3) pose error;
- TCP handling.

Use Pinocchio as the primary rigid-body kinematics engine.

Do not simply trust library output.

Perform numerical validation.

## Jacobian verification

For many random valid configurations compare analytical/library Jacobian against finite differences.

Example:

\[
J_{\text{analytic}}
\approx
J_{\text{finite difference}}
\]

Use at least thousands of random samples.

Report:

- absolute error;
- relative error;
- worst case;
- distribution.

Test translational and rotational components correctly.

Be careful with:

- WORLD;
- LOCAL;
- LOCAL_WORLD_ALIGNED;
- frame conventions;
- quaternion ordering;
- body vs spatial twists.

## SE(3) error

Define a mathematically consistent pose error, preferably through Lie-group methods:

\[
e =
\log\left(T(q)^{-1}T_d\right)^\vee
\]

Document exact convention.

### Phase 1 acceptance gate

Require:

- FK tests;
- Jacobian numerical tests;
- SE(3) consistency tests;
- reference-frame tests;
- random configuration tests.

No unexplained coordinate-frame hacks.

Create:

`reviews/phase_1_review.md`

---

# 12. PHASE 2 — BASIC IK BASELINES

Implement:

## Baseline A — Moore-Penrose pseudoinverse

\[
\dot q = J^\dagger v_d
\]

## Baseline B — Damped least squares

\[
\dot q
=
J^T
(JJ^T+\lambda^2I)^{-1}v_d
\]

Allow fixed and optionally adaptive damping.

Construct controlled singularity tests and record:

- minimum singular value;
- joint velocity;
- Cartesian tracking error;
- damping;
- condition number.

Demonstrate the expected instability of naive pseudoinverse near singularities and bounded behavior of DLS.

Do not tune baselines deliberately poorly.

---

# 13. PHASE 3 — REDUNDANCY RESOLUTION

Implement null-space control:

\[
\dot q =
J^\dagger v_d+
(I-J^\dagger J)z
\]

Support multiple null-space objectives.

## Joint-limit objective

Example form:

\[
H_{joint}(q)
=
\sum_i
\left(
\frac{q_i-q_{mid,i}}
{q_{max,i}-q_{min,i}}
\right)^2
\]

Use:

\[
z=-k\nabla H
\]

## Manipulability

Calculate at least:

\[
w(q)=\sqrt{\det(JJ^T)}
\]

and:

\[
\sigma_{\min}(J)
\]

and condition number:

\[
\kappa(J)
=
\frac{\sigma_{\max}}
{\sigma_{\min}}
\]

Do not rely on manipulability alone because it may be numerically misleading near certain configurations.

Store multiple singularity indicators.

### Phase 3 tests

Verify that null-space commands approximately satisfy:

\[
J(I-J^\dagger J)z\approx0
\]

within numerical tolerance.

---

# 14. PHASE 4 — REACTIVE CONSTRAINED QP

Build a reactive differential-IK controller using OSQP.

Base problem:

\[
\min_{\dot q}
\frac12
\|J\dot q-v_d\|_Q^2
+
\frac{\lambda}{2}\|\dot q\|^2
+
C(q,\dot q)
\]

subject to constraints.

## Joint position

Predict one-step position:

\[
q_{k+1}=q_k+\dot q_k\Delta t
\]

and enforce:

\[
q_{min}+m_q
\le q_{k+1}
\le q_{max}-m_q
\]

## Joint velocity

\[
-\dot q_{max}
\le
\dot q
\le
\dot q_{max}
\]

## Collision constraints

Use signed-distance or minimum-distance information.

Linearize where required:

\[
d(q+\Delta q)
\approx
d(q)
+
\nabla_q d(q)^T\Delta q
\]

Require:

\[
d(q)\ge d_{safe}
\]

or use velocity-damper style constraints.

The precise formulation must be documented.

## Singularity handling

Use either:

- a suitable cost;
- adaptive damping;
- singularity-related constraints;
- or a justified combination.

Do not pretend manipulability is convex.

Document approximations honestly.

---

# 15. MOVEIT SERVO BASELINE

Integrate MoveIt Servo as an external strong baseline.

Use comparable:

- Cartesian commands;
- joint limits;
- robot model;
- scenes;
- task trajectories;
- controller frequencies where possible.

Do not compare against MoveIt Servo under intentionally unfavorable settings.

Document configuration in:

`docs/baselines/moveit_servo.md`

The benchmark must make clear which functionality is:

- provided by MoveIt;
- implemented by this project.

---

# 16. PHASE 5 — PREDICTIVE CONTROLLER

This is the primary research component.

Do NOT merely execute the reactive QP multiple times.

Use an explicit finite prediction horizon.

Define state:

\[
x_k=
\begin{bmatrix}
q_k\\
\dot q_k\\
s_k\\
\dot s_k
\end{bmatrix}
\]

where:

- \(q\): joint position;
- \(\dot q\): joint velocity;
- \(s\): task-path progress;
- \(\dot s\): task-path speed.

Possible control variable:

\[
u_k=
\begin{bmatrix}
\ddot q_k\\
\ddot s_k
\end{bmatrix}
\]

Use discrete kinematics:

\[
q_{k+1}
=
q_k+\dot q_k\Delta t
+\frac12\ddot q_k\Delta t^2
\]

\[
\dot q_{k+1}
=
\dot q_k+\ddot q_k\Delta t
\]

and corresponding dynamics for \(s\).

Initial nominal horizon:

\[
N=20
\]

with approximately:

\[
0.5-1.0\,s
\]

preview.

Treat these as configurable, not hard-coded.

---

# 17. PREDICTIVE TASK TRACKING

Reference path:

\[
T_d(s)
\]

Predicted robot pose:

\[
T(q_k)
\]

Task error:

\[
e_k=
\log
\left(
T(q_k)^{-1}
T_d(s_k)
\right)^\vee
\]

The predictive optimization should account for future Cartesian error.

Because this introduces nonlinearity, implement a clearly documented strategy such as:

- local linearization;
- sequential convex programming;
- iterative QP;
- another justified approximation.

Do NOT falsely call a nonlinear problem a convex QP if nonlinear quantities are simply ignored.

If sequential convexification is used:

- expose maximum iterations;
- convergence thresholds;
- trust-region handling if needed;
- solver failure behavior.

---

# 18. PREDICTIVE OBJECTIVE

A representative objective is:

\[
J
=
\sum_{k=0}^{N}
[
e_k^TQe_k
+
w_v\|\dot q_k\|^2
+
w_a\|\ddot q_k\|^2
+
w_j\|j_k\|^2
\]

\[
+
w_lC_{joint}(q_k)
+
w_sC_{sing}(q_k)
+
w_cC_{collision}(q_k)
-
w_p\dot s_k
]
\]

Interpretation:

- minimize task error;
- avoid excessive joint motion;
- avoid excessive acceleration;
- suppress jerk;
- preserve joint-limit margin;
- avoid singularity;
- maintain collision clearance;
- maximize safe task progress.

Do not use this exact formulation blindly if numerical testing shows a better formulation.

Any modification must be documented mathematically.

---

# 19. PREDICTIVE CONSTRAINTS

At minimum investigate:

## Joint position

\[
q_{min}
\le q_k\le
q_{max}
\]

## Joint velocity

\[
|\dot q_k|
\le
\dot q_{max}
\]

## Joint acceleration

\[
|\ddot q_k|
\le
\ddot q_{max}
\]

## Jerk

\[
|j_k|
\le
j_{max}
\]

## Collision

\[
d_j(q_k)
\ge
d_{safe}
\]

for relevant robot/environment and self-collision pairs.

## Path progress

\[
0\le s_k\le1
\]

\[
\dot s_k\ge0
\]

unless a benchmark explicitly allows reversing.

---

# 20. FUTURE SINGULARITY PREDICTION

Predict quantities such as:

\[
\sigma_{\min}(J(q_k))
\]

and/or:

\[
\kappa(J(q_k))
\]

across the horizon.

Do not blindly impose nonconvex hard constraints unless the solver formulation supports them reliably.

Potential approaches include:

- soft penalties;
- local gradient approximations;
- predictive damping;
- constraint tightening;
- terminal costs;
- posture costs.

Compare alternatives if practical.

The system should demonstrate cases where:

1. current configuration is safe;
2. future trajectory approaches a singularity;
3. the predictive controller begins modifying posture before the reactive controller would.

---

# 21. FUTURE JOINT-LIMIT PREDICTION

Create scenarios where a locally reasonable IK decision leads to an unavoidable joint-limit problem several hundred milliseconds later.

The predictive algorithm must be capable of choosing a different redundancy solution early enough to avoid the trap.

This experiment is one of the project's primary demonstrations.

---

# 22. FUTURE COLLISION PREDICTION

Use predicted configurations to evaluate future clearance.

The algorithm should preferably alter:

- elbow posture;
- wrist posture;
- path speed;

before a collision-avoidance emergency is required.

Avoid claiming "collision avoidance" merely from one-step distance constraints.

Clearly distinguish:

- reactive collision avoidance;
- horizon-based predictive collision avoidance.

---

# 23. ONLINE PATH RETIMING

Path progress \(s(t)\) must be a meaningful part of the controller.

When future constraints become restrictive:

\[
\dot s \downarrow
\]

When configuration improves:

\[
\dot s \uparrow
\]

The controller should avoid binary stop/go behavior if smooth slowdown is feasible.

Evaluate:

- completion time;
- minimum speed;
- number of near-stops;
- jerk;
- tracking error.

---

# 24. RUCKIG

Integrate Ruckig as a baseline / smoothing solution for jerk-limited state-to-state motion.

Use it to create a meaningful comparison against the project's native predictive retiming.

Example comparison:

### Method 1
Reactive QP + Ruckig smoothing

### Method 2
Predictive redundancy controller + Ruckig

### Method 3
Proposed predictive controller with path-progress and jerk handling integrated into the optimization

Do not claim superiority without benchmark evidence.

---

# 25. TOPPRA

Use TOPPRA as an offline time-parameterization baseline for fixed paths where appropriate.

Clearly separate:

- offline known-path retiming;
- online reactive retiming;
- predictive online path-progress optimization.

Do not compare algorithms solving fundamentally different problems without explaining the distinction.

---

# 26. PRIMARY BENCHMARK METHODS

At minimum compare:

1. Moore-Penrose pseudoinverse
2. Damped least squares
3. Null-space redundancy IK
4. Reactive constrained QP
5. MoveIt Servo
6. Predictive controller without adaptive retiming
7. Full predictive redundancy + retiming method

If feasible:

8. Reactive QP + Ruckig
9. TOPPRA on fixed-path experiments

---

# 27. BENCHMARK A — SINGULARITY FUNNEL

Create a task that forces the manipulator toward a poor-conditioning region unless redundancy is handled intelligently.

Record:

- Cartesian position RMSE;
- orientation RMSE;
- minimum singular value;
- maximum condition number;
- maximum joint velocity;
- minimum joint-limit margin;
- task completion;
- solve time.

The predictive method should be evaluated on whether it changes configuration BEFORE severe degradation occurs.

---

# 28. BENCHMARK B — JOINT-LIMIT TRAP

Design a reference path where:

- several redundancy choices initially appear valid;
- the reactive solution drifts toward a joint limit;
- later path segments become infeasible or require emergency correction.

Measure:

- minimum limit margin;
- limit interventions;
- emergency slowdown;
- completion;
- tracking error;
- task time.

This benchmark must be visually understandable and quantitatively rigorous.

---

# 29. BENCHMARK C — CONSTRAINED INSPECTION WORKSPACE

Use the CAD fixture/workpiece.

Require the tool tip to follow the inspection curve while maintaining tool orientation.

Some arm configurations should produce:

- elbow collision;
- wrist collision;
- self-collision;
- poor joint-limit margin.

Measure:

- minimum distance;
- collision count;
- path tracking;
- orientation tracking;
- completion time;
- path-progress profile.

---

# 30. BENCHMARK D — HIGH-SPEED 3D TOOLPATH

Use multiple paths:

- circle;
- helix;
- figure-eight;
- spline;
- high-curvature toolpath.

Measure:

- position RMSE;
- orientation RMSE;
- peak velocity;
- peak acceleration;
- peak jerk;
- path completion time;
- solver performance.

---

# 31. BENCHMARK E — ONLINE TARGET / PATH CHANGE

Change the target while the robot is already moving.

Measure:

- response latency;
- peak jerk;
- overshoot;
- Cartesian tracking error;
- solver stability;
- emergency stop events.

---

# 32. BENCHMARK F — MOVING OBSTACLE

After the static system is reliable, introduce predictable moving obstacles.

Initially provide perfect obstacle trajectory information.

Only after that works should uncertainty be optionally introduced.

Evaluate whether the predictive controller reacts earlier and more smoothly than reactive baselines.

This is an extension, not a prerequisite for the first valid research result.

---

# 33. BENCHMARK G — COMBINED STRESS TEST

Combine:

- higher motion speed;
- singularity risk;
- joint-limit risk;
- obstacle proximity;
- target/path change.

Do not tune solely for this scenario.

Use it as a final integrated demonstration.

---

# 34. METRICS

Every benchmark should report relevant subsets of:

## Accuracy

\[
RMSE_p
\]

Cartesian position RMSE.

\[
RMSE_R
\]

orientation error.

## Kinematics

- minimum \(\sigma_{\min}(J)\);
- maximum condition number;
- manipulability where useful;
- minimum joint-limit margin.

## Safety

- minimum environment clearance;
- minimum self-collision clearance;
- collision count;
- safety-margin violations.

## Smoothness

- RMS acceleration;
- peak acceleration;
- RMS jerk;
- peak jerk.

## Task performance

- task completion;
- completion time;
- mean path speed;
- slowdown duration;
- full stop count.

## Optimization

- mean solve time;
- median solve time;
- p95;
- p99;
- worst-case;
- iterations;
- solver failures;
- deadline misses.

## Robustness

- success rate across seeds;
- success rate across initial configurations;
- success rate across task variations.

---

# 35. EXPERIMENT REPLICATION

For important experiments, do not rely on one hand-selected run.

Use multiple:

- initial configurations;
- task variants;
- obstacle positions;
- random seeds;
- trajectory speeds.

Store seeds explicitly.

Report distributions rather than only cherry-picked examples.

Visual demo cases may be selected for clarity, but quantitative conclusions must come from systematic trials.

---

# 36. BENCHMARK FRAMEWORK

Create configuration-driven experiments.

Example:

```yaml
robot: fr3

scenario: joint_limit_trap

controller:
  type: predictive

control:
  frequency_hz: 250

prediction:
  horizon_steps: 20
  horizon_seconds: 0.8

constraints:
  joint_position: true
  joint_velocity: true
  joint_acceleration: true
  jerk: true
  collision: true

collision:
  safe_distance_m: 0.03

seed: 42
```

Provide a single reproducible entry point such as:

```bash
ros2 launch predictive_motion_benchmark run_benchmark.launch.py ...
```

or a wrapper:

```bash
./scripts/run_benchmark.sh configs/fr3_joint_limit.yaml
```

It should automatically:

1. reset simulation;
2. load robot;
3. load scenario;
4. run controller;
5. record logs;
6. compute metrics;
7. store metadata;
8. generate machine-readable result files.

---

# 37. RESULT FORMAT

Each run should produce structured output, e.g.:

```text
results/
└── run_<id>/
    ├── config.yaml
    ├── metadata.json
    ├── metrics.json
    ├── trajectory.csv
    ├── solver_stats.csv
    ├── rosbag/
    └── logs/
```

Never make plots the only source of quantitative evidence.

---

# 38. ANALYSIS PIPELINE

Create scripts that aggregate experiments into:

- CSV/Parquet tables;
- summary statistics;
- confidence intervals when appropriate;
- plots;
- comparison tables.

All figures used in the report must be reproducible from stored experiment outputs.

Do not manually edit numerical values into figures.

---

# 39. REQUIRED FIGURES

Generate useful research figures such as:

1. desired vs actual Cartesian path;
2. joint trajectories;
3. joint-limit margin vs time;
4. \(\sigma_{\min}(J)\) vs time;
5. condition number vs time;
6. collision distance vs time;
7. path speed \(\dot s\) vs time;
8. acceleration vs time;
9. jerk vs time;
10. solver timing distribution;
11. success-rate comparison;
12. method-vs-scenario performance table.

Where useful, shade:

- unsafe regions;
- joint-limit margins;
- collision thresholds;
- solver deadlines.

---

# 40. ABLATION STUDY

The full method must be decomposed.

At minimum evaluate:

### Full method

Predictive redundancy + singularity handling + collision prediction + joint-limit prediction + retiming + smoothness constraints.

Then remove one component at a time:

- no prediction;
- no singularity term;
- no joint-limit future penalty;
- no predictive collision handling;
- fixed path speed;
- no jerk constraint;
- shorter prediction horizon.

Measure how performance changes.

The report must not simply state that every component is useful.

If an ablation shows a component contributes little, report that honestly.

---

# 41. HORIZON STUDY

Evaluate multiple horizons.

Example:

- 0.1 s
- 0.25 s
- 0.5 s
- 0.75 s
- 1.0 s
- 1.5 s

Study tradeoff:

\[
\text{performance}
\quad vs \quad
\text{computation}
\]

Determine whether longer horizons provide diminishing returns.

---

# 42. CROSS-ROBOT VALIDATION

After FR3 is stable, test the same algorithm on at least one additional 7-DoF manipulator.

Preferred:

- KUKA iiwa 14.

Optional third:

- Kinova Gen3.

Do not extensively retune the algorithm separately for each robot without documenting the changes.

Separate:

- universal parameters;
- robot physical limits;
- task-specific parameters.

Report whether behavior generalizes.

---

# 43. TESTING REQUIREMENTS

## Unit tests

Test at minimum:

- FK;
- frame transforms;
- Jacobian;
- finite-difference Jacobian;
- SE(3) log error;
- null-space projection;
- joint-limit cost;
- singularity metrics;
- QP matrix dimensions;
- QP feasibility;
- bound construction;
- trajectory constraints;
- retiming continuity.

## Integration tests

Test:

- controller ↔ MuJoCo;
- ROS state ↔ controller;
- scene ↔ collision model;
- reference generator ↔ controller;
- benchmark runner ↔ metrics.

## Regression tests

Create deterministic scenarios with expected envelopes.

Example:

```text
joint_limit_trap_seed_42
```

A regression test may assert:

- no collision;
- task completes;
- max position error below threshold;
- no joint-limit violation;
- solver deadline miss below threshold.

Do not make regression thresholds unrealistically tight.

---

# 44. NUMERICAL ROBUSTNESS REVIEW

Explicitly investigate:

- singular matrices;
- poorly conditioned Jacobians;
- tiny singular values;
- invalid quaternions;
- discontinuous orientation representations;
- finite-difference sensitivity;
- infeasible QPs;
- solver warm-start failure;
- collision-gradient instability;
- path endpoint behavior;
- \(\dot s\rightarrow0\);
- large timestep instability.

Every discovered numerical issue should either be fixed or documented.

---

# 45. FAILURE HANDLING

Runtime control code must define behavior for:

- QP infeasibility;
- solver timeout;
- numerical exception;
- missing robot state;
- invalid command;
- impending collision;
- path reference failure.

Do not silently continue with invalid commands.

Provide a safe fallback strategy appropriate for simulation, e.g.:

- hold current state;
- smoothly decelerate;
- invoke reactive fallback.

Track fallback activations in benchmark metrics.

---

# 46. CODE QUALITY

Use:

- clang-format;
- compiler warnings;
- static analysis where practical;
- clear namespace structure;
- documented public APIs;
- meaningful unit tests.

Avoid:

- giant monolithic controller classes;
- hidden global state;
- magic constants;
- duplicated kinematics implementations;
- uncontrolled configuration proliferation.

Separate math from ROS wrappers where practical.

Core algorithms should be unit-testable without requiring ROS launch.

---

# 47. PERFORMANCE ENGINEERING

Profile the predictive controller.

Measure time spent in:

- Jacobian computation;
- collision query;
- linearization;
- QP construction;
- QP solve;
- trajectory update;
- ROS overhead.

Optimize actual bottlenecks rather than guessing.

Use solver warm starts where appropriate.

Avoid unnecessary dynamic memory allocation in critical loops where practical.

---

# 48. REPRODUCIBILITY

Document:

- OS;
- dependency versions;
- compiler;
- solver configuration;
- robot model commit/version;
- MuJoCo version;
- ROS version;
- seeds;
- benchmark configuration.

The README must contain a minimal reproducible workflow.

The benchmark must not depend on hidden local files.

---

# 49. THIRD-PARTY LICENSE REVIEW

Before finalizing:

- identify third-party repositories/models;
- check their licenses;
- preserve required notices;
- distinguish copied/modified code from original project code.

Create:

`THIRD_PARTY_NOTICES.md`

Do not claim externally authored robot models or algorithms as original work.

---

# 50. DOCUMENTATION

At minimum write:

## `docs/project_spec.md`

What the project is and is not.

## `docs/architecture.md`

System architecture and package responsibilities.

## `docs/mathematics.md`

Mathematical formulation, frames, notation, constraints, objective.

## `docs/experiment_protocol.md`

Exactly how experiments are performed.

## `docs/benchmark_definition.md`

Scenario definitions and metrics.

## `docs/report.md`

Paper-style final technical report.

---

# 51. FINAL REPORT STRUCTURE

Use a research-paper-like structure:

1. Abstract
2. Motivation
3. Related technical background
4. Problem formulation
5. System architecture
6. Baseline methods
7. Proposed predictive method
8. Online retiming
9. Implementation
10. Benchmark design
11. Experimental results
12. Ablation
13. Cross-robot evaluation
14. Computational performance
15. Limitations
16. Failure cases
17. Future hardware validation
18. Conclusion

Do not write the report before actual results exist.

No fabricated values.

---

# 52. README QUALITY

The repository landing page should quickly explain:

- what problem is being solved;
- why reactive methods fail;
- what the proposed method does;
- system architecture;
- supported robots;
- how to run a demo;
- benchmark summary;
- key quantitative results;
- limitations.

Include visualizations only after they are generated from actual working experiments.

Prefer three strong visual examples:

- joint-limit trap;
- singularity avoidance;
- constrained inspection/collision scenario.

---

# 53. PHASE REVIEWS

After EVERY major phase, create:

`reviews/phase_<N>_review.md`

Each review must contain:

## Scope completed

What was actually implemented.

## Evidence

Commands/tests/results proving functionality.

## Known issues

Concrete remaining defects.

## Technical debt

Shortcuts that need repair.

## Scientific risk

Anything that could invalidate later experiments.

## Decision

Exactly one:

`PASS`

or

`FAIL`

A phase should FAIL if its core acceptance criteria are not met.

Do not mark PASS because "the implementation is mostly there."

---

# 54. INDEPENDENT ARCHITECTURE REVIEW

After the main system works, perform a dedicated architecture audit.

Create:

`reviews/architecture_audit.md`

Inspect for:

- controller/simulator leakage;
- duplicated data sources;
- hidden robot-specific assumptions;
- incorrect coordinate conventions;
- ROS coupling inside mathematical core;
- untestable components;
- benchmark-controller coupling;
- inappropriate access to ground-truth simulator data.

Findings must be categorized:

- Critical
- High
- Medium
- Low

Fix Critical and High findings whenever feasible before final benchmark.

---

# 55. MATHEMATICAL REVIEW

Create:

`reviews/mathematical_audit.md`

Independently re-check:

- Jacobian convention;
- SE(3) error;
- null-space projection;
- discrete-time model;
- path-progress model;
- velocity bounds;
- acceleration bounds;
- jerk bounds;
- collision linearization;
- optimization dimensions;
- convexity assumptions;
- singularity approximations.

For each equation used in code, verify that implementation matches documentation.

Specifically search for sign errors and frame inconsistencies.

---

# 56. SCIENTIFIC REVIEW

Create:

`reviews/scientific_audit.md`

Act as a skeptical robotics reviewer.

Ask:

### Novelty

Is the project actually doing something beyond combining existing packages?

### Baselines

Are comparisons fair?

### Metrics

Do metrics actually measure the claimed improvements?

### Benchmark design

Were scenarios designed after seeing results in a way that unfairly favors the proposed method?

### Tuning

Were baselines given reasonable tuning?

### Evidence

Are claims supported by repeated trials?

### Generalization

Does the method work outside one manually tuned FR3 scenario?

### Limitations

What does simulation fail to capture?

### Contribution

Which parts are genuinely original?

The audit must explicitly identify any claim that is not yet justified.

---

# 57. RED-TEAM REVIEW

After implementation and before declaring completion, deliberately attempt to break the system.

Create:

`reviews/red_team.md`

Test at least:

- unusual initial configurations;
- near-singular initial state;
- path starting close to joint limits;
- very slow reference;
- very fast reference;
- nearly zero movement;
- abruptly changing target;
- infeasible target;
- collision corridor narrower than feasible;
- solver warm-start corruption/reset;
- prediction-horizon extremes;
- orientation wrap-around;
- robot model change;
- larger control timestep.

Document failures.

Do not hide unsuccessful cases.

Fix critical failures when practical.

---

# 58. REPRODUCIBILITY AUDIT

Perform a clean build from scratch.

Create:

`reviews/reproducibility_audit.md`

Verify that a new environment can:

1. build;
2. launch simulation;
3. run at least one benchmark;
4. regenerate metrics;
5. regenerate at least one main result figure.

If this fails, the project is not complete.

---

# 59. PERFORMANCE AUDIT

Create:

`reviews/performance_audit.md`

Report:

- requested frequency;
- achieved frequency;
- mean solve time;
- p95;
- p99;
- maximum;
- deadline misses;
- collision-check cost;
- optimization cost.

Do not claim "real-time" without these measurements.

---

# 60. FINAL PROJECT AUDIT

At the end, create:

`reviews/final_audit.md`

The final audit must answer:

## Engineering

- Does everything build?
- Are tests meaningful?
- Is the architecture maintainable?
- Is the setup reproducible?

## Robotics correctness

- Are FK/Jacobians validated?
- Are frames correct?
- Are constraints actually respected?

## Algorithm

- Is prediction genuinely used?
- Does prediction improve anything?
- Does retiming genuinely interact with redundancy?

## Science

- Are baselines fair?
- Are results statistically credible?
- Are ablations complete?
- Are negative findings reported?

## Performance

- Can the system meet its target control rate?
- Are solver failures understood?

## Generalization

- Does it work on another robot or substantially different scenario?

## Original contribution

State in precise terms what was newly implemented in this project rather than inherited from external libraries.

Finally classify the project:

- NOT READY
- ENGINEERING DEMO
- STRONG ENGINEERING PROJECT
- RESEARCH-GRADE PROTOTYPE

Explain the classification using evidence.

Do not automatically choose the highest category.

---

# 61. ISSUE REGISTER

Maintain throughout development:

`reviews/issue_register.md`

Each issue should include:

```text
ID
severity
component
description
evidence
status
resolution
```

Use severity:

- Critical
- High
- Medium
- Low

No unresolved Critical issue is allowed at final completion.

Any unresolved High issue must be prominently disclosed.

---

# 62. NO-FAKE-COMPLETION RULE

Never mark a task as complete when it only has:

- placeholder code;
- TODO;
- mocked numerical result;
- unexecuted test;
- configuration with no validation;
- generated figure from fake data;
- algorithm that compiles but has not been run;
- README claim not supported by evidence.

If something cannot be completed, explicitly record:

- what failed;
- why;
- what evidence exists;
- what remains.

Partial but verified implementation is preferred over fake completeness.

---

# 63. NO-RESULT-FABRICATION RULE

Never invent benchmark numbers.

Never place hypothetical results into final tables.

Synthetic dummy data may only be used for testing plotting pipelines and must be clearly marked as synthetic and excluded from final research conclusions.

---

# 64. ITERATIVE IMPLEMENTATION POLICY

At every major phase:

1. implement;
2. compile;
3. run tests;
4. run the smallest meaningful simulation;
5. inspect numerical output;
6. fix problems;
7. document;
8. perform phase review;
9. only then proceed.

Do not implement the entire repository first and test at the end.

---

# 65. PRIORITY ORDER

If scope becomes large, prioritize in this exact order:

### Tier 1 — mandatory

- FR3 model;
- MuJoCo simulation;
- Pinocchio validation;
- pseudoinverse;
- DLS;
- null-space control;
- reactive QP;
- MoveIt Servo comparison;
- standardized benchmark framework.

### Tier 2 — project core

- predictive horizon;
- future joint-limit handling;
- future singularity handling;
- future collision handling;
- path-progress optimization;
- online retiming;
- jerk handling.

### Tier 3 — research validation

- systematic multi-seed experiments;
- ablation;
- horizon study;
- cross-robot test;
- computational profiling.

### Tier 4 — extensions

- moving obstacles;
- uncertain obstacle prediction;
- control barrier functions;
- torque/dynamics constraints.

Do not sacrifice Tier 1–3 quality for Tier 4 features.

---

# 66. DO NOT ADD UNRELATED FEATURES

Do not add unless clearly necessary:

- reinforcement learning;
- neural networks;
- vision;
- LLMs;
- SLAM;
- grasping;
- force control;
- torque NMPC;
- hardware drivers.

These can become future work.

They are not part of the current research question.

---

# 67. EXPECTED FINAL DELIVERABLES

A complete project should include:

- working repository;
- professional package architecture;
- parametric CAD;
- FR3 simulation;
- additional robot validation;
- validated kinematics;
- baseline controllers;
- reactive QP;
- predictive controller;
- retiming system;
- benchmark framework;
- automatic experiment runner;
- quantitative metrics;
- systematic experiment results;
- ablation results;
- solver performance results;
- plots;
- automated tests;
- CI;
- reproducible environment;
- technical documentation;
- paper-style report;
- phase reviews;
- architecture audit;
- mathematical audit;
- scientific audit;
- red-team audit;
- reproducibility audit;
- final audit.

---

# 68. FINAL DEFINITION OF SUCCESS

The project is NOT successful merely because the robot moves.

It is successful when evidence demonstrates that:

1. robot kinematics are numerically correct;
2. simulation is reproducible;
3. reactive baselines are implemented fairly;
4. future constraints are explicitly predicted;
5. predictive redundancy resolution changes behavior BEFORE reactive intervention becomes necessary;
6. online path retiming meaningfully interacts with constraint risk;
7. joint, velocity, acceleration, jerk, and collision constraints are quantitatively monitored;
8. the proposed method is compared against meaningful baselines;
9. ablation shows which components actually matter;
10. performance is measured rather than assumed;
11. the algorithm generalizes beyond one hand-crafted trajectory;
12. all major claims can be traced to reproducible experiment data.

---

# 69. STARTING INSTRUCTION

Begin by inspecting the existing repository and environment.

Do not immediately write large amounts of controller code.

First produce or update:

1. `docs/project_spec.md`
2. `docs/architecture.md`
3. `docs/dependency_matrix.md`
4. repository/package structure
5. build environment
6. Phase 0 reproducibility setup

Then proceed sequentially through the phases above.

At the end of every phase, perform the required review before continuing.

When there is a design choice, prefer:

- mathematical correctness;
- reproducibility;
- modularity;
- measurable performance;
- scientific validity;

over implementation speed or visual spectacle.

The final goal is not a flashy simulation.

The final goal is a **defensible, quantitatively validated robotics motion-control research project**.