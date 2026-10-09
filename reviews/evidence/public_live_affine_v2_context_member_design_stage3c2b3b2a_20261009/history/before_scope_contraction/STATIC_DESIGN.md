# B3B2A execution/provenance/context snapshot design only

Checkpoint e5dd7335c2f7f24622712e3b81935ed016324e29 was independently rechecked:
HEAD==remote master, clean, all57 B3B1 payload bytes/SHA match READY9e04c33e.
This packet contains STATIC DESIGN and original before guards only. No canonical
or Git edit, implementation/new target, CPP/compiler/IO/Model/metadata/parser/
serializer/numerical function execution. It does not dispatch B3B2 implementation,
reference reconstruction, early-failure owners, root READY or any phase gate.
Phase5 NOT_ACCEPTED, Phase6 NOT_STARTED; original checker/freezes/archives retained.

## Actual facts, lifetime and smallest retention sites

| Required fact | Existing real capture position and owner | Minimum proposed retention / what remains missing |
|---|---|---|
| Actual producer ELF | permission(): observeCurrentProducerElf, later recheck; ForecastReleaseState.producer survives via invocation/profile/forecast | Existing actual identity remains. A path or requested digest is not its substitute. Process argv/exit/streams do not follow from ELF success. |
| Protocol eight artifacts | permission() verifies exact protocol fields, parses each Artifact and verify(identity), then stores files+file_roles | Retain existing role/path/hash/bytes together and group=Protocol, observed input sequence if needed, checked review/protocol parent binding. Existing map gives role-sorted retained order; do not relabel it original document order. |
| Source-closure members | permission(): readDocument(source_closure) hashes the EXACT parsed bytes; each original Artifact role/identity is available before verify then local roles/paths maps die | FileIdentity already appended to r.files. Retain role and actual parent manifest/group/original ordinal at this point, not after Model or by reparsing a caller certificate. Existing full identities must never be mislabeled entirely NOT_RETAINED. |
| SDK file members | Same checked sdk_manifest loop, actual role and verified FileIdentity before push | Same paired retention. Keep source versus SDK parent/group distinct; do not deduplicate two legitimately different manifest memberships by path. |
| Loaded library membership | Parsed loaded_libraries list is matched against verified SDK members; r.libraries survives; actual verifyLoadedLibraries already performs Linux loader/map checks | Declared membership and actual successful loader recheck are separate. Existing library path/SHA/bytes survive. Retain original SDK member association/list ordinal while names/verified map are alive. Actual mapping/inode observations require capture inside existing verification, never inferred from declared library list. |
| Bound cost input | prepare(): verifies frozen cost artifact before InvocationStorage; then appends cost identity to r.files | Append role=cost_input paired with file, group=Invocation, actual parent invocation identity. Existing r.cost input/private semantic binding survives, but current aggregate role vector is missing this entry. |
| Immutable attempt claim | claim() inside open() BEFORE constructor; already O_EXCL writes exact four binding lines/fsync/close | New private ClaimCaptureV1 must record actual opened FD/dev/ino/bytes/write cursor/first error and successful-write SHA, not hash the intended string and call it stored. Independent actual readback/EOF/SHA and file+directory fsync needed before claiming complete. Retain in existing release/open profile lifetime without retry/deletion. Existing claim path alone remains insufficient. |
| Actual ctor/query/rollout attempt counts | Existing release counters increment immediately before actual entry; ModelOpenOutcome has booleans/observed metadata/refusal; forecast owns transport/structural/raw errors | Preserve real counters and current/historical meanings. Outcome success is not process exit. Earlier OpenStorage facts may already exist but no current complete-affine capture-owner bridge reaches them: early-failure publication still missing/deferred. |
| Context original inputs | validateLiveActual receives observed,command,progress,nominal,current,ranges; original age/contact/completed/anchor fields disappear on return | Proposed source-bound immutable ContextInputSnapshotV1 copies EXACT supplied typed inputs at entry, validates those same owned bits, retaining original flags/ages/anchors/IDs separately from validated actual state. Calling inputs are assertions, not sensor/process attestation. Needs actual Case admission before copy; legacy validation alone cannot fund it. See lifecycle budget below. |
| Actual process argv/cwd/executable | No driver/launcher/argv recorder exists in current library | Future reviewed Linux OS-backed capture at actual program entry/spawn could retain exact argv boundaries and paths. /proc/self/cmdline is a capture-time snapshot, not proof of original immutable spawn argv. Do not accept expected argv, invocation JSON or caller process certificate as actual argv. Still missing in this minimum implementation. |
| Exact stdout/stderr/exit | No parent collector/pipe tee/wait-status owner exists | Must be captured by an actual separately reviewed launcher/parent throughout child lifetime, then EOF/waitpid status. In-process library return cannot know its future process exit. Empty streams and exit0 are not defaults. Remain mandatory missing; no launcher/main or redirection in this scope. |

