# Architecture and ownership boundaries

This document specifies interfaces and package responsibilities. A listed package is a planned component until executable source and a passing phase review exist.

## Data flow

```mermaid
flowchart TD
    Task[Inspection path T_d(s), geometry, limits] --> Ref[SE3 reference and derivatives]
    Ref --> Control[Baseline or predictive C++ controller]
    State[Measured q, dq, timestamp] --> Control
    Model[Versioned controller robot and collision model] --> Control
    Control --> Guard[Validate, interpolate and apply command]
    Guard --> Plant[MuJoCo plant]
    Plant --> State
    Plant --> Eval[Independent executed-state evaluator]
    Control --> Log[Solver and cycle telemetry]
    Eval --> Record[Run recorder]
    Log --> Record
    Record --> Analysis[Python aggregation and figures]
```

The optimizer receives measured configuration/velocity, reference and declared scene geometry. It cannot access MuJoCo `mjData`, future plant states, contact solver state or ground-truth collision answers. The evaluator can use those quantities and must remain out of the controller dependency graph.

## Components

| Package | Responsibility | Public boundary |
|---|---|---|
| predictive_motion_description | pinned external MJCF/URDF, frame/joint mapping, physical limits, tool transform, collision pair policy | immutable RobotSpec + asset manifest |
| predictive_motion_sim | MuJoCo model/data ownership, stepping, reset, command application; ROS adapter | Plant interface, measured JointState, evaluation-only contact records |
| predictive_motion_kinematics | Pinocchio FK, TCP transform, LOCAL Jacobian, SE(3), independent numeric validation | immutable model + caller-owned Data/workspace |
| predictive_motion_baselines | pseudoinverse, DLS, null-space, external Servo adapter | controller interface shared by all methods |
| predictive_motion_qp | OSQP workspace, bounds, distance linearizations, reactive QP | validated problem/result with explicit status |
| predictive_motion_predictive | horizon rollout, sequential convexification, risk prediction, warm-start management | horizon plan and first control action |
| predictive_motion_retiming | s/ds/dds model and integrated path constraints; Ruckig/TOPPRA adapters | reference progress state and rate limits |
| predictive_motion_tasks | CAD fixture descriptions and SE(3) inspection paths | geometry snapshot, T(s), derivative and validity |
| predictive_motion_benchmark | resets, seed schedules, common command clock, recorder and independent metrics | immutable run config + result bundle |
| predictive_motion_bringup | launch wiring and visualization | ROS launch/config, no control mathematics |

## Runtime contracts

`RobotSpec`: source revisions/hashes, ordered arm joint names, nq/nv, base/TCP frame names, unit-bearing limits and model paths resolved from an explicit asset root. Acceleration/jerk limits absent from a source must be identified as justified experiment parameters, never silently represented as manufacturer specifications.

`MeasuredState`: monotonically identified sample, simulation/steady timestamps, q and dq in the model joint order, validity/freshness. Invalid length, NaN, out-of-order timestamp or stale data enters failure handling.

`Reference`: T_d(s), body derivative with respect to s, path domain and endpoint policy. Numerical derivatives and rotational interpolation have dedicated tests.

`ControlResult`: accepted command, solver status, residuals, iterations, solve duration, full-cycle duration, feasibility checks, fallback reason and predicted constraint diagnostics. Solved-inaccurate is distinct from accepted; policy thresholds are explicit.

`CollisionSnapshot`: controller-model signed/minimum distances, named geometry pairs, gradients, query timestamps and approximation validity. Mesh simplification and safety margin are common across methods. Ground-truth distances are stored separately in evaluator output.

## Command and plant design

The initial experiment is kinematic motion control driving position-controlled MuJoCo actuators; plant tracking lag remains measured. No torque-control superiority is claimed. Simulation integration timestep, actuator parameters and controller period are distinct fields. All methods use the same plant and actuator mapping. Joint names are validated, not assumed from the first seven qpos entries; gripper coordinates are locked/configured independently.

Controller reset clears previous acceleration, warm starts, reference progress and fallback state. Plant reset restores q, dq, actuator/filter state, time, solver warm state and RNG seed. Determinism is scoped to the same pinned platform/build and serial evaluation; cross-platform bitwise equivalence is not assumed.

## Coupled predictive optimization

The design state is (q, dq, s, ds), with joint/path acceleration inputs. Tracking, posture, clearance and progress terms are optimized over one horizon. Each sequential convexification iteration linearizes around its own nominal rollout and checks the nonlinear candidate. Trust-region limits, convergence thresholds and maximum iterations are configured. Nonconvex singularity and distance terms remain approximations, not claimed convex guarantees.

First-action validation and independent execution monitoring are mandatory. Fallback deceleration must respect available stopping distance; a hold command is not assumed safe for a moving robot. Infeasible stopping is logged as failure. No hard real-time guarantee is claimed on WSL.

## Parallel work and artifacts

One canonical source tree is assembled on Mac. Assigned package owners avoid concurrent edits to the same file. Dell exports source changes and actual build/test evidence through a verified outbox bundle; generated caches/build trees stay on Dell. Analysis reads immutable run directories with model/source revisions. A source revision change invalidates prior regression provenance until re-run.

The initial project will not publish a GitHub repository or execute CI in a remote account without a concrete repository destination. The same CI commands will be run locally; hosted execution status is reported separately.
