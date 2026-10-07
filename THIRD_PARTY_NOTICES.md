# Third-party provenance

Original project code is MIT licensed. External assets and libraries retain their own terms and are not claimed as original contributions. FR3 model provenance and its preserved license are incorporated into `src/predictive_motion_description`; fetched meshes and binary runtimes remain external caches.

| Component | Source | License / verification | Use |
|---|---|---|---|
| FR3 MJCF and meshes | google-deepmind/mujoco_menagerie/franka_fr3 | model-specific Apache-2.0; preserve model LICENSE and notices at pinned commit | plant model |
| Franka URDF / meshes | frankarobotics/franka_description | Apache-2.0; preserve LICENSE and NOTICE from pinned commit | controller model and visualization |
| MuJoCo | google-deepmind/mujoco | Apache-2.0; release notice verification in fetch manifest | simulation runtime |
| Pinocchio | stack-of-tasks/pinocchio | BSD-2-Clause, verify installed source package notice | kinematics engine |
| Coal 3.0.3 | coal-library/coal; Jazzy deb 3.0.3-2noble.20260825.051040 | BSD; installed headers preserve full three-clause notices; no upstream implementation copied into project sources | independent primitive query audit; runtime collision adapter pending |
| Eigen | eigen.tuxfamily.org | MPL-2.0; verify included package notices | linear algebra |
| FreeCAD 1.1.4 | FreeCAD/FreeCAD official Linux AppImage | LGPL-2.0-or-later; upstream bundled dependencies retain their own terms, archive hash pinned in fetch script | parametric tool and fixture generation |
| ROS / MoveIt / OSQP / Ruckig / TOPPRA | dependency matrix links | component licenses must be inspected at integration, not assumed from a meta-package | middleware and comparison infrastructure |

Upstream model generation, collision meshes, library algorithms and external Servo behavior remain attributed to their authors. Each incorporated source/model gains revision, SHA-256 manifest and preserved notices. Licenses of iiwa/Gen3 assets require their own model-specific inspection before use. FreeCAD-generated CAD scripts are original project work; robot meshes are not.
