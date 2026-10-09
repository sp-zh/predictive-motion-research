# B3B1 fixed-column provisional manifest — source only

Private CaptureLeafSession.captureProvisionalManifest consumes one attempt, using
only its actual source/cost/partition/case/paired records. There is no caller record,
hash/event-list/completeness or accounting-skip API. No serializer/parser/reader/
metadata/sort/reference/coverage/IO/compiler/numeric/Model function was run.
FullCapture/FullFlow false; Phase5 NOT_ACCEPTED; Phase6 NOT_STARTED. All original
checker/freezes/accepted evidence/failures remain. This is not a root READY or
COMPLETE_COMPONENT publisher; no rename/unlink/overwrite/retry occurs.

## Actual V2 allocation and tickets

V1 and generic source paths remain. New prepareCaptureWorkspaceV2ProvisionalManifest
and decodeAndBuildCostWithCaptureWorkspaceV2ProvisionalManifest require private
version2, policy CAPTURE_WORKSPACE_PARTITION_2_PROVISIONAL_MANIFEST. V1 rejects V2
and vice versa after one-attempt admission. Original caps and receipt bounds stay.
Credit =160 transient +16 held snapshot +4*receipt_limit. Actual cost work reduces
from W by Q+decoder16+credit BEFORE allocation; original exact required layout must
fit. The cost constructor rechecks private policy/formula/once/source/case, records
actual allocated==remaining, then sets applied. No pool/buffer/slice or cap growth.

Writer/reader EACH reserve96 before materialization and never coexist: cache128=16,
integer32/magnitude4, escaping/unicode<=8, digest64=8, bounded control/cursors/
field comparison60. Producer metadata/reference/attempt-row40 overlaps IO96;
coverage20+catalogue20 overlaps IO96. HeldSnapshot16 persists. Peak152 <=160+16,
plus actual existing4-axis receipt tickets. Sort40 ends before IO begins. No DOM,
resident event/index/string dictionary/numeric-array snapshot exists. Static schema
data are code constants, not a mutable result registry. Logical slots are not all
STL/EVP allocator RSS. Reservations/copies/cache generations/format/parser reuse
are actually charged and can refuse case/batch ceilings; no whole-flow admission.
PROVISIONAL_RESOURCE.json records isolated integer layout, not runtime evidence.

The16 snapshot ticket is declared before its fields and dies after them. Custom
move-assignment uses temporary-old+swaps; old snapshot bytes die before old ticket
release. Snapshot freezes real pre-file live/charges/metadata/output and their
four original ceilings, plus section availability. B3A private manifest branch
emits identical quota8 scalars during writer AND reader, not newly observed values.
All other facts remain borrowed from unchanged genuine owners. Manifest exclusion
denies mutable capture/attach/export/sample/forensic/close/consumer paths; only
private event producers enter evidence scopes. Frozen callbacks/first-poison
prevent swallowed reentry from succeeding. No source/record list mutates midborrow.

## Explicit compact schema, no automatic encoding fallback

Schema PUBLIC_LIVE_AFFINE_V2_PROVISIONAL_MANIFEST_COLUMNS_2 has ordered root keys:
schema,status,mode,references_available,coverage_available,references_reason,
coverage_reason,metadata,attempt_rows,references,coverage,counts,
references_reconstructed,full_capture_complete,full_flow_accepted,phase5,phase6.
Status PROVISIONAL_UNACCEPTED; diagnostic mode LIVE_UNACCEPTED_DIAGNOSTICS or
RETAINED_FAILURE_DIAGNOSTICS. Three final gates false and phases NOT_ACCEPTED/
NOT_STARTED. Unavailable sections have explicit mandatory-missing reasons/empty
arrays; no fabricated fields. Exact provisional equality never passes full gates.

The old object-per-field format is retained with its15,979,020-byte lower bound
for just16 minimal fields*11579 attempts. It is unsupported and never selected.
This new frozen schema uses positional typed rows and explicit references, without
statistical compression or an encoding fallback. No required value is discarded.
PROVISIONAL_COMPACT_BYTES.json has a CONDITIONAL static length upper8,136,962 bytes
<8,388,608 for declared default Compact N20/T200/S400/K0/J0,11579 actual numeric
attempts, names<=64/role labels<=32/common root<=128, exact closed IO satisfying all
reference laws and other source/schema bytes<=262144. It is not a measured file or
full planned cumulative admission. Other inputs remain lossless but may exceed
unchanged cap and must refuse. Actual successful write bytes are always charged.

