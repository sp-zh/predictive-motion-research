# General affine horizon draft interface v3 (revision of schema_version 1)

SOURCE DRAFT ONLY: no implementation, build, preparation-script execution or
new numerical output. Root prerequisite d4b6caa2400b7c6c9e843473445c4e1fd554d753.
Phase5 NOT_ACCEPTED; earlier finite-step FD FAIL retained unchanged.

Proposed CLI: public_affine_horizon_probe --policy POLICY.json INPUT.json OUTPUT.json.
Refuse an existing output path. No model/XML/constants arguments or model calls.
JSON matrices are row-major arrays of rows; vectors are flat arrays. Numeric
scalars must be unquoted finite JSON numbers (booleans/strings refused). Integers
are canonical nonnegative integers, with cycles strictly positive. Empty cases
is the sole empty preflight; it returns metadata and cases=[], no matrices.

## Frozen policy

Top-level schema_version=1, limits exactly matching header, artifacts list of
{id,path,sha256,source_binary_sha256,certificate_name,archive_sha256} and all seven
scope flags false. CLI verifies actual source file bytes and max_document_bytes
before parsing. Input selects an artifact id; it cannot supply a new allowed hash.
Policy itself and every artifact are frozen/hashed before numerical execution.
Archive identity is provenance, not a claim that this CLI independently checked
every archive member. This verification was completed in prior checkpoint records.
The public source binary is f1b7e6c7e4219fec2beb310540c725b448dcf021b3a95ddafc2922e8849bf1d6.

## Input schema

Top-level {schema_version:1,cases:[CASE]} with unique nonempty case names.
CASE={name,source,actual_initial,terms,evaluate_controls,scope}.
scope={connecting_segment:false,ball:false,admissibility:false,execution:false,
safety:false,uniform_error_bound:false,controller_readiness:false}; omitted or
true claims are refused. evaluate_controls is exactly N*nu entries, cell-major.
An algebraic initial/control shift never changes source nominal fields.

Public source={kind:"public_saved_json",artifact_id,roster:"complete"|"refused",row_name}.
Artifact schema is root archived_sources.json: complete/refused arrays of
{name,original_input,original_output}, plus identities and scope. Names must be
unique across each roster. Preserve failed source value/flags and error text;
refused roster membership cannot become assembly permission. complete membership
also requires successful value with final_state, extension_jacobian_success=true,
first_uncertified_substep=-1, exact named certificate and false original
certifies_two_sided_admissible_neighborhood at case/map level. Descriptor state is
packed [q7,v7,C7,w7,s,r], cell input [alpha7,b], nx=30,nu=8.

Exact ordered roster: N cell maps, sum(m) cycle maps, 2*sum(m) substep maps and
matching value traces; no duplicates or fabricated tail. Public cell maps use
JSON A/B/defect/origin/state/input and last cycle m, half=2. Sample maps use
cell_A/cell_B/cell_defect/cell_origin/state/input, with cell zero-based,
cycle one-based and half 1,2. Last-cycle-local A/B may NOT replace cumulative
sample fields. Native Result.cell_maps requires cell_* fields even for full cells.
Map origins and inputs must exactly match descriptor/literal prior endpoint;
endpoints exactly match corresponding original value traces. Verify all nominal
affine identities with abs=2e-13,rel=2e-13, retain maximum component residuals.
Known cycle/half progress roundoff: each sample retains its own literal endpoint,
and each cell retains its own value.cell_end_states endpoint; do not normalize
or overwrite one from another. Origin chaining uses literal cell origins.

Generic source={kind:"generic_synthetic",nx,nu,cells,samples}.
cells=[{cycles,A,B,defect}], shapes nx*nx,nx*nu,nx; samples optional list of
{cell,cycle,half,A,B,defect}, same shapes, explicitly cell-prefix maps. No physics
certificate or requirement that synthetic substeps reconstruct a physical model.
Indices within cell mesh, ordered, unique; an optional synthetic sample roster
is preserved exactly. Generic source has no public nominal records.

TERM={name,units,F,f0,linear,constant,sample_additions}.
Let dx=nx*(N+1),du=nu*N,dy=dx+du. F is r*dy, f0 r, linear dy; r>=1.
Sample_additions=[{sample_index,coefficient}], coefficient r*nx. Each adds
coefficient*sample.lifted_factor to used_F and
coefficient*sample.lifted_offset to used_f0, preserving full lifted coordinates.
Empty sample_additions is explicit. Terms may be empty: sum is the zero
objective, with used_F=[] (0*dy), used_f0=[], used_linear=zero(dy),
used_constant=0, factor=[] (0*du), offset=[], H=zero(du*du),g=zero(du),constant=0.
Empty matrices serialize as [] with their zero-row shapes inferred from dx/du/dy.
No implicit weights. Arbitrary units are declared algebra coefficients, not task
cost preference. Explicit accepted alpha/b history can be encoded in factor
offsets; boundary jerk uses .004s lattice, never held cell duration.

