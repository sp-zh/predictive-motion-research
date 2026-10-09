# Complete output capture contract 1 — publisher/readback deferred to SOURCE3C2

This contract defines required future full evidence. It is not an implemented
writer, accepted research result, permission to run, or output READY. Actual
encoding must equal the frozen requested output NumericEncoding; actual capture
mode must equal requested mode, with no Dense/JSON fallback. Phase5 NOT_ACCEPTED,
Phase6 NOT_STARTED and all7 scope claims remain literal false in every status.

## Closed typed artifact set

Future root manifest schema is `PUBLIC_LIVE_AFFINE_V2_CAPTURE_1` with exactly
schema, status, source_kind, requested_mode, actual_mode, requested_encoding,
actual_encoding, identities, dimensions, rosters, regions, chunks, failures,
execution, quota, scope_claims, phase5, phase6. Status is COMPLETE_COMPONENT or
RETAINED_FAILURE; every phase and controller claim is separate. The final
`PUBLIC_LIVE_AFFINE_V2_CAPTURE_READY_1` names exact manifest SHA/byte length and
all unique relative chunk names/SHA/lengths. Provisional chunk/manifest names
must never be accepted as READY. Publication and independent readback require
actual complete closure checks, fsync and quota checks before atomic final READY.
Writer/readers are not in this source stage.

Numeric chunks have unique role, relative path (no traversal/symlink/absolute),
representation, dimensions, ordered strides/traversal, exact element/byte count,
SHA256, source field/owner identity, computed/initialized classification and
coverage ranges. Binary data is f64le/u64le/i64le with no padding, checked exact
8*n length and endian/schema identity. JSON chunks have complete flat numeric
arrays of the exact length, strict JSON grammar/duplicate decoded-key refusal,
round-trippable binary64/canonical u64/i64 counts and no norm-only summaries.
Every finite scalar including signed zero retains complete semantic bits. For
retained failure chunks containing nonfinite IEEE values, an explicitly typed
JSON `f64_ieee_bits` array of16-hex-digit strings preserves every value's exact
bits, including NaN payloads; these failure chunks cannot become complete finite
math output. This is JSON failure representation, not silent binary fallback.
Metadata records the exception from finite JSON values. Primitive finite tokens
and failure bit strings fit the existing34-byte-per-slot envelope; actual bytes,
chunk metadata, stdout/stderr/error text/rosters and manifests must nonetheless
be counted against frozen aggregate output and8MiB metadata caps. Oversize
capture retains failure/provisional evidence and cannot emit a complete READY.
No omitted chunk, duplicate/overlapping/missing element range or unchecked extra
file is permitted. Closure hashes alone do not prove source completeness.

| Inventory | Mandatory complete values and provenance |
|---|---|
| Release/model/raw | Real ELF/source/build/SDK/XML/constants/review/protocol/invocation/cost artifact identities; actual metadata/profile; constructor/query/rollout attempt claims and all original transport/structural/SDK errors, nominal/Jac flags, first uncertified index, friction iterations/branches/KKT/forces, clipping and complete returned raw matrices/state/input/origin/cell origin/times/rosters/prefixes. No Model rerun to fill gaps. |
| Normalized | Every cell/prefix/cycle native cumulative A/B/d, actual origin/endpoint/input and indices. Half2 polynomial sample progress and recursive cycle progress/defects remain distinct. Borrowed native records may reference exact raw chunks only with full reconstruction/coverage proofs. |
| Compact affine | Complete boundary o/M/P for0..N; flatten T/t; chosen initial kind and30 bits; complete structured initial selector (all P blocks, zero U block). Independent control slices and fixed layout [X0..XN;U], no resets/control ties. |
| Samples | Full native sample composition recipe, source identity/indices and every actually evaluated o/M/P/actual offset, captured once per sample with bounded stream work. Compact never materializes S dense selectors. Recipe and actually evaluated chunks are distinct; no claim that a recipe was evaluated. |
| Cost input | Real complete input artifact or verified immutable archive identity; all sealed names/units/layouts/order, every F/f0/ell/c0/C, parent-row indices, chosenkind/initial and eval U; opaque and typed semantic SHA. Forensic moved request identified separately. |
| Cost terms | Each ORIGINAL actually computed usedF/usedf0/ell/c0, Fc/fc/Hraw/g/c and complete original direct/condensed objective/gradient/Hessian. Raw H never rewritten; Hsym half-first semantics explicit. |
| Canonical cost | Ordered concatenation of complete used/Fc/fc term chunks with exact full row ranges; exact ordered summed Hraw/g/ell/input c0/condensed c and complete original direct/condensed objective/gradient/Hessian. Concatenation must not substitute different floating sum arithmetic. |
| DenseAudit | If actually requested/run: full L/E/f/I0, initialized active LU/R workspace, eliminated solution, every actual dense selector and both independent sample map sets; elimination stage/partial updates preserved on failure. Unused audit capacity is not data. |
| Execution/failures | Exact reviewed arguments/process paths, original stdout/stderr/exit/errors/first claim, attempted/closed stages, decoder consumed/physical frontiers, partial input/math regions and all retained prior failures; no retry/overwrite/partial full-success claim. |

