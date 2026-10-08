# Foundation stage 1 source review notes

Only read-only source inspection and text edits occurred. No CMake configure,
compiler, empty probe, kernel, numeric test, Model constructor/metadata/rollout,
plant, solver, main or scorer has run. This is implementation source awaiting
independent static review, not passing build/runtime evidence.

## Mesh and resource implementation

`CycleMesh` and `ResourcePlan` have private default constructors and immutable
public views. Checked uint64 additions/products reject overflow before storage.
Unsigned plain decimal durations must lie exactly on the 4 ms lattice; no
floating rounding, exponent, signed/whitespace input or cover policy is enabled.
UniformExact, BalancedInteger and ExplicitCycles preserve the reviewed ordering
and reject unknown enums, empty/zero cells, extra explicit data and wrong sums.

Resource ceilings are version-fixed compile-time constants. Cost shape inputs
describe actual aggregate counts: every addition coefficient block has 30
columns, so its total count must be divisible by 30. The source-plan illustrative
C=200000 envelope is a prospective budget allowance; an actual full-row shape
uses a multiple of 30, such as 199980. Actual per-term/parent-row shape validation
is still a stage-2 responsibility. Zero-row pure linear terms remain representable.

The implementation translates the reviewed raw Map2441/Substep52/State30/Cell9
and normalized1241/1243 integer formulas, K+1 evaluation blocks and canonical
sum workspace. The r term bound is the declared largest term row count instead
of always256. Admission is conditional on complete live, cumulative and output
plans; it never increases ceilings or omits data to pass. DenseAudit conservatively
prices all additional declared audit/work arrays in the output bound as well as
live/cumulative storage. This can refuse more cases than memory-only preflight;
it does not claim the previous compact output table measured dense output.

`SDKplanningAllowance()` is only 3*raw+1m logical planning reservation. It does
not instrument SDK allocators, vector capacity, YAML/STL/string overhead or RSS.
Later raw-result ownership must retain a ticket for that whole lifetime. No raw
result or SDK allocations exist in this stage. File hashing uses a 64 KiB chunk;
bounded constants parsing is a separate static metadata operation (at most8MiB),
not a numerical-buffer or all-process memory guarantee.

`CaseBudget` shares its state with move-only lifetime tickets. Ticket destruction
decrements both case and shared-batch live storage exactly once; reserve checks
both the case's planned live ceiling and the fixed batch64m live ceiling before
committing any counter. Tickets intentionally retain case/batch states across
owner destruction, so overlapping retained case outputs share the global tracked
numeric-live limit. This is not a bound on other batches, all process memory or
opaque SDK/STL allocations. Cumulative case and shared batch charges never
decrement. Allocation failure after reservation retains cumulative charges.
Preflight rejection before a charge/allocation retains prior charges and makes
no allocation. `OwnedNumericBuffer` reserves before allocation and destroys data
before its ticket; move assignment frees old data before moving its reservation.
Ticket owners for external/borrowed storage must follow the same lifetime order.
There is no public early-release operation, numeric-buffer resize or silent
capacity growth. Ledger use is explicitly single-threaded per batch.

Actual encoded metadata and unique output bytes have separate monotone quotas.
The future writer must charge metadata bytes to BOTH metadata and output ledgers,
charge each unique blob exactly once, and verify referenced chunks. The foundation
does not yet claim a capture writer enforces those obligations.

## Current state and preview

Fixed seven-coordinate arrays separate physical q/v, accepted C/w and committed
s/r. Caller-supplied observer/history facts must bind the same completed tick,
accepted-command sequence, immutable observation ID and transaction ID; partial
and in-flight records refuse. First live mode requires nominal==actual initial
with exact numeric equality (no tolerance or substitution); +0 and -0 compare
as equal numerical coordinates. Current freshness policy is explicit, finite and
at most one4ms macro cycle. This is an initial conservative source policy, not
a measured scheduler guarantee or validation of the caller's clock/contact fact.

Static ranges are parsed from exactly the SHA-verified bytes and have private
construction. q is strictly inside the original joint ranges; C/w/s/r use the
original closed nominal domains. No finite perturbation radius, future branch,
contact, safety or physical accuracy certificate is inferred. Full original
Model/SDK metadata and derivative support remain stage-2 gates. Range/context
witnesses use copy-only value semantics to avoid a moved-from state with emptied
identity fields. Arbitrary finite AlgebraTest initial shifts, including negative
r, have a separate type and cannot enter `first4msRequest`.

The literal preview law is w_next=w+.004*alpha, C_next=C+.004*w_next; progress
separately uses s+.004*r+.5*.004*.004*b and r+.004*b. Both2ms progress references
are retained and domain-checked; no physical step is performed. Candidate alpha
stays distinct from implied preview acceleration (w_next-w_previous)/.004.
Conditional command jerk uses that literal reconstruction and the previous
accepted alpha on the4ms lattice. Actual later supervisor acceptance still
requires reconstruction from actual accepted w, logging and revalidation.
Neither a whole-cell endpoint nor measured physical v substitutes for history.

An early written candidate-alpha jerk expression was corrected before this
packet. `history/pre_command_preview_fix/` preserves the exact preceding patch
text and explains its recovery. No executed result was repaired or rerun.
An independent review also found the original batch state lacked a shared-live
counter; `history/pre_batch_live_fix/` preserves that exact source/manifest snapshot
before adding cross-case simultaneous tracking. No hard ceiling was increased.

## Identity and remaining stages

Hash observations only report actual read bytes and caller-declared expected
hash agreement. They do not independently authorize a run. Current producer
identity reads the Linux kernel's `/proc/self/exe` binding, checks ELF magic and
rejects the archived f1 hash. Other hosts refuse this live-ELF API; no arbitrary
caller-selected executable can masquerade as the running producer. Static range
parsing rejects duplicate root keys and malformed range/limited rosters; parsing
does not replace the eventual full fixed-profile/SDK/XML metadata validation.

The next separately reviewed source stage must implement permission/complete
live Model profile binding and move-only genuine result ownership, preserving
all original successes, partial data and failures. Normalization, compact/full
affine/cost algebra, half-first Hessian, capture/readers and independent runtime
verification are not implemented by this foundation stage. Their absence is
explicit; this packet is not represented as the complete live adapter.
