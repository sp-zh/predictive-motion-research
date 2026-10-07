# Project showcase

Actual project renders, diagnostic figures and downloadable CAD artifacts.
Phase 0–4 component gates have passed; Phase 5 awaits independent acceptance.
These assets illustrate the stated scope and do not establish final research
performance or physical hardware safety.

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
