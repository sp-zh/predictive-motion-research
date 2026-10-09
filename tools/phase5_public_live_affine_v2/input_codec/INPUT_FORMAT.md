# Cost input codec 1: complete bounded source, unexecuted

The opaque artifact is the exact real file/path/length/SHA pinned in
INVOCATION_COST_BOUND_2. Its typed semantic SHA remains COST_SEMANTIC_1 from the
cost contract; both opaque and semantic identities must match. No default weight,
file generator, numeric example or runnable release is provided here.

Input encoding and requested OUTPUT NumericEncoding are distinct facts.
ResourcePlan now retains numericEncoding(). This version supports only matched
LosslessBinary/LosslessBinary and FullNumericJson/FullNumericJson pairs. It
classifies the artifact header separately and records actual_input versus
requested_output; mismatch refuses before metadata/scalar decoding. No byte or
JSON refusal chooses another encoding. A later version may support independently
selected pairs only after review. Binary starts directly with its magic; JSON
may start with JSON whitespace. Leading whitespace before binary is refused explicitly, so there is one declared binary representation.

All integer arithmetic is checked u64; dy/du, kind/chosen initial bits, exact
K/R/rmax/C/record totals and scalar count must match the owned affine invocation.
Names/units are nonempty valid Unicode UTF8, at most256 decoded bytes, no NUL.
Parent rows are ordered, bounded, nonempty; duplicates/repeated additions remain
literal. The source sample index must exist. Counts are validated before vector
reserve/push. The full metadata prefix, including punctuation/whitespace, is at
most8MiB. Whole actual artifact bytes must fit the smaller of the bound output
ceiling and256MiB. This stricter input envelope does not change the output plan.

## Binary exact field order

| Position | Representation |
|---|---|
| Magic | Exactly16 ASCII bytes `P5COSTBINARYV001` |
| Endian | u64le `0x0102030405060708` |
| Schema | u64le UTF8 byte length, then `PUBLIC_LIVE_AFFINE_V2_COST_INPUT_BINARY_1` |
| Dimensions | u64le DY, DU |
| Initial | i64le kind0 LiveActual/1 AlgebraTest, followed by30 f64le chosen initial bits |
| Shape | u64le K, R, largest rows, addition coefficients C, addition records |
| Scalar count | u64le R*DY+R+K*DY+K+C+DU |
| Terms | Exactly K ordered descriptors, below |
| Payload | Exactly scalar_count f64le values, below; no suffix |

Each descriptor: name and units as u64le byte length followed by UTF8 bytes;
u64le rows, addition count; then each addition: u64le sample index, parent count,
and exactly that many u64le ordered parent-row indices. Entire metadata precedes
all numerical payload values. IEEE754 binary64 is mandatory. Endian marker,
exact scalar count and exact remaining byte length reject alternate endian,
truncation and trailing bytes. Signed kind is two's-complement i64 (only0/1
supported); no compiler-native structs/padding are serialized.

## Strict full numeric JSON field order

The root is one JSON object with exactly these decoded keys in this order:
`schema,endian,dy,du,initial_kind,chosen_initial,factor_shape,scalar_count,terms,scalars`.
Schema is `PUBLIC_LIVE_AFFINE_V2_COST_INPUT_JSON_1`, endian is `little`;
initial_kind is `LiveActual` or `AlgebraTest`; chosen_initial has exactly30 JSON
numbers. factor_shape has exactly ordered keys
`terms,rows,largest_term_rows,addition_coefficients,addition_records`.
Each of exactly K terms has ordered keys `name,units,rows,additions`; each
addition has ordered keys `sample_index,parent_rows`. Scalar array has exactly
the declared count. Fixed schema depth has no arbitrary recursive object tree.

Keys are decoded before comparison, so escaped duplicate/unknown/reordered keys
refuse. Strings require strict JSON escapes, paired surrogates and bounded valid
UTF8; raw controls/NUL refuse. Counts require canonical unsigned decimal integer
syntax, no quotes/signs/fraction/exponent/leading zeros. F64 tokens use strict
JSON number grammar, at most32 ASCII bytes, locale-independent from_chars;
conversion overflow/underflow errors, nonfinite, NaN/Inf/YAML tags/aliases,
comments, quoted numbers, trailing commas/content and wrong scalar types refuse.
Every accepted number is a finite binary64; signed zero is retained in semantic
bits. Producers must emit round-trippable numbers (at least max_digits10 where
needed); independent source/build/runtime review must validate actual from_chars
rounding, subnormals and library availability. No rounded metadata tolerance or
fallback parser is permitted. Whitespace after the final object counts toward
actual file length/hash and must still fit the artifact quota.

## Payload and ownership closure

For each term in input order: row-major F(rows,DY), f0(rows), ell(DY), c0,
then each ordered addition's row-major C(parent count,30). Finally evaluation U(DU).
The scalar callback enforces exactly successive indices, rejects replay/skip,
returns each payload scalar once and retains the first error latch even if error
text allocation fails. Header chosen initial is parsed separately; it is not part
of this scalar callback stream. No decoded numeric DOM/full array/cache exists.

One regular nofollow FD survives failures. A128-byte cache owns16 logical slots
reserved before allocation; each refill charges16 slots before IO. SHA tracks
actually physically read bytes on this FD, including at most128-byte read-ahead.
Observation distinguishes physical read frontier/prefix SHA from consumed parser
cursor, metadata/term/addition/row/scalar frontiers, last decoded f64-bit validity, partial u64
bytes/bits/start and bounded JSON numeric token prefix, and exact EOF state.
First-error state latches independently of error-text allocation; all copied
callbacks refuse before budget/FD access after any upstream cost refusal. Prefix SHA is not mislabeled consumed-prefix SHA.
Finish requires exact scalar count, JSON/binary closure, all declared bytes
consumed, physical EOF, unchanged FD device/inode/size and complete observed SHA.
The cost factory invokes finish_read before accepting semantic completeness and
rechecks its sealed bound file. Changing file contents still refuses; no internal
claim protects against adversarial filesystem mutation or replaces immutable
runtime artifacts/archives.

Let Q=C/30+4*records, J=16 cache slots, I/V/W original input/capture/work.
The private shared original receipt owns Q+J once; descriptor and cache owners
retain it through transfer and independent observation lifetime. The cost anchor
does not charge original topology again. The sealed topology owns Q. Numeric
capacity is (I-Q)+V+(W-Q-J), leaving total I+V+W. Required actual work must fit
before input callbacks; insufficiency refuses. Cache refill charges also count
against bound case/batch cumulative ceilings; admission is not a promise that
arbitrary input whitespace/replays/export operations fit. Vector/string capacity,
allocator/SDK/all-process RAM are not instrumented by logical element tickets.

Generic manually provided CostInputRecipe remains a source interface, not a
complete-codec certification. The private ownership receipt cannot be minted
through its public fields. Its forensic request remains separate from sealed
calculation identity. Decoder failures retain parsed prefixes and source; failures
after transfer retain the cost outcome, including original artifact/metadata and
initialized mathematical buffers. All streamed capture chunks stay provisional.
EOF completion never promotes a failed mathematical cost to success.