Nonattempt metadata records retain complete ordered family/field/index/subindex/
type/value objects. Types utf8/u64/i64/bool/ieee64_bits/numeric_reference/missing
remain distinct. Missing has actual reason, never null/zero. Primitive bool/U64/
I64 are canonical; IEEE strings preserve16 literal lowerhex bits/signedzero/NaN.
Strings validate UTF8 and exactly escape controls/NUL/quotes/backslashes. Invalid
UTF8 refuses without rewriting held source; opaque byte publication remains later.

At the ORIGINAL contiguous attempt metadata span, a typed marker
["ATTEMPT_COLUMN_ROWS",actual_count] names complete rows in attempt_rows. Source
metadata event order reconstructs from that marker and fixed alias layout; counts
still count EVERY original B3A event, including aliases. The static79 projected
family/field/kind-mask declarations reject unknown fields or original type changes.
They are schema data shared by writer/reader, not parser or formatter logic.
Alias field indices refer to key-sorted row index; original_sequence remains
immutable actual execution order. No caller can construct the private row view.

### Complete attempt row columns0..42

0 original_sequence(u64),1 role(u64),2 primary(u64),3 secondary(u64),4 generation,
5 computed_state(i64),6 storage string,7 assignment string,8 source-match bool,
9 cost-match bool,10 partition-match bool,11 original bool,12 canonical bool,
13 sample bool,14 cell,15 tick,16 cycle,17 half,18 full dimensions array(rank<=4),
19 scalar kind(i64),20 classification(i64),21 encoding(i64),22 root string,
23 provisional relative name,24 actual role label,25 actual main SHA string,
26 count,27 bytes,28 device,29 inode,30 directory device,31 directory inode,
32 closed-fsynced bool,33 actual writer observation,34 comparison-attempted bool,
35 expected-valid bool,36 mismatch bool,37 comparison index,38 expected kind(i64),
39 actual kind(i64),40 expected bits-or-explicit-missing,41 actual bits-or-missing,
42 readback compound-or-explicit-missing. Other scalar columns are U64.

All attempt family fields map to identically named columns, rank/dimension fields
map to18 length/elements. expected_bits/actual_bits recover original distinct
U64 versus Ieee64Bits metadata kind from actual kind38/39 and validity34/35;
invalid bits keep exact original missing reason, not a default payload. Exact bit
strings are representation, never conversion to a floating decimal.

Expanded IO observation is [["stage",typed_string],attempted_index,
encoded_or_decoded,physical_bytes,consumed_bytes,pending_bytes,last_scalar_bits16,
last_bits_valid,bool_hash_valid,refused,first_error,physical_prefix_SHA]. Source
last bits remain literal held bytes even if invalid, with the separate valid flag.
Readback42 is [exact_readback,observedSHA,actual_reader_observation], or the original
NO_INDEPENDENT_READBACK_OUTCOME missing reason. Both old attempt_write/attempt_read
summary fields and their full frontier fields alias these SAME actual observation
columns: no repeated value or source error is dropped. Standard/nonstandard/early
factory errors mark the retained actual attempt's first refusal; bounded512-byte
error copies are charged before allocation, otherwise explicit fallback and source
first-error evidence survive. No failed file is removed.

### Lossless explicit string/observation references

String columns accept UTF8 literal or ["d",schema_literal_id]; dictionary constants
are exactly provisional_manifest_schema.hpp. ["r",0] may name first-row ROOT only
on later rows and only when actual root bytes match; row0 itself stores its root.
["h",0] may name CURRENT row's earlier mainSHA25 only when actual SHA bytes match.
Reader independently checks each law against private actual source; other strings
remain literal. Forward/self/unknown/mismatched references fail. No heap string map.

IO observation may be ["CW1"] or ["CR1"] ONLY when ALL actual fields equal its
closed law: stage CLOSED_PROVISIONAL_CHUNK/EXACT_CHUNK_READBACK, attempted index
count-1(or0 for empty), encoded count, physical record bytes, consumed0/write or
bytes/read, pending0, last-valid=(count!=0), hash true/refused false/empty error,
prefixSHA==mainSHA25, and last bits equal40/write or41/read (0 for empty). Positive
write requires actual expected_valid, positive read actual comparison_attempted.
These are complete source-field reference descriptors, not success summaries.
Writer checks every actual field before emitting the tag. Independent reader
revalidates EVERY condition; no writer predicate/formatter is reused. If any field
fails, ALL actual fields use expanded observation. Partial/error evidence never
gets a closed tag; it is never omitted merely to fit.

