# Version4 actual FIRST claim source contract

SOURCE3C2B3B2C is source/static only. Prerequisite backup:
9820b0d78a61e78f0be002f969ee307458fef494. No compiler, resource planner, Case,
claim/helper/IO/metadata/parser/Model/numerical/plant/main/scorer function ran.
Phase5 remains NOT_ACCEPTED, Phase6 NOT_STARTED. Existing checker, immutable
d3d4 freeze, accepted Phase4 evidence, source histories and failures remain.
A separate exact-source/build/SDK/FP/protocol review/freeze is required before
any execution; this contract is not a runtime release.

## Private authority and planning

Only V4 creates ClaimCaptureData in the actual private release. A caller's plain
ClaimCaptureFactsV1 value cannot be injected into a forecast or permission. No
public claim factory, IO callback, caller SHA certificate or success flag exists.
The private source token is the actual context tag; the same real Case/Batch
already created from the reviewed invocation survives preparation. claimCaptured
checks that exact token/Case plus member admission and one-entry refusal state.
The source contract role is required in the exact reviewed closure.

V4 prospectively adds448 live,524288 cumulative and324 output bytes to the
member+context plan; unchanged original resource caps apply before Case creation.
Its versioned planner explicitly adds324 to outputCeiling; preparation checks the
same versioned delta. Generic/member-only/context-only plans do not gain output
credits or claim reservations. No SDK1M, future W, member transient hash workspace
or manifest allowance is borrowed. All new payload has real reservations before
materialization; old bootstrap/provider/allocator/RSS/full-flow limits remain.

ClaimCaptureData has its reservation before source token, expected324-byte array,
readback325-byte array and facts. Exact selected payload:

| Held fields | Logical slots |
|---|---:|
| Facts31 Count values |31|
| Facts39 booleans |39|
| Three signed64 values, two errno ints, one stat-target enum |6|
| Three retained64-character SHA arrays |24|
| Expected324 and actual-read325 byte arrays, each rounded/8 |82|
| Retained private source token and member claim-owner identities |2|
| Total actual selected payload/ticket |184|

Bounded path/error strings use actual metadata bytes and ceil(length/8) copy
charges separately. Constant stage labels and ledger/refcount/allocator bookkeeping
are excluded from numeric evidence payload. Arrays/strings/token/facts die before
184 ticket; the shared Case state survives that ticket. Source tag points to an
independent context tag, not back to member storage, so there is no owner cycle.
The release and successful forecast retain the private data/ticket.

A real256 workspace reservation precedes component256-byte storage, two native
stat objects, digest/hex/control/descriptor/provider handles. Future Linux source
static_assert requires each stat<=512 bytes and dev/ino/size types<=64bits. The
array/stat/digest fields occupy at most164 rounded slots; remaining92 slots are
conservative bounded small-control/hash/descriptor capacity, not a claim that92
named evidence scalars exist. Workspace is a declared logical source bound, not
compiler stack/RSS/provider-allocation inspection. OpenSSL opaque provider/global
allocation and allocator/refcount machinery are excluded from full RSS claims,
as in existing identity paths. That closure remains a separate gate.
A separate8 metadata frame is reserved. Thus184+256+8=448; every workspace dies
before its reservation. Expected and writer hash handles are released before the
next stage; a prefix digest uses an actual independent EVP context copy.

## Exact contents and safe descriptor path

The record is exactly the original format: review_sha256, protocol_sha256,
producer_sha256, invocation_sha256 lines in that order, each with64 lowercase
hex characters and newline. Sizes79+81+81+83=324. Content is built only from the
private actual verified release identities, with bounds and copy charges before
materialization. expected_ready is set only after complete fixed-array assembly;
expected_digest_known only after actual SHA calculation/retention. Neither is a
claim that file IO has occurred. Allocation or quota failure may leave only the
private refusal and absent path/content/digest fields.

The absolute path is bounded4096, nonempty, no NUL or trailing slash; components
are1..255 bytes, no empty/dot/dotdot, at most64. The entire path is checked before
creation. Actual metadata/copy/scan charges precede its owned copy. path_copied
marks assignment success; partial path copy is not an original known path.
Directory traversal opens root and each parent with O_DIRECTORY|O_NOFOLLOW|
O_CLOEXEC, using bounded component storage and actual descriptor-relative opens.
No directories are created. Root/parent observations and final file names are
independent of caller certificates. Read-only open also uses O_NONBLOCK so an
unexpected nonregular substituted entry cannot block before stat validation.

Exactly one O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC0600 create is attempted.
An existing/partial claim refuses and is never removed or retried. The new FD must
be an empty regular single-link file with actual mode0600; umask/permission
mismatch refuses without chmod repair. Actual dev/ino/size/links/mode facts are
observed from fstat, with target/known state before each attempt. Negative native
size remains in signed last-stat data; incomplete unsigned identity groups are
explicitly unavailable. Safe descriptors are not a filesystem race lock or
physical storage attestation; future runtime requires stable trusted storage.

## Actual prefix IO, digest coverage and durability

