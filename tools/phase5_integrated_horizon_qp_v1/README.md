# Integrated coupled horizon/QP source V1

New files are intended at tools/phase5_integrated_horizon_qp_v1 after independent
Root import/review. This temporary packet edits no canonical source or Git.

- integrated_horizon_qp.hpp/.cpp: genuine horizon ownership, new inline objective,
  complete finite SI rows, one solver latch, command/progress gates and data-only
  candidate-forward seam; control-only warm guess.
- first_cycle_component.hpp/.cpp: one prepared invocation -> genuine Model nominal
  -> connection/solver. No CLI, plant or repeated Model/controller loop.
- task_local_provider.hpp/.cpp: actual pinned world-path/kinematics local residual
  and derivative provider. Rotation length applied once by inline objective.
- CMakeLists.txt: static core/original independent QP backend; optional actual task
  provider. Future full review/build must enable provider and pin its closure.
- INTEGRATION_CONTRACT.md: equations, objective weights/units, row/storage/timing
  grains, provenance and failure semantics.
- CRITICAL_PATH_GAPS.md: code gaps, necessary review/freeze gates and later
  acceptance, including750 task commits and .6 progress upper bound at3s.
- MODEL_SESSION_FACTORY_DESIGN.md: minimal new authority for one true candidate
  forward, then a separately reviewed750-cycle session. Design, not implementation.
- HOST_FREE_FIRST_CYCLE_RUN_PROTOCOL_DRAFT.json: deliberately non-runnable schema
  until host/binary/observer/driver/runtime review and external scoped dispatch.
- SOURCE_DIAGRAM_DATA.json: source topology/counts for Root's actual diagram,
  clearly SOURCE_ONLY, with no runtime results or robot motion implied.

No execution-based validation has been performed. Review the source, then freeze
one cohesive build/program package. All historical failures, denied protocols,
original checker and ec1/d3d4 freezes are preserved. Phase5 NOT_ACCEPTED and
Phase6 NOT_STARTED. A source backup does not open the model/solver/plant gates.
