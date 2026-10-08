# Complete compact output proposal (no omitted required quantities)

SOURCE ONLY. Compact means a lossless structured/streamed representation of ALL
requested data, not residual summaries or a replacement by sufficient statistics.

Root metadata: schema/version, nominal Model identity/invocation, ACTUAL context
and initialization kind, integer mesh/times, resource/capture policy, scope7false,
full original raw ModelResult manifest, and actual/model/command units. Each
blob is f64le (finite), i64le/u64le indices/flags, or typed JSON metadata with
shape, row ordering, filename, offset/length and SHA256. Chunk rows completely
partition the declared matrix; no holes/overlap/truncation. Independent reader
reconstructs values and compares within the frozen arithmetic gate; hashes prove
serialization identity, not tolerance equivalence. All referenced blobs are
members of the immutable artifact or explicitly pinned retained source archive.

Boundary views contain all actual offset30, control30xDU and initial30x30.
Each ordered sample retains its literal origin/input/endpoint/tick/cell/cycle/half
and cumulative A30x30/B30x8/d30. Its complete recursive affine representation is
`CELL_PREFIX_COMPOSITION{boundary_view_id, A, B, d, own_control_slice}`:

- o=A*boundary.o+d
- M=A*boundary.M+B*E_own
- P=A*boundary.P

E_own selects the declared8 independent columns; zeros elsewhere are defined,
not omitted unknown entries. Dense selector over y is losslessly encoded as
`STATE_CONTROL_BLOCKS{state_boundary_id,A;own_control_slice,B;offset:d}`. Root can
construct the whole dense selector independently. If DenseAudit was requested,
independently eliminated boundary views are also serialized, and every sample's
eliminated view references THOSE views with the same prefix. If it was not run,
metadata explicitly says so; recursive data is never labeled eliminated output.
An explicitly requested dense dump that exceeds plan refuses the whole request.

Cost input for every term: full arbitrary F(r,DY),f0(r),ell(DY),c0, name/units,
integration weights/scaling/provenance and ordered additions. An addition is
`{sample_id, target_row_indices[n], C(n,30)}`. Its row embedding R gives
Fused=F+sum(R*C*S_sample) and f0used=f0+sum(R*C*d_sample). Application order is
input order; repeated row indices/additions accumulate in that order. Every C block has n<=parent r<=256; coefficient dimensions and row indices
are checked before allocation. Full C over all parent rows is supported; sparse row embedding merely avoids padding
zeros, and may express arbitrary crosscomponent/crosscell terms. New quotas also
bound total C coefficients to4m, addition records8192 and row indices accordingly.

Term output serializes FULL ACTUALLY COMPUTED used_F/used_f0/used_linear/
used_constant plus Fc/fc/Hraw/g/constant and direct lifted/condensed evaluation
values/gradients/Hessians. Chunks may be written and released term by term; all
values remain available. Do not replace used_F by only an expression/hash/error
summary. Scalar linear/constant shifts and every sample contribution stay visible.

Canonical ordered sum: sum.used_F and sum.factor are manifest concatenations of
the term used_F and Fc chunks IN INPUT ORDER; offsets likewise. This defines the
entire numeric matrix, without a second in-memory/disk copy. used_linear and
used_constant, Hraw/g/constant are accumulated term-by-term in that order and
serialized in full. Independent concatenated-factor recomputation is a tolerance
check, not substituted bit-exact canonical accumulation. Hraw is unaltered;
literal polynomial gradient/Hessian use .5(Hraw+Hraw^T). Empty terms have complete
zero shapes/zero vectors/constants and empty factor manifests, as in v1.

All raw ModelResult fields, including unused friction/clip diagnostics, are
retained in the live artifact. Archived map/state reconstruction is explicitly
tagged and must not claim a complete original native result. Full negative-control
corruptions can target chunks, block descriptors, indices or manifests and must
be rejected; source-only schema makes no passing runtime claim.

Proposed256MiB output quota is aggregate UNIQUE serialized artifact bytes, not a
compression assumption. Binary numeric slots cost8 bytes plus explicitly bounded
metadata; JSON expansion has a separate conservative34 bytes/slot plus8MiB
metadata plan and refuses over-budget cases. Inputs reused by verified references
are counted once, not silently discarded. Maximal N32/R8192/C4m full capture is
over budget and refuses; smaller declared costs admit .8/1.5 profiles per the
prospective table. Quota applies before capture and while writing .part streams;
an unexpected exceedance preserves a failed artifact and never emits READY.

Topology index fields (normalized cell/cycle/half/tick/row identities), byte-level
blob descriptors and UTF-8 strings are explicitly charged to the8MiB metadata
allowance and checked against actual aggregate encoded metadata bytes. Normalized
numeric topology also has conservative slot counts in the shape table; double
counting this small subset is safe. No unchecked string/metadata growth is hidden
under a constant allowance. Model error text remains preserved; if it exceeds a
planned artifact quota, publish failure evidence rather than truncating it.
