# Live affine v2 foundational source stage

This module implements the first reviewed source stage in the separate
`phase5_public_live_affine_v2` namespace. It has not been configured, compiled,
linked or executed. Phase 5 remains NOT_ACCEPTED; Phase 6 remains NOT_STARTED.

Implemented source: checked integer arithmetic and exact-decimal 4 ms mesh
planning; version-fixed resource plans; move-only batch/case budget ownership;
lifetime tickets and owned numeric buffers; pinned file hashing and bounded
static range parsing; validated current-boundary actual state versus an
independent AlgebraTest initial; and a pure first-4-ms command/progress preview.

The foundation target is a standalone static library. It has no executable,
Eigen/Model/plant dependency or Model constructor/query/rollout call. The
`ReviewedForecastPermission` constructor is private and its factory is not
defined in this stage. Hash-only observations and parsed static ranges cannot
produce Model permission or a verified live Model profile.

Start with [source review notes](SOURCE_REVIEW.md) and the deferred
[verification roster](DEFERRED_VERIFICATION.md). The root chat independently
reviews/imports/backs up this packet. No build or execution is released by the
presence of a CMake target or verification roster.

The accepted source plan is under `docs/design/public_live_affine_v2/`.
Old APIs, sources, profiles, checkers, input fixtures, original failures and the
d3d4/ec1 freezes are unchanged. Main/solver/geometry/terminal/stopping/deadline
integration is outside this foundational stage.

The separate [Model boundary source stage2A](model_boundary/SOURCE_REVIEW.md) adds a future reviewed-release gate, actual full metadata checks and genuine move-only raw-result ownership. It remains uncompiled/unexecuted; foundation-only compilation has no Model dependency. No runtime permission follows from these source files. Normalization and full affine/cost/capture remain pending.

[Genuine cumulative normalization source2B](normalization/SOURCE_REVIEW.md) now supplies full/refusal ownership and checked cumulative coefficient views, keeping half2 sample and recursive cycle progress separate. It adds zero Model calls and remains uncompiled/unexecuted. Complete affine/cost/capture/readers remain pending.

[Affine boundary/sample source3A](affine/SOURCE_REVIEW.md) adds compact o/M/P and T/t/structuredinitialselector, callback sample views and optional quota-bound independent DenseAudit. It remains source-only. Cost/capture and numerical validation are pending.