## Output schema

Top-level {schema_version:1,metadata,cases:[RESULT]}, order exactly input order.
metadata={namespace:"phase5_public_affine_horizon",policy_sha256,limits,scope}.
All matrices/numbers finite, booleans typed, exact integer shapes and rosters.
RESULT={name,success,error,source,scope,...}; error="" on success.
Failure emits refusal_code, source_diagnostic (original flags/value/errors for
public source), and no assembly/objective/evaluation fields. Source IO or policy
parse failure is process failure and creates no output. Per-case malformed
shape/source refusal is success=false; never partial/full relabeling.

Success source={kind,artifact_id,file_sha256,row_name,source_binary_sha256,
certificate_name,full_nominal_source_certified,actual_initial_shifted}.
For generic, certificate empty/full_nominal_source_certified=false, file hash
empty. actual_initial_shifted is public actual_initial != literal nominal initial.
It does not assert physical support for a shifted initial or chosen U.

Success assembly={nx,nu,N,cycles,recursive_states,lifted,samples,
nominal_cell_defect_residual_max,nominal_sample_defect_residual_max}.
recursive_states has N+1 {offset,control,initial}: nx,nx*du,nx*nx.
lifted={L,E,f,initial_selector,X_control,X_offset,X_initial,T,t} with L dx*dx,
E dx*du,f dx,initial_selector dx*nx, X_control dx*du,X_offset dx,
X_initial dx*nx,T dy*du,t dy. L diagonal I/subdiagonal -A, E row c+1
block B, f=[actual_initial;defects]. initial_selector first block I/rest zero.
X matrices come from independent pivoted solve, not recursive copies.
Samples ordered exactly source substeps, each {cell,cycle,half,recursive,
lifted_factor,lifted_offset,eliminated}. recursive/eliminated contain
{offset,control,initial}; lifted_factor nx*dy, lifted_offset nx.
Sample initial=A_prefix*P_cell_origin. eliminated initial also independently
uses lifted state selector * X_initial. No reset from nonlinear future states.

Success objective={terms:[CONDENSED],sum:CONDENSED}; CONDENSED={name,units,
used_F,used_f0,used_linear,used_constant,factor,offset,H,g,constant}.
Individual used_* retain sample additions. Sum.used_F vertically concatenates
term.used_F, sum.used_f0 concatenates term.used_f0, and sum.used_linear and
sum.used_constant sum term.used_linear and term.used_constant. Sum.factor
vertically concatenates term.factor, sum.offset concatenates term.offset.
All concatenation follows explicit input term order. Canonical sum.H,sum.g,
sum.constant accumulate individual condensed H/g/constant in that same order,
starting with exact zero. Do not recompute these canonical fields from the
concatenated factors. An independent concatenated-factor recomputation is a
floating-point arithmetic check within the frozen tolerance, not bitwise equality. sum.name="sum",units="declared_terms".
Fc=used_F*T,fc=used_F*t+used_f0,H=Fc^T*Fc,
g=Fc^T*fc+T^T*used_linear,constant=.5*fc^T*fc+used_linear^T*t+used_constant.
Sum also has factor vertical Fc and offset concatenated fc. Compare all these,
not just Hessians. Preserve nonsymmetric FP roundoff; no hidden symmetrization.

Success evaluation={controls,terms:[EVAL],sum:EVAL}; EVAL={name,lifted_value,
condensed_value,lifted_chain_gradient,condensed_gradient,lifted_chain_hessian,
condensed_hessian}; gradients du, Hessians du*du.
For y=T*U+t: lifted value=.5||used_F*y+used_f0||^2+used_linear^T*y+used_constant;
condensed value=.5U^T H U+g^T U+constant.
Lifted-chain gradient=T^T(used_F^T(used_F*y+used_f0)+used_linear).
Stored H retains raw floating-point entries. Let Hs=.5*(H+H^T).
Condensed gradient=Hs*U+g; condensed Hessian=Hs. These are the literal
derivatives of .5U^T H U, including possible nonsymmetric roundoff.
Lifted-chain Hessian=T^T used_F^T used_F T is independently reported; compare
it with Hs under the frozen arithmetic gate without overwriting raw H.
This evaluates algebra, never solves or declares nonlinear model cost accuracy.

