# Inventory core B1 — closed requirements, no leaf export or full closure

This is the explicitly scoped B1 core/schema fallback. CaptureInventoryOwner
consumes actual move-only CostDecodeOutcome through a private constructor/factory,
retaining genuine source, cost/raw/normalized/affine/model/profile/input objects
and failures. It accepts no NumericChunkRecord, arbitrary raw carrier, SHA/count,
fixture array or caller coverage certificate as source completeness. It does NOT
publish root manifest/READY, export full leaf values, execute a driver or certify
full capture. fullCaptureComplete() is deliberately always false.

The implemented source branch is actual decoder/cost return (including rejected
input/cost paths that retain genuine upstream data). Prepare/open/metadata/forecast/
normalization/affine failure branches that never reach a bound affine origin need
additional genuine-owner variants in B2; the complete schema below requires them,
but B1 does not claim they have already been serialized. Early binding failure
keeps original_ or already transferred storage_.source, never drops a moved source.

Five facts remain distinct: genuine component source availability; defined/assigned/
computed leaf classification; successful ORIGINAL callback observation; bytes
captured; exact independent readback. RequiredField describes EXPECTED schema,
indices/type/shape/classification and source availability. Actual leaf binding,
defined_computed state, bytes_captured and exact_readback are UNKNOWN/false inB1,
even if an upstream component is complete. No recipe or observed callback becomes
an evaluated/captured chunk. Dimensions in missing fields are schema placeholders,
not actual zero-sized exports. B2 must resolve exact actual shapes and frontiers.

## Required finite role universe and coverage

Every role has unique (RequiredRole,primary,secondary) key, fixed scalar kind,
rank<=4, ordered dimensions/traversal, conditional presence and computed/forensic/
recipe status. Matrices are row-major unless explicitly stated. Data absent from
upstream is recorded AbsentUpstream, never replaced by zero data. SourceMetadata
roles are compound typed structures, not empty numeric placeholders.

| Family / indices | Required full typed fields |
|---|---|
| Provenance/profile | ELF/build/source/SDK/loaded-DSO/XML/constants/policy/review/protocol/invocation/cost identities and source kind/units/claims. Actual cached metadata: pinocchio_version,nq,nv,joint/frame names,idx_q/idx_v/joint_nq/joint_nv,masses,armature,gravity,R,B,damping; all values/rosters, not hashes alone. No new Model getter. |
| Invocation/process | Exact actual initial q/v/C/w/s/r, previous alpha/b, boundary observation/transaction IDs, cycles/mesh/controls, requested/actual capture mode and encoding; original one-attempt counts/claim, arguments/stdout/stderr/exit/errors and source statuses. |
| Raw flags/errors | value.success,has_final_state,value.error,extension_jacobian_success,first_uncertified_substep(i64),error,transport/structural refusal; all original prefixes retained. |
| Raw state/control | Final/cell/cycle states q/v/C/w/s/r(f64), every cell alpha7,b(f64),cycles(i64), literal roster/time. RawCellControl is composite9, NOT all-double coercion. |
| Substep k | q/v/C/w28(f64); elapsed_s/s_reference/r_reference3(f64); friction force7(f64),branches7(i64),iterations(i64),original_kkt(f64),control/force clips2(i64) plus cell/cycle/half indices. |
| Raw map group,k | group0 substeps/1 cycles/2 cells: local A30x30/B30x8/d30; cumulative cell_A/cell_B/cell_defect; origin/cell_origin/state30; input8; cell/cycle/half(i64). Actual malformed/failure dimensions must be preserved with expected-vs-observed tags inB2. |
| Normalized | Complete indexed cell/sample/cycle A/B/d/origin/endpoint/input/rosters reference EXACT raw chunks with full coverage proofs; polynomial half2 and recursive cycle progress/defects remain distinct. A compound source-reference schema is not a missing values substitute. |
| Compact k0..N | o30/M30*DU/P30*30; T(DY,DU),t(DY); chosen kind(i64)/initial30; structured initial selector all P blocks+zero U block. |
| Samples k | Native A/B/d/source/cell/tick recipe; separately actual evaluated o30/actual offset30/M30*DU/P900. Compact complete affine/cost callbacks do not imply any sample stream ran. All SampleEvaluated roles remain pending inB1. |
| Input term k | Complete names/units/topology/order; F(rows,DY),f0(rows),ell(DY),c0; every addition C(parent_count,30),u64 parent rows,source sample ID/order; evaluation U(DU); file bytes/opaque and typed semantic identities. Missing sealed topology cannot be inferred from frozen totals. |
| Original term k | ORIGINAL usedF/f0/ell/c0; Fc/fc/Hraw/g/c; full direct/condensed objective/gradient/Hessian. Observed callback is not stored output; finite default tolerances remain unchanged. |
| Canonical | Ordered full concatenation term chunk coverage, exact ordered sum Hraw/g/ell/input c0/condensed c; ORIGINAL direct/condensed value/gradient/Hessian at primary=K. Concatenation cannot replace ordered FP arithmetic. |
| Actual DenseAudit | L/E/f/I0; active LU/R workspace; solution column/reverse-row traversal; every actual dense selector; both original compact/eliminated sample o/M/P sets, separate from subsequent streamed samples. Requested Dense but refused/partial audit uses defined/assigned frontier tags, no actual-complete claim. |
| Failure/decoder | All genuinely retained raw/math buffers, initialized-not-computed placeholders, assigned-but-unvalidated prefixes/stage/cursor, prior errors, physical-vs-consumed byte/EOF/SHA/partial-scalar state. Never serialize unused capacity or CPU temporaries as stored arrays. |

B1 catalogue is a bounded streaming schema interface, not a resident numeric
registry. One20-slot role/index/dimension/control frame is reserved before each
visit sequence and every reuse charged before materialization. User copies must
have their own accounted metadata lifetime; role visitor exceptions/reentry latch
first capture refusal. Full actual raw roster overflow or fields not represented
by a current bound complete plan require B2 explicit failure/archive handling,
not truncation to nominal counts or a false COMPLETE_COMPONENT.

## Original consumer ownership

prepareOriginalCaptureGate requires actual complete owned affine outcome. Its
private stable origin token retains the genuine affine anchor/normalization/raw
lifetime. CostFactory creates the actual CostAnchor and privately marks only the
INITIAL term/canonical callbacks as original scope; views reveal that scope and
actual cost-origin token only to the private inventory factory. The observation
gate requires SAME stable source and SAME actual cost origin, exact term order,
all terms before canonical, no replay/reentry, and successful sink return before
counting an observation. K=0 still requires its original canonical callback.

Later withTerm/withCanonicalEvaluation has no original-scope marker and cannot
mint observations, even when values/shapes/hashes match. Source/cost origin tokens
retain actual owners and prevent pointer reuse from masquerading as the old source.
Token/consumer issuance is one attempt; sink/issuance exceptions retain first
source/observer failure. No view may survive its producer callback or be copied
as numeric state. Sink stdfunctions must borrow reviewed owned fields, not retain
unbudgeted arrays or invoke IO/Model in copy constructors/asynchronous callbacks.
Bind compares returned actual cost origin with the observed constructor origin.
No observed event implies bytes captured; B2 must connect original scoped sinks
to private write/readback/coverage commitment without numerical replay.