readDocument already recomputes SHA from exact bytes then rechecks file; it is not
just a path-only parse. Its existing immutable-input assumption remains, not an
adversarial filesystem lock. New snapshots must preserve observed/expected/checked
statuses separately and keep actual source origin/parent bindings.

## Concrete current defect and correction scope

At model_boundary.cpp current permission() top artifact loop pushes8 file_roles
and8 files. The source and SDK loops append files ONLY; prepare() later appends
cost file ONLY. Each closure must be nonempty. Thus even before prepare:
files>=8+1+1=10, file_roles=8; after prepare files>=11. Metadata iterates ALL files
and calls verifiedArtifactRole(i).at(i), first out-of-range is index8 (ninth record).
No runtime was invoked to establish this counterexample; it is a source/integer
fact. The current preserved version can refuse instead of producing a full capture.

Smallest first implementation: append one role to EVERY actual files append and
store actual source/SDK roster counts plus parent/group mapping; require lengths
match before any getter/catalogue/metadata use. Preserve top artifact ordering,
original nested member sequence and cost insertion separately. If one vector
allocation fails midappend, never issue a complete witness/getter; keep available
prefix with explicit recorded incompleteness. Prefer atomic paired record or
pre-reserved paired lists, not a guessed synthetic role or zip to minimum length.
Legacy files consumer order and actual stored failures must remain recoverable.

Change metadata missing text to two facts: verified member identities ARE held;
complete role/parent/ordered roster/loaded association capture is currently missing.
The current binary cannot backfill those lost associations without a new reviewed
snapshot execution. A future actual permission parse can retain them while locals
exist. Do not silently reinterpret the accepted old source checkpoint as repaired.

## Context snapshot authority and budget

Raw inputs are observed q/v14, boundary2, age1, completed/contact2=19 slots;
command C/w/previous-alpha21,boundary2,completed1=24;
progress s/r/previous-b3,boundary2,completed1=6;
nominal State30+boundary2=32;
current boundary2,maximum_age1,no-command-in-flight1=4. Total85 literal numeric/
integer/boolean slots. Proposed8 capture/status/cursor fields make93, rounded96
owned slots. IDs: observed/command/progress/current each observation+transaction
string, eight strings bounded256 BEFORE copy; exact raw values are retained, no
postvalidation replacement or finite/zero coercion. Ranges/identity must remain
strongly owned by existing immutable domain witness; no dangling caller reference.

LiveActualContext is currently created BEFORE prepareFrozenLiveInvocation creates
CaseBudget. Therefore adding96 into standalone validateLiveActual with no budget
would be unaccounted. Minimum viable versioned branch must first parse/check the
reviewed frozen mesh/factor plan, create the SAME genuine CaseBudget, reserve96
BEFORE copying inputs, then validate the owned snapshot and construct invocation.
Suggested prepareFrozenLiveInvocationWithContextSnapshotV3 is PRIVATE-source-bound;
it does not accept a caller budget token or archive carrier as live witness.
The original validation algebra, margins, exact boundary/equality and typed live
versus algebra separation remain unchanged. Legacy path leaves snapshot missing.

