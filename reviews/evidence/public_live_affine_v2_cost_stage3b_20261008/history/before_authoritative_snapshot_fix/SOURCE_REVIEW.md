# Quadratic source stage 3B — pending independent static review

Complete factor/offset/linear/constant costs and canonical term/sum computation
are implemented as source. No configuration/compiler/empty/numeric/matrix/Model/
query/plant/solver/main/scorer invocation occurred. There is no default weight,
task tuning, controller, codec or phase permission. Phase5 NOT_ACCEPTED; Phase6
NOT_STARTED.

The only source is a complete owned affine outcome. Actual K/totalR/largest rows/
addition coefficient/record counts are computed from descriptors and must equal
the original frozen FactorShape. Real opaque input SHA/length and complete typed
IEEE semantic SHA bind all full values, metadata, order, chosen initial and evalU;
see INPUT_CONTRACT.md. The bounded scalar-reader interface is an explicit future
decoder contract, not a claim that complete binary/JSON codecs already exist.

Every F/f0/ell/c0 and addition C is copied into owned numeric storage after whole
reservation; descriptors/ordered indices move with the recipe. No raw source
matrices are copied. For each term, usedF and usedf0 start at actual input and
apply every parent-row embedded sample contribution in declared order. Native
sample A/B/d uses its cell-boundary slot/own8-control slice; Compact allocates no
S dense selectors. Used linear/constant stay explicit.

Fc=usedF*T, fc=usedF*t+usedf0; Hraw=Fc^T Fc, g=Fc^T fc+T^T ell,
c=.5fc^T fc+ell^T t+c0. Every product/sum and updated entry is finite-checked.
RawH is never rewritten or symmetrized. Literal condensed value uses rawH;
gradient/Hessian use overflow-avoiding `.5*H+.5*H^T`, never `.5*(H+H^T)`.
Generic nonsymmetric serialization/reference cases remain an explicit deferred
test; this factor construction mathematically yields PSD symmetric H.

Canonical H/g/ell/constants accumulate term-by-term in exact input order. Fc/fc
concatenation is ordered representation and never substitutes different floating
sum evaluation. Every term AND canonical sum is evaluated direct and condensed,
including objective, full gradient and full Hessian. Direct term value/gradient
uses full usedF/y; direct Hessian forms T^T*(usedF^T*(usedF*T)) through bounded
separate row/intermediate work rather than reading stored condensedH. Canonical
direct evaluations add the individual direct results in order. Fixed2e-13
abs/rel comparisons are source defaults requiring independent frozen runtime
verification; no output has been observed or gate changed.

All input values, Fc/fc, per-term H/g/c and canonical H/g/ell/c are retained.
Full computed usedF/usedf0 and direct/condensed evaluations are exposed in bounded
callbacks, regenerated from immutable owned input in the same declared order.
Sum used factors are the input-ordered concatenation of those complete term
chunks. This is a complete recipe/value API, not a norm-only summary; future
capture must visit every chunk/entry and distinguish recipe from captured output.
Empty terms, zero-row linear-only terms, arbitrary initial shifts and rewards
are represented without fabricating missing factors.

Whole input+condensed capture+reviewed term-work storage is reserved before
numeric allocation. Initial materialization is covered by ownership charge;
every later reused term/sum work operation is charged before use. Callback
reentry/quota/finite/standard or nonstandard exceptions poison complete cost,
keep the first reason, and preserve source/raw/input identity. Source assembly
poisoning also invalidates complete cost and reports the upstream failure.
Callbacks are borrowed, noncopyable and valid only while active. No const_cast,
Eigen numeric temporary, growing cap or silently omitted data exists.

Ordinary construction failure retains the failed owned numeric storage with
input_initialized/active-term/addition trackers. Complete capture of initialized
regions, precise stage/region manifests for failure intermediates, argument/
stdout/stderr/exit evidence and actual metadata/output byte quotas are SOURCE3C
obligations. Uninitialized/unused buffer capacity is NOT an output. Logical
tickets do not instrument callback/SDK/STL/string allocations or prove process
RAM. The reader contract forbids unbudgeted retained numerical caches; the actual
future decoder must enforce/account its buffers and opaque-file completeness.

Necessary private bound shape/file/semantic/budget bridges cross Model boundary,
normalization and affine wrappers. The invocation schema change is versioned;
all six accepted original bridge files and local edit revisions are retained in
history. Original Model/checker/freeze/Dell metadata stays unchanged. Lossless
readers/writers, controller, geometry, stopping, timing and phase gates remain
separate, and all7 claims remain false.

Canonical callback serves retained construction-time ordered direct value/gradient/Hessian and reevaluates the condensed polynomial in one bounded work operation. It does not repeat all K terms merely to recapture the canonical evaluation. Term replay uses separate work regions and cannot overwrite the canonical direct cache. A before-cache-cleanup source/manifest snapshot is retained.
