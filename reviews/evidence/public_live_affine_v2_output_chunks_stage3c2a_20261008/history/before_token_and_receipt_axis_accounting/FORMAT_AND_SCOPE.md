# Typed numeric chunks 1 — low-level, source only

No function was executed, configured or compiled. These interfaces implement
one provisional numeric file and independent readback only. They do not connect
raw/normalization/affine/cost inventories, reproduce mathematics, select weights,
publish CAPTURE_READY, authorize Model/solver/controller work or accept research.
Phase5 NOT_ACCEPTED; Phase6 NOT_STARTED.

## Receipt and safety envelope

A sealed NumericChunkSpec has a safe ASCII role/name (1..128 bytes), supported
scalar kind/classification and at most4 axes. Axes multiply with checked u64
arithmetic; empty axes denote one scalar, any zero axis denotes zero elements.
Count is at most12m. All caller fields are bounded/validated BEFORE owned copying.
The file name is ONE safe component ending `.provisional`; no slash, NUL, dot/dotdot,
traversal or symlink path is accepted. The absolute root is bounded4096 bytes,
opened component-by-component with O_DIRECTORY/O_NOFOLLOW and pinned as a directory
FD. Names/axes/root snapshots remain immutable during user callbacks.

Writer uses O_CREAT|O_EXCL|O_NOFOLLOW, mode0600; an existing name refuses, with no
retry, removal, replacement or rename. Actual file must be regular/single-link.
The receipt records sealed root/name/role/shape/type/classification, frozen numeric
encoding, exact count, successful physical byte count, file/directory device and
inode and write-stream SHA. File and directory fsync must succeed for
closed_fsynced. Partial/failed provisional files remain exactly where created.
No lower-level success flag is a root READY or complete mathematical inventory.

Independent reader opens the sealed existing root/name again, O_NONBLOCK before
fstat so FIFOs/devices/nonregular inputs refuse without blocking open. It verifies
regular/single-link file, exact receipt directory/file identity/size, exact typed
header, every scalar/count/byte, physical EOF and actual FD read SHA; inode/size
must remain unchanged during reading. Readback is scoped to the same original
provisional artifact; copies/archives require separate verified identities.
Its parser shares only path/hash/primitive type definitions with the writer,
not formatting/conversion or a cached numeric array. Missing/extra/trailing/type/
endian/SHA/byte/shape/encoding mismatch refuses; no format fallback exists.

Writer SHA covers bytes actually reported successful by write(), including
short writes. closed_fsynced is NOT independent final-FD-content attestation:
a callback or external actor can overwrite earlier bytes in the same inode with
the same length. Independent readback must match before any future root READY.
Reader SHA covers actual bytes read, including bounded read-ahead; consumed cursor
is distinct. Neither interface claims an adversarial filesystem lock or atomic
immutable snapshot; future frozen runtime must require immutable retained files,
trusted callbacks, and independently checked full closure.

## Exact binary and JSON representations

| Binary field | Representation |
|---|---|
| Magic | Exactly16 ASCII `P5NUMCHUNK000001` |
| Scalar type | u64le1 f64 /2 u64 /3 i64 /4 failure f64 bits |
| Endian | u64le `0x0102030405060708` |
| Count | u64le number of scalar entries |
| Values | Exactly count8-byte little-endian words; no padding/trailing bytes |

Binary length is exactly40+8*count. IEEE754 binary64 and two's-complement i64
are the declared representations; actual platform/compiler assumptions require
future independent freeze/build tests. F64 entries MUST be finite for finite
fields; signed zero bits survive. Kind4 is arbitrary exact IEEE bits and requires
ForensicDefinedFields classification. It may preserve NaN payload/Inf/initialized
failure values, but cannot masquerade as finite or complete successful math.

JSON is one exact ordered object with decoded keys `schema,type,count,values`.
Schema is `PUBLIC_LIVE_AFFINE_V2_NUMERIC_CHUNK_JSON_1`; type is `f64`, `u64`, `i64`
or `f64_ieee_bits`; count is canonical unsigned decimal; values is the complete
flat array, exactly count elements. Writer emits finite f64 via locale-independent
to_chars(general,max_digits10), canonical u64/i64, and failure bits as quoted
exactly16 literal LOWER hexadecimal digits in most-significant nibble order.
These are typed IEEE bit strings in JSON, never binary fallback or bare NaN/Inf.

Reader checks strict JSON grammar, decoded ASCII schema/key escapes, fixed key
order (duplicate/unknown keys refuse), full number grammar/token32-byte limits,
unsigned/signed range, no leading zeros or plus/fraction/exponent in integers,
no minus-zero integer, finite f64 from_chars and exact failure16-hex strings.
Quoted numbers, YAML tags/aliases/comments, trailing commas/content, nonASCII
schema fields, wrong types and nonfinite finite-field values refuse. Signed f64
zero remains legitimate. Whitespace is accepted only as JSON whitespace, counts
in actual bytes/SHA and does not waive byte/resource limits. Header strings are
ASCII because all declared schema/type/key values are ASCII; Unicode input cost
names/units belong to their separate codec/inventory metadata, not these chunks.

## Budget and callback lifetimes

SharedCaseBudget shares the SAME CaseState/BatchState and original frozen encoding
and output cap; it is not a new/wider ResourcePlan and cannot be freely constructed.
The shared state survives source CaseBudget wrapper destruction. Each writer or
reader owns20 logical slots (128-byte16 cache plus up to4 sealed shape indices)
before dynamic buffer/shape allocation. Buffer/specs are destroyed before their
ticket. Every writer cache generation, including first/header/partial payload
fill, charges16 slots BEFORE its first byte assignment; flush does not charge
again. Reader charges16 BEFORE each fill. Refusal cannot first overwrite work.
Every reuse contributes to the same case/batch cumulative ceilings, never refunded.

Writer prechecks the entire pending output buffer against existing aggregate caps
before physical writes. No user callback occurs between cap precheck and charging
successful short-write bytes. The single-thread-per-batch contract is mandatory;
these ledgers are not thread-safe. Only actual successful bytes advance unique
output counters/hash/frontiers. Header bytes additionally advance metadata counters;
reader metadata parsing advances separate metadata-work byte debits but NEVER
charges unique output bytes again. Ledger debits and artifact physical bytes are
reported as distinct concepts on failure; stdout/manifest/other actual metadata
remains the future driver's responsibility. No output/metadata cap is raised.

The scoped per-case ChunkIOLease prevents recursive writer/readback from source
or observer callbacks; reentry latches a first refusal, and outer IO checks it
before/after callbacks and before buffer use. Even a swallowed nested refusal
cannot produce a closed/readback success. Standard/nonstandard exceptions preserve
first error/stage/element/physical/consumed/pending frontier and files. No returned
callback captures IO state or raw budget pointer. The input std::functions are
copied locally; their arbitrary C++ capture/STL allocations are NOT instrumented.
Contract forbids retained unbudgeted numeric arrays, IO/Model/ledger-changing copy
side effects or asynchronous use; future driver callbacks must borrow genuine
owned scalar fields and undergo frozen source review.

Failure observation separates attempted index, fully encoded/decoded entries,
actual physical bytes, parser consumed bytes, uncommitted pending bytes and last
scalar-bit validity. A partially encoded scalar is not a complete element. Pending
unwritten cache bytes are not a file chunk and are not claimed published. The
upstream driver must retain the original mathematical/input owners and failure
frontiers; low-level chunk closure cannot stand in for them.
