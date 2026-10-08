# Source normalization stage 2B — pending independent static review

This implements the bounded genuine-forecast normalization layer. No compiler,
configuration, empty probe, matrix/numeric check or Model/plant/solver/main/scorer
invocation occurred. C++ validation expressions are source, not passing evidence.
Phase5 remains NOT_ACCEPTED and Phase6 NOT_STARTED.

## Genuine source and full/refusal outcomes

The only input is move-only OwnedPublicForecast. There is no public RawResult,
archived-carrier, AlgebraTest or caller-certificate factory. NormalizationOutcome
moves the original owner directly into its value storage. Ordinary validation,
quota and container-allocation refusals retain it and return a separate wrapper
reason. Original successes/failures, partial physical values/maps, first uncertified
index, source errors, friction and clipping are never rewritten or discarded.
Detailed refusal allocation failure uses a fixed fallback label instead of
fabricating success or modifying the original result.

Full output requires complete successful value/has-final-state/extension flags,
first_uncertified==-1, empty source errors and exact N/T/2T values/maps rosters.
Source review/protocol/producer/invocation and compiled original certificate
identity remain bound by the genuine stage2A owner. Transport/structural refusal
prevents full output even if a raw success object was retained. No shortened
horizon, tail, fallback model, cost/problem or controller command is produced.

## Literal records, command law and cumulative coefficients

Every point/map index/half/elapsed time, nominal control, cycle origin and cell
origin matches its own source. The first cycle is anchored in actual q/v/C/w/s/r,
not a nominal future or reset history. All recursive cycle states separately obey
the original4ms w_next=w+h*alpha, C_next=C+h*w_next, s_next=s+h*r+.5*h*h*b and
r_next=r+h*b. Physical halves share that new C/w; no second command update is
inserted at half2, and coarse-cell duration never replaces4ms.

Substep_map.state retains physical point q/v/C/w plus the value substep's own
cell-origin polynomial s_reference/r_reference. Cycle_map.state retains the
recursive cycle endpoint. Half2 physical q/v/C/w matches that cycle, and its
derivative matrices match the cycle matrices, but its s/r and associated defects
are NOT forced to equal recursive cycle s/r. Both literal expressions and native
defects are preserved. A cell_map remains the exact final cycle record; its local
A/B/defect/origin still refer to that last cycle.

Both local and cumulative matrices/shapes/defects are finite. Native cumulative A/B
composition is checked against the preceding COMPLETE cycle within the same
cell (identity/zero at cell start), separately for each half and cycle. Both local
and cell-origin direct nominal defect identities are evaluated. A separately
evaluated propagated-defect recurrence is NOT implemented or claimed. Local
physical-target/command/progress block identities use the unchanged public law:
full4ms command history in both halves, independent virtual progress, physical
b sensitivity zero. Fixed nominal identity gates remain abs=rel=2e-13, matching
the old algebra defaults; no caller tuning or gate repair is enabled. Exact
source parity uses numeric equality, treating signed zero as equal. Independent
future build/runtime review must freeze compiler arithmetic behavior and retain
any failed identity rather than changing it after outputs.

Wholecell/sample views always expose native cell_A/cell_B/cell_defect/cell_origin.
Cycle accessors expose the same cumulative fields of the validated native cycle
records. They do not relabel cycle-local fields. No raw matrix/state copying or
nominal offset reset occurs, and cell input identifiers remain independent.

## Budgets and lifetime

Before validation loops, the same bound CaseBudget reserves the complete logical
inventory N*1241+S*1243 and640 numeric scratch slots. Every map check charges640
reused-work slots before operations. Scratch actually stores at most120 doubles;
remaining reservation conservatively covers scalar/stack work. No Eigen product
temporary or dense sample selector is materialized: bounded scalar products are
finite-checked and compared to original native coefficients. Wholecell duplicate
checks stream references and allocate no numeric buffers. These charges fit the
previous prospective sample-work schedule; implementation support is not a
runtime or allocator measurement.

Inventory1241/1243 prices the complete1238-coordinate borrowed block plus3/5
logical topology values. Internal views store only a source index/kind; cell,
cycle, half, tick and sample identity reference/derive from the validated raw
records/mesh. Thus there are no uncounted copied matrices or extra topology
arrays; a conservative logical borrow reservation is retained anyway. Actual
STL/refcount/container/string overhead remains outside the numeric ledger and
must not be advertised as an all-process/RSS bound. Metadata/output serialization
quota enforcement is still the future capture layer's obligation.

After all record checks pass, the outcome anchors the genuine owner BEFORE new
container allocations. Quota/allocation failure therefore keeps full original
ownership. Output containers are move-only; their public cells/samples are const
and their block views cannot be copied. Shared anchors retain all stage2A source/
input/profile/SDK/raw tickets while outcomes or inventories reference them.
Inventory destruction destroys views before its own reservation; outcome drops
maps before its original owner. Move-only extraction/moved-from behavior is
explicitly part of the deferred independent audit. Normalized views borrow raw
data; callers must keep the owner/inventory alive for any borrowed reference.

All7 claims remain fixed false: segment, two-sided ball, admissibility, execution,
safety, uniform accuracy and controller readiness. Nominal normalization is not
a finite-neighborhood, physical accuracy, trust or trajectory certificate.

## Scoped version extensions and remaining work

The accepted stage2A model_boundary.hpp/cpp are preserved in
history/model_boundary_before_stage2b. Their necessary extensions provide ONLY
private budget/plan/certificate bridges to NormalizationFactory and add the
normalization source/target roles to the future complete closure. No public raw
factory or mutable Model/result accessor is introduced. A pre-canonical-check
normalization header/cpp snapshot is retained separately. Foundation, original
Model/checker/profile and old freezes/Dell metadata are unchanged.

Stage2A counters refer to top-level boundary API attempts, not every internal
base Model/SDK/friction operation within them. The normalizer invokes ZERO new
Model constructors, metadata queries or rollouts. It performs no affine/cost,
capture/reader, solver/controller/geometry/stopping/timing implementation.
Those remain separate source/review/freeze/runtime gates. No runtime release is
created by the source files or the at-most-once claim mechanism.