Versioned request planning must explicitly include actual96 storage and real85
input-copy charge (plus actual metadata/copy/reuse), under unchanged64M live/512M
case/1.024B batch caps. Keep original planResources/V1/generic unchanged. Do NOT
spend the V2 manifest160/16 credit, future cost W, supposed SDK1M slack or an idle
pool for a pre-Model context object. Record actual allocations/ceilings and refuse
shortage. Snapshot is noncopy/immutable shared ownership: copied Context witnesses
may share one ticket/owned bytes, not clone arrays without charges. Ticket must
outlive input arrays/strings; same-case binding prevents cross-invocation reuse.

The minimum success-path snapshot does not itself provide a new public early-
validation-failure owner. Capturing before validation then throwing can destroy the
local snapshot: do not claim complete failure retention/publication in that case.
Original caller objects remain caller-held; early failed-context owners and their
archive bridge remain explicitly missing unless separately scoped. This is a
required boundary for root's later implementation decision, not hidden completion.

## Minimal proposed files and ordered implementation gates

1. model_boundary.hpp/cpp plus capture_metadata_internal.inc: fix actual aggregate
   role alignment; retain grouped source/SDK membership and cost role; correct
   held-versus-missing wording; bounded readonly genuine getters. Freeze/review/
   backup before anything else. No process envelope, new Model call or early owner.
2. model_boundary.hpp/cpp (and a small reviewed claim snapshot header if needed):
   add actual claim FD capture/readback to existing claim lifecycle, original
   one-attempt/first failure preserved. SharedCaseBudget real tickets/metadata/output
   charges for the actual new bytes; parent-directory safety/fsync requirements
   need new reviewed protocol/source freeze. No retry or fake success certificate.
3. foundation.hpp/context.cpp/resources.cpp and model_boundary.hpp/cpp: propose
   immutable raw context snapshot and explicit versioned SAME-case preparation/
   planner before any copy. Default validator/plan unchanged. Snapshot source-kind
   InputAssertionsValidated is distinct from measured physical observer evidence.
   Actual lifetime/copy/metadata budgets must pass independent design/source review.
4. capture_metadata_internal.inc + relevant source contracts/provisional schema:
   borrow real snapshots only; do not expose whole mutable DOM. Newly available
   fields replace missing only when actual private snapshot/first-error/identity
   is present. Preserve source type/index/order/IEEE bits and schema version. Full
   phase/file/reconstruction acceptance still false. The B3B1 default byte bound
   must be revisited for added member/context fields, not reused unchanged.

Parent execution launch/argv/stdout/stderr/exit, sensor attestation, root READY,
reference reconstruction, inverse file closure and early-failure owners are NOT
minimum implementation targets. root must authorize a concrete next source scope;
this design creates no task/thread, implementation, run or permission certificate.

## New accounting obligations, not an approval shortcut

Role/group facts are metadata. Prefer moving/retaining existing identities and
actual roles once, no second path/SHA vector. Keep two actual roster boundary counts
(2 logical slots) if compatibility requires deriving groups in existing aggregate
list; exact encoded role/parent/ordinal metadata bytes must be charged before copies/
serialized output, under8MiB aggregate. Preflight release parsing predates CaseBudget:
its bounded owned metadata is external preflight, not silently Case-accounted.
Case attachment needs explicit real admission before Model; new counters cannot
be called free. Full preflight YAML/EVP/STL RSS is not measured by numeric tickets.

Claim proposal:16 held fact/control slots,48 mutually exclusive IO/hash transient
(before constructor, after actual Case creation); cache128=16, digest64=8, tokens4,
FD/cursor/control20. Counts/outcomes become valid only following actual IO. A new
ledger reservation/metadata/unique output schedule is required; original claim
bytes are currently unmetered output, so do not charge an imagined prior file.
Observe successful writes once, retain partial bytes/FD identities, no overwrite.
Actual returned early Open outcome/archive publication is outside this design.

Added context96+provenance counters2+claim16 =114 held candidate slots, not already
reserved. Initial context copy85 and all subsequent copies/transient hashes/caches/
bytes must consume real planned charges. This is a proposal for versioned planning,
NOT a claim existing plans have spare capacity or complete flow fits. Exceeding
metadata/live/cumulative/output must preserve failure and remain incomplete.
