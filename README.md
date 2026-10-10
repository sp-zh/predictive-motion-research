# Predictive Redundancy-Aware Motion Control

A research project investigating finite-horizon posture selection and online path retiming for 7-DoF inspection manipulators. The intended contribution is preventive constraint handling coupled to path progress, evaluated against strong reactive baselines.

**Development status: Phase 0–4 component gates passed with retained failures. Phase5 has a compiled standalone 0.8s predictive-horizon/QP entry and independently verified immutable runtime profiles; its first actual program attempt was refused by the original file-identity gate before model initialization (symlink-path protocol incompatibility). Canonical-path protocol repair, a complete offline component, repeated controller execution and online timing remain pending. Phase5 is NOT_ACCEPTED and Phase6 is NOT_STARTED. No demonstrated predictive closed-loop advantage over Reactive QP, DLS or Servo is claimed.** The original requirements are preserved in [docs/source/master_project_prompt.md](docs/source/master_project_prompt.md). Historical pauses, conditional diagnostics and rejected protocols remain in the evidence.

Primary platform: Ubuntu 24.04 / ROS 2 Jazzy on Dell WSL2. Primary robot: Franka FR3; planned cross-validation: KUKA iiwa 14. C++ owns runtime math/control/simulation; Python owns experiments and analysis.

- [Project specification](docs/project_spec.md)
- [Visual showcase and downloadable 3D models](docs/showcase.md)
- [Architecture](docs/architecture.md)
- [Dependency matrix](docs/dependency_matrix.md)
- [Mathematical conventions](docs/mathematics.md)
- [Issue register](reviews/issue_register.md)
- [Executed evidence and remaining acceptance work](docs/acceptance_tracker.md)
- [Paired analysis and its executed tests](analysis/README.md)
- [Phase 1 executed kinematics review](reviews/phase_1_review.md)
- [Phase 2 baseline and retained failure review](reviews/phase_2_review.md)
- [Phase 3 redundancy and executed tradeoffs review](reviews/phase_3_review.md)
- [Phase 4 constrained control, actual Servo and retained failures](reviews/phase_4_review.md)
- [Two-computer setup](COORDINATION.md)
- [Parametric CAD generation](cad/README.md) and [executed export review](reviews/cad_component_review.md)

```bash
# Ubuntu 24.04 x86_64 with ROS Jazzy already installed:
sudo bash scripts/phase0/setup_linux.sh
bash scripts/ci.sh
```

See [reproducibility](docs/reproducibility.md) and [Phase 0 review](reviews/phase_0_review.md) for prerequisites and actual evidence. An [uncached rootless Podman build](reviews/clean_component_environment_review.md) independently passed 24 actual unit cases across Phases 0–3, ROS command/state/reset exchange, 2000-sample kinematics validation and four installed consumers. Hosted GitHub Actions has executed successfully, including [run 38090687120](https://github.com/sp-zh/predictive-motion-research/actions/runs/38090687120) at checkpoint `1aa607c`. Its current scope is the baseline component inventory and statistics tests; it does not build or execute the new Phase5 standalone program or a complete predictive task. The editor devcontainer workflow and final research reproduction remain unverified. See [CI coverage and the Phase5 migration path](docs/ci-phase5-coverage.md).

![Actual Phase 0 FR3 MuJoCo render](figures/fr3_phase0.png)

The image shows the pinned upstream FR3 model running in MuJoCo; it is not an inspection benchmark or predictive-controller result. No hardware commands are enabled.

![Actual generated inspection tool and fixture](figures/inspection_cad.png)

CAD geometry and source-document persistence were tested; a three-dimensional inspection curve passed 81 discrete pose and conservative full-tool clearance checks. Continuous motion and research experiments remain pending.

![Actual FR3 with inspection tool and separate fixture collision components](figures/inspection_scene.png)

Physical TCP mapping and a contact-free held startup were tested. Payload inertial parameters are declared simulation assumptions; the held home pose has a conservative clearance lower bound of 0.122684 m. Independent collision-distance validation and continuous motion remain open.

![Recorded discrete inspection pose screening](figures/offline_inspection_screening.png)

These 81 poses define a candidate 3D inspection curve with full-tool clearance checks. They do not represent executed control. [Independent collision-query audits](docs/coal_geometry_protocol.md) retain distance-query and nonsmooth-gradient failures before constrained benchmarks.