Reference rows have exactly24 columns in original ReferenceFact order: use,index,
part,role,primary,secondary,kind,rank,dimensions,count,offset,source_count,
destination_offset,zero_block,empty_concatenation,source_valid,paired_verified,
reconstruction_verified,requires_original_scope,requires_sample_scope,cell,cycle,
half,tick. No field/boolean/coefficient/range is replaced by a norm. Structured P/
zeroU/native normalized/cycle/sample/canonical4 refs stay unreconstructed.

Coverage rows20 columns: role,primary,secondary,rank,dimensions,availability,
classification,traversal,mandatory,scalar_kind,defined_computed,shape_known,
actual_leaf_bound,bytes_captured,exact_readback,state,matching_attempts,reason,
full_capture_complete,false_full_flow. All fields retain original types/values.
Compound/source/metadata/missing obligations stay explicit; ancillary19 and true
raw-control8f64/1i64 split remain. Count/footer checks require exact complete source
traversals and all actual rows; extra/duplicate/missing/unknown/type/scope changes
cannot be accepted as complete ordered source collection.

## Physical bytes and independent strict readback

Root is opened component-by-component nofollow; name single safe .provisional.
O_EXCL|NOFOLLOW|CLOEXEC0600 fresh empty regular single-link FD; actual file/root
size/dev/ino tracked. Before flush check pending output/metadata caps; charge each
successful shortwrite byte ONCE as unique output and encoded metadata, hash that
same byte span. Preserve partial physical/pending/hash/event/field/bit diagnostics.
File+directory fsync and unchanged FD identity/length for closedProvisional.
No READY/rename/unlink/overwrite/retry, even on exact readback.

The private writer branches use actual borrowed metadata text and counted physical
encoding; they never invoke the already-charging B3A withJsonString, subtract/
refund charges or expose a skip flag. Every punctuation/scalar/string byte is paid
once at FD write. Paths/retained observations have separately paid bounded stored
metadata allowance. Reader does not charge these encoded output bytes again;
its own cache/parser/copy/digest/retained diagnostics remain actually charged.

New O_RDONLY|NOFOLLOW|NONBLOCK independent FD with same regular single-link/root/
file identity/size required. Handwritten reader does not call writer formatter,
encoder/type-name/compact-choice predicates. It independently decodes UTF8/raw/
escaped surrogate pairs, strict integer grammar/types/bools/16-hex bits, column
counts/dims/flags/errors/reference law and each actual fresh private source field.
Reset numeric validity BEFORE parsing/quote; partial values are invalid. I64 valid
only after sign/range/delimiter checks, records exact actual modulo2^64 bits;
-0/leading zeros/exponents/fractions/overflow refused. Source mismatch preserves
actual parsed bits. Advertised bytes/consumed cursor/physical EOF/unchanged FD and
independent read-ahead SHA==actual writer SHA required. Shared low-level safe-path/
SHA primitives and immutable schema declarations are not shared parser logic.

## Explicit failure mode and still missing

Live mode needs current complete unrefused source/appliedV2. Failure mode needs an
actual closed/refused/incomplete source PLUS historical actualV2 reduced allocation
STILL HELD by same genuine cost owner. Historical applied is diagnostic headroom,
never restored validity/export. Missing actual allocation/early owners refuse
without file IO. One attempt cannot retry under another mode/name after any error.
First source/math/decoder/capture/forensic errors and partial artifact survive.

Still mandatory missing: reviewed argv/process/stdout/stderr/exit/actual claim
SHA/source+SDK members/prevalidation context snapshots, genuine early-failure
owners/opaque invalidUTF8 archives, full-reference reconstruction, all unique files/
inverse extra files/aggregate metadata/output/cumulative/live admission, complete
immutable failure publication and atomic root READY/whole independent reader.
Provisional equality does not fill those facts. No new motion/render/video/
controller accuracy/safety/performance result. Bind all provisional headers/cpps/
inc/schema and provisional_manifest_contract exact path/hash in source closure.

The complete79-field alias map, original type masks/index/subindex derivations and event-order template are PROVISIONAL_ALIAS_LAYOUT.json. Runtime projected-fact checks establish existence/type mask ONLY; old individual MetadataFact values are NOT separately compared after the marker. Runtime reader instead compares all actual private row properties and reference laws directly; old-event value reconstruction is the independently reviewed static SAME-source correspondence. This limited scope does not establish metadata/root full acceptance. Future source mapping changes need a new review/freeze.

Attempt row cursor field is the1-based parent column0..42 shown above (field1..43 in diagnostics); it advances and invalidates/reset last bits BEFORE comma/value handling. Nested dimensions/observations report that parent column, not an independently tracked child-field index. New string parse also invalidates previous numeric diagnostics; explicit string-reference indices are their own parsed U64 primitives. This source does not claim finer nested cursor granularity.