Before creation, remaining real unique-output quota must accommodate324 bytes.
The Case is single-threaded, with no claim IO callbacks/reentry. Each successful
write advances written_bytes by only the actual returned positive count; unique
output charge and output_charged_bytes advance by that count. Attempted-request
bytes/calls are distinct from actual bytes. Request-rounded copy work and bounded
operation work are paid before each OS call; short writes and EINTR do not mint
full-record success. write_complete reflects actual324 bytes independently of
later SHA/fsync/close success. Zero/failed/impossible writes refuse.

The writer SHA is updated only from that actual successful byte span. Each saved
prefix digest uses an independent clone/finalization of the actual updated
stream; metadata64 and copy/work72 are paid before retained hex materialization.
The immutable retained digest has an explicit writer_digest_bytes coverage count.
If later update/clone/fee fails, an older retained digest remains attached to its
older prefix; it is never relabeled as the current physical prefix. Hash-state
booleans mean last successful init/update history, not retained live EVP state or
a saved digest. Expected/writer/reader digests and their known flags are separate.
No digest is recomputed during failure handling to fill missing evidence.

After writing, actual writer FD identity/size is rechecked. File fsync and parent
directory fsync have separate attempted/success flags. The written FD is closed
once, with actual result recorded; EINTR/ambiguous close is a refusal and never
retried. No close failure restores authority. Cleanup close work64 is prepaid
before any descriptor creation; real close counts/results and failure errno are
retained even during unwinding. Cleanup never unlinks/truncates/overwrites.
Directory traversal closes are recorded separately from final-parent flags.

Readback independently reopens the same basename from the held parent FD with
O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC and a fresh offset. Its actual regular/
single-link/mode/dev/ino/size must match the created file before reading. Returned
bytes go into the owned325 array, whose defined prefix is exactly read_bytes.
The actual reader SHA and byte comparison use those returned bytes, never the
expected array as a substitute. A bounded one-byte sentinel detects growth after
324. That extra byte/digest prefix is retained before refusal. Real EOF, complete
length, comparison prefix and complete SHA matching are separate facts. Premature
EOF, changed identity/size/content, missing digest or extra bytes refuse.

Final reader FD and nofollow directory-name stats must still identify the same
regular single-link0600 file of324 bytes. identity_stable describes these actual
observations, not permanent immutability after the last observation. Complete
readback requires EOF324, byte equality, all three saved SHA matches at coverage324,
actual unique-output324, file/directory fsync and checked writer/reader/parent
closes. It precedes the constructor. historical_complete remains true after an
actual successful claim; current complete/refused and member authority remain
separate. A later/repeated claim entry cannot recreate or authorize the file.

## Refusal, last-result history and publication limits

All normal OS attempts have a precharged128 control fee plus bounded copy work,
with a maximum1024 metered attempts. Read/write EINTR may continue only on the
same existing FD within this cap, not a new FIRST claim attempt. Other opens,
stats, fsync and closes are not retried. Up to four cleanup descriptors can close
under the prepaid cleanup allowance. No completion theorem assumes the OS will
avoid short/EINTR/quota failures.

Actual last non-close IO result retains its own stage, attempt index, return,
errno and known flag. Current stage cannot relabel an older successful result
when the next quota/hash/precondition fails. Close result has its own actual
close counter and signed result; missing results/errors remain Missing. Last-stat
current target/known state is separate from committed parent/created/writer/
reader identities and sizes. First refusal stage is frozen. Error detail<=512 is
copied only on the first refusal, after actual metadata/copy payment. If that copy
fails, it stays missing; reentry cannot replace it with a later error. Claim's
versioned member refusal helper also prepays rounded error-copy work.

Any claim exception poisons claim and member, including allocation/quota/hash/
close/read/name errors; valid/recheck gates then reject Model and retry. A created
partial/failed file is left in place. fsync failure does not promise crash durability.
Private release ownership can retain captured prefix/status where allocated;
source allocation before retention can fail, and detail may be absent. There is
no public early-open failure source, bridge or publisher, and no unconditional
preservation promise across process death or discarded owners.

Successful OwnedPublicForecast exposes only a const borrowed facts pointer,
checking private token/sameCase. Caller-built records cannot mint this owner.
The original metadata EvidenceGuard/source/generation rules apply.93 extra typed
facts include counts, booleans, signed errors/results, stat target/stages, SHA/
coverage, actual file path/bytes/identity and explicit missing. No large temporary
field roster is constructed; fields stream individually under the extra8 frame.
Legacy forecasts keep actual_claim_identity Missing. Historical claim success
is not process/PID/arguments/stdout/stderr/exit evidence or phase acceptance.

The source does not depend on output_chunks or add a CMake cycle. Original claim
body and legacy V1/V2/V3 successful behavior remain. New source metadata invalidates
inheritance of the old provisional8MiB/full-manifest bound. Full byte/cumulative/
lifetime/RSS closure, public early-failure publishing, reference reconstruction,
rootREADY/whole reader and all runtime/plant/main/scorer work remain deferred.
No simulation/render/motion video is produced or claimed in this source-only unit.