## Preparation and frozen verification plan (not executed)

1. Root first statically reviews header/schema. Then implement separate Eigen/
yaml-cpp/OpenSSL-byte-verification library/CLI without model links; source-only
revisions retain each prior draft. CMake/build/freeze await separate dispatch.
2. Draft input preparation from archived_sources.json exact bytes and explicit
synthetic definitions. Producer fixtures include saved startup and [1,3,2,4]
maps, nonzero actual initial/history/targets, distinct eight inputs in every
cell, rectangular dense crosscomponent/crosscell F, sample additions and linear
progress terms. Root independent definitions stay independent.
3. Declare resource, type, roster and scale-aware arithmetic policy before any
new binary output. Every allocation/intermediate product/sum has finite/resource
guards. The following cumulative budget is mandatory in both loader and core. Freeze source/compiler/dependencies/binary/input/policy/archived source
bytes; empty-schema preflight is separate and retained.
4. First numerical attempt: independent pivoted lifted elimination vs recursive
maps, all sample P/M/offsets, full term/sum objective/value/gradient/Hessian,
nominal-source identities and initial-shift behavior. No epsilon retuning.
5. Negative controls: authentic failed/unsupported packets; last-cycle fields;
tied input columns; actual-origin reset; missing initial/sample P; dropped
linear/constants/cross terms; half-square weight error; omitted/fabricated rows;
malformed shape/type/nonfinite/resource overflow; true scope flags. Refuse
altered outputs in independent checker even if other fields are consistent.
6. No solver/main/geometry/trust/admission/model/plant/timing/untouched seeds/task
videos. This source contract alone adds no new renderable physical result.

## Revision 2 cumulative budget and static review record

Root review requested literal polynomial derivatives and an aggregate numeric
budget. Revision 1 stays immutable, including its erroneous raw-H derivative
statement. This revision changes no model, build, numerical output or fixture.

Limits additionally fix max_problem_numeric_elements=8000000 and
max_cli_numeric_elements=16000000, counting input matrices/vectors, retained
assembly/objective/evaluation arrays, planned dense scratch matrices and numeric
serialization arrays. max_matrix_elements=2000000 still limits any single array.
Before Eigen allocations, the loader inspects scalar types and exact shapes,
uses overflow-checked size_t addition/multiplication, and computes a conservative
whole-problem plan covering all cells, sample views, factors, term evaluations,
sum factors and elimination workspace. Before loading all cases, it also checks
the aggregate declared plan against the CLI budget. A shared CliBudget survives
case failures; each ProblemBudget consumes its own and shared remaining budget
before every explicit input/output/scratch numeric allocation. No release/reset
allows failed cases or temporaries to evade the cumulative limit. Nested Eigen
expression scratch must either be bounded by the planned conservative workspace
or explicitly materialized and charged; implicit unbounded allocation is refused.
Public artifact documents are byte capped and shared/read once, not recopied per
case. Parsed document scalar counts and source numeric materialization also count
against the CLI total; per-case source views avoid owned document clones. Refused
source diagnostics use bounded original node references until serialization.
JSON parsing/strings/container overhead is bounded separately by byte, roster
and factor/sample limits; the numeric budget does not claim a process RAM limit.

Literal condensed derivatives: raw H remains stored; gradient=.5*(H+H^T)*U+g,
Hessian=.5*(H+H^T). Independent full-factor chain computations retain their own
roundoff and are compared within a preregistered arithmetic gate. No hidden
symmetrization of stored H, no solver claim, and no performance acceptance.

## Revision 3 sum contract and v1 scope

This source-only revision resolves the independent math review comments.
Revision 2 and its record remain immutable. No implementation or numerical
execution was performed. Sum matrices/vectors use the complete used_* fields
and input-order accumulation described above. When terms are empty, all zero
shapes are defined explicitly; sum name/units remain sum/declared_terms.

Limits and arithmetic tolerances in this v1 interface are fixed to header values,
not configurable by a policy or C++ caller. The core and loader reject any
changed limit/tolerance value. Policy must repeat the exact values for provenance.
max_cells=16, max_samples=512 and the 8m/16m cumulative numeric budgets define a
bounded development diagnostic envelope intended for the reviewed N1/N4
fixtures. They do not assert support for the project's N20/.8-second horizon,
1.5-second horizon or all problems below the individual count caps: cumulative
resource checks may still refuse a dense case. Public source samples require
2*sum(cycles)<=512, so this version also does not guarantee every long duration
allowed by another module. Larger resource envelopes or configurable limits
require a separate reviewed version and freeze. No silent N20 support claim.
