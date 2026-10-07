# Project showcase

Actual project renders, diagnostic figures and downloadable CAD artifacts.
Phase 0–4 component gates have passed; Phase 5 awaits independent acceptance.
These assets illustrate the stated scope and do not establish final research
performance or physical hardware safety.

## Task-completion videos

Three curated successful Phase 4 inspection trials, rendered from saved measured
joint states using MuJoCo 3.3.7 and the pinned scene assets. Each clip is 24 seconds
at 720p/30 fps and 1x simulated-time speed. It includes warmup, path following and
settling; the mint curve is the reference-path overlay. These are recorded-state
replays, not fresh experiments or wall-clock real-time demonstrations.

| Method | Video | Recorded final position error |
|---|---|---:|
| Reactive QP | [Watch / download](../videos/phase4-reactive-qp-81011.mp4) | 0.00471 mm |
| Fixed DLS with common constraint projection | [Watch / download](../videos/phase4-fixed-dls-81011.mp4) | 0.00514 mm |
| Adaptive DLS with common constraint projection | [Watch / download](../videos/phase4-adaptive-dls-81011.mp4) | 0.00514 mm |

![Reactive QP task replay](../videos/phase4-reactive-qp-81011-middle.jpg)

![Fixed DLS task replay](../videos/phase4-fixed-dls-81011-middle.jpg)

![Adaptive DLS task replay](../videos/phase4-adaptive-dls-81011-middle.jpg)

Selection: completed evaluation seed 81011 from each of these methods. Both DLS
methods had lower peak position error on 81011 than on 81012; the QP 81012 trial
failed. All failures remain retained, including Servo halts. These curated clips
do not imply superiority or replace the [full Phase 4 review](../reviews/phase_4_review.md).
Clearance overlays report the shared controller model rather than a physical
safety certificate. Replay uses the original frozen records, which precede the
separately verified online position-monitor repair.

Provenance and hashes:
[QP](../videos/phase4-reactive-qp-81011.json),
[fixed DLS](../videos/phase4-fixed-dls-81011.json),
[adaptive DLS](../videos/phase4-adaptive-dls-81011.json).
The [renderer](../scripts/render_task_video.py) samples nearest saved post-step
states and runs forward geometry only; it does not simulate new motion. Raw
recordings remain in the verified local Phase 4 evidence archive.

## Inspection assembly

![Generated inspection tool and fixture](../figures/inspection_cad.png)

Parametric CAD tool and fixture, with persisted-document and export checks.

![FR3 inspection simulation scene](../figures/inspection_scene.png)

FR3 with the inspection tool and separate fixture collision components.
This image depicts the integrated scene; it is not a predictive-control result.

## Simulation and diagnostic figures

![FR3 MuJoCo simulation render](../figures/fr3_phase0.png)

Pinned FR3 model running in MuJoCo, from the Phase 0 simulation check.

![Kinematics numerical validation](../figures/kinematics_validation.png)

Kinematics validation figure; provenance is recorded in
[the figure manifest](../figures/kinematics_figure_manifest.json) and
[Phase 1 review](../reviews/phase_1_review.md).

![Discrete inspection pose screening](../figures/offline_inspection_screening.png)

81 discrete candidate inspection poses with conservative full-tool clearance
screening. These are offline pose checks, not a continuous executed trajectory.
[Figure manifest](../figures/offline_inspection_figure_manifest.json).

![Phase 5 position-servo contract diagnostic](../figures/phase5/phase5_servo_contract_v19.png)

The retained failed high-tracking-weight development run corrects the initial
pose while path progress remains negligible. Model input, command acceleration
and measured physical acceleration have different meanings under the existing
position servo. This is a paused-simulation development diagnostic, not Phase 5
acceptance. [Independent mathematical audit](../reviews/evidence/predictive_math_specialist_20261007.md)
and [source/output hashes](../figures/phase5/phase5_servo_contract_v19.json).

