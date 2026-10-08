# General affine horizon source implementation draft 4

SOURCE_ONLY; static review pending. No CMake configure/build, compiler invocation,
preparation/checker execution, empty/nonempty binary output, model or plant call.
Precondition private remote checkpoint 8eb397f35131071c7e13a5aacaf5fae0e3acccfd
was independently confirmed local HEAD == origin/master before source writing.
Phase5 NOT_ACCEPTED, Phase6 NOT_STARTED; prior finite-step FD FAIL immutable.

New namespace/module only. Core uses Eigen; JSON loader uses a strict JSON
grammar followed by yaml-cpp nodes and OpenSSL EVP byte identity. CMake links no
original nonlinear-model sources or libraries. Original headers provide only
carrier types. No Model constructor, rollout, solver, main, plant or geometry
integration is added. No task weights are imported or tuned.

Core includes actual-coordinate recursive offsets/control maps/initial P,
independent FullPivLU lifted solve, all available exact cell-prefix half samples,
sample lifted views and P, full rectangular factor plus linear/constant objective
substitution, every individual term plus canonical ordered sum, and direct lifted
versus literal polynomial values/gradients/Hessians. Raw H is preserved; literal
polynomial derivatives use its symmetric part. Sum.used_F/f0 and Fc/fc concatenate
in input order; H/g/constants accumulate individual terms in input order.

Public loader consumes byte-pinned archived original input/output only, refuses
incomplete/unsupported or mismatched roster/origin/input/endpoint/defect data,
retains source failure objects exactly, and preserves distinct literal cycle and
half reference states. It reconstructs a native Result with LAST CYCLE LOCAL
Map.A/B/defect/origin and cumulative full-cell cell_* fields, calls the real
normalize_public_native function, compares against JSON normalized cumulative
maps, and supplies typed per-case bridge proof. The N4 fixture has multicycle
cells, so replacing native cell_* with local fields must fail that bridge.
Shifted actual_initial or chosen U remains algebra only, not physically certified.

Fixed v1 development diagnostic caps (N1/N4 intended, no N20/.8s/1.5s support
claim). CLI conservative preallocation plan covers whole case and all cases;
parsed document numeric nodes, materialized inputs, retained outputs, expression
and solver workspace, and serialization arrays consume shared CLI/per-case
numeric budget. Failed cases never release their charges. Individual arrays have
caps; all size arithmetic and finite products/sums are checked. No process RAM
limit is claimed. Policy repeats exact header values and pinned source bytes.

Producer source preparation declares 10 cases: two archived public cases, a
different four-state/three-input synthetic noncommuting case, zero-term algebra,
two authentic source refusals, quoted cycle, false safety flag, ragged matrix and
overflow. Dense explicit rectangular factors, nonzero offsets/linears/constants,
distinct per-cell inputs and prefix sample additions are included. It also writes
separate duplicate-key/YAML/NaN process controls. The preparation script has NOT
been executed, so no final fixture bytes/roster freeze exists yet.

Producer checker source independently assembles NumPy lifted elimination and a
separate recursion, prefixes/initial P, full used factors and exact canonical
sum, direct values/derivatives, source/bridge/types/rosters. Fourteen altered-output
negative controls include omitted case, false scope, unused native bridge,
changed provenance, omitted constant/fullsum factor/initial P/sample P/linear,
state reset, NaN, tied cell inputs, local-lastcycle substitution and failed tail.
Declared comparison abs/rel 2e-12 is prospective and must be independently
reviewed/frozen before outputs; this source file provides no passing evidence.
Root-owned pivoted oracle, plan and archived bundle stay untouched.

Static draft preservation:

- draft1/2/3 remain in their previous immutable paths and accepted checkpoint.
- static-drafts/before-source-self-review retains initial draft4 core/native/CLI.
- before-whole-shape-review retains source before additional preparser shape/scalar scans.
- before-budget-copy-review retains source before explicit descriptor copy charge.

Corrections were static: header cstdint, native temporary copy charges, removal
of unused reference, mixed-type auto declarations, hash-before-parse, exclusive
file create, exact failure diagnostic object, concrete native bridge proof,
additional preparser scalar/shape scans and negative controls. No executable
attempt, compile failure or numeric repair occurred; all earlier source versions
are retained for audit.

Pending dispatch sequence: independent static code/parser/policy/fixture review;
source checkpoint backup; separate configure/build plus logs; reviewed empty
schema preflight; prepare exact producer/root inputs; full immutable dependency
snapshot including source headers, compiler/CMake flags, Eigen/yaml/OpenSSL,
runtime libraries, root oracle/plan/bundle and policy/fixtures; only then a scoped
first algebra numerical attempt and independent root review. No unreviewed model,
physics seed, main, trust/admission, holdout or timing run is authorized here.
Evidence-backed plots/showcase update follow actual checked algebra outputs;
existing accepted Phase4 visuals and all failures remain preserved.

Container-capacity static refinement: every known Eigen-owned carrier roster
reserves exact bounded capacity before insertion, preventing vector reallocation
from implicitly deep-copying prior entries regardless of noexcept move traits.
All inserts then use moves or explicitly precharged scalar-vector copies. No
source/model execution occurred; before-container-capacity-review retains the
previous whole core/native/probe/manifest snapshot.

Native proof scope clarification: archived relevant map/state carrier normalization
only. The reconstructed carrier retains needed maps/state/timing/forward
certificates; unused friction/clip auxiliary fields remain default. It is not a
byte-identical complete native Result and does not independently revalidate those
physical auxiliary fields. The full JSON remains byte-pinned and source refusal
diagnostics preserve every original field. Executable sources are unchanged.

Independent bounded semantic math review passed; remaining cumulative-budget
comment resolved in source: per-case planned ceiling is bound into reserve BEFORE
every allocation/counter update, including cases failing midway. Direct callers
default to the fixed 8m hard bound; CLI passes precomputed planned[j]. Authentic
refused sources have zero plan and never materialize Eigen matrices. Pre-fix
header/core/probe/schema/review/manifest are retained under
static-drafts/before-planned-budget-binding. No execution or numerical result.

Final DOC accuracy clarification: the mandatory whole-case preflight guarantees
dimension/count/scope planning and conservative numeric resource ceilings before
materialization. Scalar types and complete array shapes are guaranteed by each
individual loader before that array's allocation. Additional preparser scans do
not imply every malformed case field is checked before any Eigen allocation;
late type/shape refusals are still bounded by the prebound cumulative ceilings.
Header/core/probe/native/scripts and all numerical policies are unchanged.
