# Future frozen Model boundary protocol schema

This describes source-level checks. It contains no runnable release, accepted
metadata values, binary identity or permission to execute. Existing SOURCE_PLAN
and FOUNDATION source-review decisions fail the required runtime decision check.
The reviewer must separately freeze/review the complete source/build/inputs,
protocol and exact process/output paths, then provide the trusted review-record
SHA256 through a direct authorized dispatch. A caller's chosen digest or newly
created record is not evidence of reviewer/human authorization.

The code parses SHA-verified actual document bytes, applies a strict JSON grammar
before yaml-cpp decoding, rejects duplicate decoded keys and unknown schema keys,
and checks the following exact schemas. YAML tags/aliases/directives/comments,
unquoted keys, trailing content and nesting beyond64 refuse. String fields are
quoted JSON strings (yaml-cpp non-specific string tag `!`). Numeric fields must
be untagged plain scalars (`?`) with JSON grammar
`-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?`, converted with the classic locale,
with conversion errors/nonfinite results refused. Unsigned count fields additionally
require `0|[1-9][0-9]*` and checked uint64 accumulation. Scope bits require the
untagged literal `false`; quoted `"false"`, `!!str false`, `!!bool false`, true,
null and aliases all refuse. Quoted/tagged numeric replacements also refuse. All
artifacts use `{role,path,sha256,bytes}`; paths are absolute, SHA256 lower-case,
lengths positive canonical unsigned integers. Metadata documents are at most8MiB.
Each closure has at most4096 unique roles/paths; loaded DSOs at most512. External
review must confirm these are complete closures, compiler/build evidence and XML
include dependencies. Runtime file hashes do not prove compiler attestation,
physical correctness or an adversarial filesystem lock.

| Document | Exact root keys / required meaning |
|---|---|
| Run review | schema=`PUBLIC_LIVE_AFFINE_V2_RUN_REVIEW_1`, decision=`RELEASED_FOR_ONE_BOUND_COMPONENT_ATTEMPT`, scope=`MODEL_CONSTRUCTOR_METADATA_AND_ONE_LIVE_FORECAST_ONLY`, protocol artifact, phase5=`NOT_ACCEPTED`, phase6=`NOT_STARTED` |
| Protocol | schema=`PUBLIC_LIVE_AFFINE_V2_FROZEN_PROTOCOL_1`, source_kind=`LiveActual`, producer_sha256, constructor_attempts=1, metadata_attempts=1, rollout_attempts=1, scope_claims, artifacts, attempt_claim_path |
| Scope claims | segment, two_sided_ball, admissibility, execution, safety, uniform_accuracy, controller_readiness; all must be literal false |
| Protocol artifacts | Exactly build_manifest, source_closure, xml, constants, sdk_manifest, derivative_policy, expected_metadata, invocation |
| Build binding | schema=`PUBLIC_LIVE_AFFINE_V2_BUILD_BINDING_1`, target=`public_live_affine_v2_model_boundary`, producer_sha256, source_closure_sha256, sdk_manifest_sha256 |
| Source closure | schema=`PUBLIC_LIVE_AFFINE_V2_SOURCE_CLOSURE_1`, files; required compiled-source roles are explicitly listed in source; all additional headers/build/compiler/entrypoint/XML dependencies required by independent review remain listed and hashed |
| SDK closure | schema=`PUBLIC_LIVE_AFFINE_V2_SDK_CLOSURE_1`, files, loaded_libraries; every library path must occur in verified files; exact Linux loader inventory, canonical path and process-mapped inode/device are checked |
| Derivative policy | schema=`PUBLIC_LIVE_AFFINE_V2_DERIVATIVE_POLICY_1`, certificate_name, cycle_dt=.004, substep_dt=.002, control_margin=1e-8, nx30, nu8, max_cells32, max_cycles375, max_samples750; original certificate string unchanged |
| Expected metadata | pinocchio_version4.1.0, nq7, nv7, joint_names, frame_names, idx_q, idx_v, joint_nq, joint_nv, masses8, armature7, gravity3, R7, B7, damping7, units; finite coefficients and fixed joint mapping; all actual values/rosters must match exactly after the gated metadata query |

