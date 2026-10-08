# Model boundary stage 2A — source implementation, pending review

Implemented: an explicit frozen-review/protocol/file gate; real current ELF and
loaded SDK file/mapping identity checks; complete reviewed actual ModelMetadata
matching; a move-only prepared live invocation, genuine model handle and owned
raw result; separate constructor/query/transport refusal records. No source was
configured/compiled/executed, and no actual Model/metadata/rollout call occurred.

Only `foundation.hpp` needs a versioned extension: the previously private empty
permission now owns an opaque shared release state, and LiveActualContext exposes
its already validated immutable observation/transaction IDs for exact binding.
The accepted original header is preserved in `history/foundation_before_stage2a`.
Foundation cpp/CMake bytes and every old model/checker/profile/freeze remain
unchanged. The new target lives under model_boundary/ and excludes original
probes from the default build graph; it has no CLI or automatic test.

Permission loading hashes/parses only actual reviewed files. No caller boolean,
invented nonempty file SHA, archivedf1 identity or synthetic RawResult constructor
can create a genuine forecast witness. Trust in the expected review SHA comes
from the separate authorized dispatch; source checks do not self-authorize a run.
The existing source-review checkpoint is not a runtime release. All seven claim
bits remain false in the required protocol, and no full-horizon performance,
finite neighborhood, controller, timing, contact or safety acceptance is inferred.

The native Model constructor occurs only after fresh identity rechecks, a bounded
profile planning reservation, expected metadata parsing and a FIRST-only retained
attempt claim. Metadata query is separately counted and every field in the old
getter is checked: nq/nv/version, joints/frames/index/dof rosters, masses, armature,
gravity, R/B and damping. The complete observed metadata is retained on mismatch.
Hash/loader closure is rechecked after constructor/query and before/after rollout.
Its exact units string follows the original public source declaration; the SDK
does not separately report units. Full compiler/source/include closure correctness
still needs independent freeze/build review; hashes are not compiler attestation.

The invocation factory consumes only an already validated LiveActualContext and
SHA-pinned LiveActual input. Frozen actual/nominal initial, previous alpha/b,
completed tick/command/observation/transaction and constants identity all match
exactly; the literal per-cell alpha/b/cycles are retained. Model-call input comes
from this context and these immutable controls. AlgebraTest and archived-carrier
types cannot be substituted. Real observer freshness/current contact facts remain
the separate integration contract: a stored typed context is not proof of the
caller's current clock or hardware state.

The invocation owns a case budget constructed internally from its exact frozen
mesh/cost-shape/capture plan, which shares batch limits with other retained cases.
It reserves128+10*N numeric slots before native input arrays. The model/profile
owner reserves1m logical planning slots before SDK construction; the raw owner
reserves3*raw_shape minus already held invocation slots, with checked subtraction.
Together these partition the original3*raw+1m SDK planning allowance rather than
increasing it. Original source-plan buffer allowances are unchanged. This is a
logical admission/lifetime plan, not measured SDK allocations, STL capacity,
YAML/string allocations, all process memory or RSS proof.

Raw fields are held exactly as returned from the real extension::Model::rollout.
No copying/flattening of raw matrices, success flag rewrite, error replacement,
prefix promotion, fabricated tail, shortening or retry occurs. RawResult destruction
precedes its ticket release. Native Model destruction precedes its profile ticket,
and shared profile/input owners retain the same tickets while any outcome/handle/
forecast needs them. Genuine derivative/nominal refusals keep all original
value/half/cycle/cell/force/friction/clip/error/maps. A C++ transport exception with
no returned result is represented separately, never as a fabricated failed Model
return. The raw numeric envelope is inspected against its reserved shape; any
violation retains the complete original object and marks refusal. SDK allocations
are opaque, so this check is not a promise to enforce allocator activity inside it.

There are no affine maps, cost/problem, usable controller permission or normalized
certificate emitted here. Native cumulative cell_A/B/defect/origin validation,
strict exact roster/timing/input/value/defect identities and all-scope-false typed
normalization are the next SOURCE stage. Lossless capture, the owned scratch/copy
schedule, canonical full term/sum evaluations, half-first Hessian, independent
readers and fixed numerical verification are also outstanding. No build/run should
be inferred from this partial implementation stage.

Local editing history includes one rejected apply_patch operation due to listing
the same file twice in one patch; it made no file changes and was corrected with
a single update operation. This is a source-edit tool failure, not an executable
or numerical failure. No previous research failure has been removed or relabeled.


Independent source-review corrections retained before finalization:

- Typed document parsing now checks strict JSON grammar, duplicate decoded keys,
  quoted strings, untagged numeric syntax and literal false. The earlier string
  coercion allowed quoted boolean/numeric substitutes; the old version and packet
  are preserved under history/before_scalar_grammar_fix. No parsed fixture or
  runtime output was repaired.
- ModelOpenOutcome.hasModel now reports the actual live handle/model/profile
  state, including false after move extraction or outcome move. Accessing an
  extracted/refused model rejects. The original source is preserved under
  history/before_handle_and_raw_envelope_fix.
- Actual retained raw numeric slots must fit BOTH the declared raw-result shape
  and the SDK planning ticket. The 3x transient/opaque SDK allowance cannot widen
  the accepted returned-result envelope. Mismatches retain the complete original
  object with a structural refusal; exact timing/dimensions/defects remain deferred.

One later documentation patch also missed a context line and was rejected;
source text edits were then completed with explicit checked replacement. These
edit-tool rejections are retained facts, not compiler/numeric results.