![Phase 5 servo training](../figures/phase5/phase5_servo_training_v1.png)

Actual MuJoCo training data shows position-servo lag and bounded stopping.
Root independently checks recorded state continuity, command integration and
derivatives, frozen URDF/protocol limits and recorded command age. The model
has not yet been fitted or validated on the separate development trace.
This is a calibration fixture, not predictive-task or online acceptance.
[Figure hashes](../figures/phase5/phase5_servo_training_v1.json).

![Rejected affine servo forecast](../figures/phase5/phase5_servo_model_v1_failed.png)

The frozen first affine model passes short-duration checks but exceeds its
prefrozen 800 ms limits on both training and separate development validation.
The independent root reproduces these errors without future-state resets.
Overlapping forecast windows are diagnostics, not independent trials.
[Independent audit](../reviews/evidence/servo_model_v1_math_audit_20261007.md)
and [figure provenance](../figures/phase5/phase5_servo_model_v1_failed.json).

![Local soft-friction model validation](../figures/phase5/phase5_servo_soft_friction_v2.png)

The frozen local soft-friction model passes the stated short and 800 ms checks
on a new development waveform. Root independently recomputes its scalar
transition, derivatives and all forecast windows. Earlier preparation motion
exceeds this model's declared domain; an expanded waveform is rejected by the
original command constraints. This is local recorded-input prediction evidence,
not main-controller or Phase5 acceptance.
[Independent local scope](../reviews/evidence/servo_soft_v2_math_audit_20261007.md)
and [figure hashes](../figures/phase5/phase5_servo_soft_friction_v2.json).
The separate [augmented transition oracle](../reviews/evidence/augmented_soft_servo_reference_20261007.md)
checks command/physical state propagation and horizon derivatives for the frozen
local model. Its numerical trajectories are model calculations; the plot above
continues to identify the actual recorded validation input.

![Retained expanded validation failure](../figures/phase5/phase5_servo_expanded_guard_failure.png)

The larger waveform ends after 1.416 seconds of excitation when the command
QP is infeasible. The plot shows accepted targets, physical motion and recorded
clearance; it does not establish a feasible next command or a completed stop.
A subsequent full replay confirms the first shared-stop QP is also infeasible.
[Original failed trial](../reviews/phase_5_servo_expanded_validation_failure_20261007.md)
and [independent constraint proof](../reviews/evidence/servo_expanded_failure_stop_math_audit_20261007.md).

## Downloadable 3D models

| Asset | Format / units | Purpose |
|---|---|---|
| [Inspection assembly](../cad/generated/inspection.FCStd) | FreeCAD document | Editable parametric source; opening requirements in the CAD guide |
| [Tool solid](../cad/generated/tool.step) | STEP / millimetres | CAD exchange |
| [Fixture solid](../cad/generated/fixture.step) | STEP / millimetres | CAD exchange |
| [Tool visual mesh](../cad/generated/tool_visual.stl) | STL / metres | Visualization |
| [Fixture visual mesh](../cad/generated/fixture_visual.stl) | STL / metres | Visualization |
| [Tool collision mesh](../cad/generated/tool_collision.stl) | STL / metres | Simplified collision representation |
| [Fixture collision mesh](../cad/generated/fixture_collision.stl) | STL / metres | Simplified collision representation |

STL does not encode a unit convention: use the units listed above when importing.
The fixture channel must remain open; a single convex hull of the entire fixture
would fill it. These are research simulation models, with an experimental flange
interface rather than a certified manufacturing design.

See [CAD source parameters](../cad/source/inspection.json),
[artifact hashes](../cad/generated/cad_evidence.json),
[CAD guide](../cad/README.md) and
[independent CAD review](../reviews/cad_component_review.md).

## Subsequent milestones

Add inspected simulation renders, executed trajectory and constraint plots,
and updated useful models as work is completed. Each addition must identify
its data or parameter source and whether it is a development diagnostic or an
accepted result. Commit and push these assets with the milestone backup.