Metadata/state units use the original published declaration exactly:
`q/C rad,v/w rad/s,s dimensionless,r1/s; alpha rad/s^2,b1/s^2; time seconds; mass kg/armature kg*m^2`.
This is a declared source convention checked for consistency, not a unit field
provided independently by the SDK getter. Expected floating values must be
losslessly round-trippable; changing gates to accommodate rounded metadata is
not permitted. A future independent protocol may choose an explicit exact binary
metadata representation through a separately reviewed source version.

Invocation root keys are schema=`PUBLIC_LIVE_AFFINE_V2_INVOCATION_COST_BOUND_2`, source_kind=
`LiveActual`, units, boundary, initial, previous_alpha, previous_b, mesh, controls,
factor_shape, cost_input, capture_mode, encoding. Boundary has completed_tick,
completed_command_sequence, observation_id, transaction_id. Initial has q/v/C/w/s/r.
The first live nominal anchor is exactly this actual initial. The file's state,
prior histories and all boundary identities must match the validated current
LiveActualContext; its constants identity must match the released profile.

Mesh has steps, total_macro_cycles, policy, explicit_cycles. Controls has one
`{alpha,b}` per cell and inherits that mesh's literal cycles. Factor shape has
terms, rows, largest_term_rows, addition_coefficients, addition_records. This
boundary stage uses those counts for the prospective whole-case resource
plan and retains them for exact comparison with actual cost topology.
`cost_input` has exactly `artifact` and `semantic_sha256`; artifact has exactly
`{role:"cost_input",path,sha256,bytes}`. Its real file SHA/length is checked during
preparation before Model construction and included in later pinned rechecks.
The separately reviewed semantic SHA binds complete ordered cost values, names,
units, sample additions, chosen initial kind/shift and evaluation U; see
[cost input contract](../cost/INPUT_CONTRACT.md). No weights, cost codec or
runtime authorization are supplied by this source checkpoint. The old
`PUBLIC_LIVE_AFFINE_V2_INVOCATION_1` schema is superseded and preserved verbatim
in source history; it must not be used with the current boundary. Capture mode and
encoding choose the reviewed foundation quota plan; actual capture is not yet
implemented. No AlgebraTest or archived carrier can enter this factory.

Permission preparation/open/forecast entry each latches at most once, including
preflight/quota failures. Before the first actual constructor, the code creates
the exact reviewed attempt_claim_path with O_CREAT|O_EXCL and fsyncs review,
protocol, producer and invocation SHA identities. An existing or incomplete
claim refuses. No deletion, overwrite, retry token or automatic repair exists.
Reloading a permission/process still faces that retained cross-process claim.
Future runner logs/stdout/stderr/exit/argument/READY evidence remain mandatory;
this small claim is not a substitute for them or for external authorization.

The loaded-library check intentionally refuses unsupported hosts, noncanonical
or unresolvable/deleted library paths, omitted DSOs and changed mapped file
inodes. It verifies the declared file/mapping identity, not a cryptographic dump
of all relocated process memory or a dynamic-loader race lock. The separately
reviewed runtime requires immutable files and a stable loaded closure.

SOURCE3C1 retains requested output NumericEncoding as ResourcePlan::numericEncoding().
The cost artifact declares its INPUT format in its SHA-bound magic/schema. This
version supports matched Binary/Binary and Json/Json pairs only; mismatches refuse
explicitly, with actual_input and requested_output recorded separately. No JSON
byte refusal selects binary. Source closure now also requires capture_state.hpp,
cost_input_decoder.hpp/cpp and input_codec_CMakeLists. The current input schema
and complete failure/output contract are in ../input_codec/; the output publisher
is not implemented and no source record constitutes a runtime release.