## Viable original-evaluation schedule

SOURCE3C2 must use InitialCostConsumer to write each original term used factors
and full evaluation during initial construction, then original canonical
full evaluation (K+1 original work charges). Retained authoritative inputs and
coefficients are read without numerical replay afterwards. Ordered term chunk
references can represent canonical concatenation losslessly; H/g/constants stay
actual ordered accumulation. Each sample composition may be streamed once
against its planned sample work. Actual decoder cache reuse, normalization work,
output byte buffers/copies and every retained chunk must be included in the
bound cumulative/live/batch plan. No promise that arbitrary repeated callbacks
fit. Independent integer accounting of the complete3C2 flow remains required;
quota refusal must preserve artifacts and must not raise caps.

## Initialized memory and mathematical frontiers

`withRetainedRegions` exposes borrowed initialized fields only. A zero-filled
placeholder is DEFINED_NOT_EVALUATED, never an accepted mathematical result.
`written` means assignments performed, including assignments whose subsequent
finite/parity validation failed. The enclosing outcome/first refusal and trace
stage govern validity. `trace.complete` records historical original-stage
completion; later callback/source failure can invalidate the outcome while
retaining that historical computation. It is not a success flag by itself.
Math source revisions retain failed buffers instead of destroying them.
Stack-local arithmetic accumulators are not falsely claimed as stored arrays;
these hooks capture all declared owned arrays and persistent scalar fields,
not process/register snapshots. Error type/stage/cursor identifies an attempted
expression that failed before an array assignment.

Affine roles/layouts: boundary is (N+1) blocks `[o30,M30*DU,P900]`; embedding is
`[T DY*DU,t DY]`; active work is `[chosen30,sample o30,sample actual30,M30*DU,P900]`.
Dense lifted is `[L DX²,E DX*DU,f DX,I DX*30]`; active workspace `[LU DX²,R DX*(DU+31)]`;
solution is row-major DX*(DU+31); selectors S*30*DY; sample maps two ordered
S blocks `[o30,M30*DU,P900]`. Other allocation capacity is never emitted.

Affine written field IDs0..23: chosen initial; boundary o/M/P; embedding t/T;
current sample o/M/P/actual; dense L/E/f/I; workspace LU/R; solution; selector;
compact dense-sample o/M/P; eliminated dense-sample o/M/P. Each is an independent
assigned prefix under its declared traversal: ordinary fields cell/sample then
row-major, solution column then reverse row. In-place elimination is fully
defined after its copy frontiers; stage/item(pivot)/row/column marks the active
mutation. These are partially transformed forensic arrays, not completed
solutions. Current sample memory_item/memory_stage tracks reused-buffer identity.
Failure before sample quota admission preserves the preceding generation.

Cost input contains numeric scalars only (no topology padding); coefficients
layout remains the cost source's retained Fc/fc/term H/g/c/sum H/g/ell/c blocks.
Active work is only the explicit layout through canonicalValueIndex inclusive,
plus persistent direct/condensed scalar roles. IDs0..16: input scalar assigned
prefix; evalU prefix; current usedF/usedf0; current term Fc/fc/H/g/c; current y,
residual,directRows,gy,inter,directG,directH,condensedG. ID20 counts complete
condensation terms during original build;21 counts complete ordered accumulation
terms;22 identifies written canonical direct value. Other IDs are reserved zero.
Stored coefficients before the active term are complete; active-term frontiers
specify exact assigned prefixes. Ordered sum stages and item/row/column identify
partial current accumulation after prior complete terms. Sample-addition stages
identify active addition, contribution row and state/control column (or offset);
full base factor has already been copied. Active reused work is cleared only
after a charged admission; memory_item records that generation. Canonical caches
are never cleared by term replay. Persistent direct/condensed values can be
partially accumulated and are therefore labeled by stage, never inferred valid
from finiteness alone. Failure decoder EOF/semantic checks keeps complete copied
input as initialized data, with input_complete still false if refused.

Normalizer role contains exactly120 owned subtraction entries, four30-vectors.
IDs0..3 mark each assigned row prefix;4/5 mark actually constructed cell/sample
view prefixes. memory_stage/item identifies the last attempted substep/cycle
map whose scratch was admitted, independently of current validation attempt.
Genuine raw source still owns all native arrays on every refusal. The existing640
scratch ticket is retained; affine unused work capacity reduces by those held
slots before allocation, preserving the old combined live/charge schedule.

Callback views cannot be saved after owner/callback lifetime or used for mutable
mathematics. Failure records must preserve FIRST errors and prior stage evidence.
A publisher must tag initialized placeholders, assigned-but-unvalidated entries,
complete prior fields and current partially updated fields independently; never
dump all allocated slots or turn partial evidence into a full success result.
