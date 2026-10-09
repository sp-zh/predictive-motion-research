# Frozen cost input contract — source only, codecs deferred

No actual cost file/weights/runtime release is supplied by this checkpoint.
Model invocation schema is explicitly versioned to
`PUBLIC_LIVE_AFFINE_V2_INVOCATION_COST_BOUND_2`, adding
`cost_input:{artifact:{role:"cost_input",path,sha256,bytes},semantic_sha256}`.
The SHA/length of the real opaque cost file is verified before Model construction
and retained for later identity rechecks. Exact original FactorShape is retained
with that invocation. A runtime reviewer must approve BOTH opaque file identity
and complete typed semantic identity. Source decisions do not authorize a run.

CostInputRecipe describes ordered term names/units/rows and ordered sample
addition sample IDs/parent-row arrays. Its bounded read_scalar(index) interface
must access reviewed input without unbudgeted retained numerical arrays. A full
binary/JSON decoder and its cache accounting are SOURCE3C obligations. The cost
factory does not treat caller counts or that callback as authority: it recomputes
actual shape totals, compares the frozen bound shape/file, reads/copies every
number exactly once, checks finiteness and compares a complete semantic digest.

The scalar stream is, for each term in input order: row-major F(rows,DY), f0(rows),
ell(DY), c0, then each ordered addition's row-major C(parent_rows.size(),30).
After all terms it contains evaluation_U(DU). Extra/truncated/uninitialized
source data must be rejected by the future complete decoder. This layer only
requests the exactly declared scalar count; it makes no claim to detect opaque
file trailing data until that codec exists.

Semantic SHA256 is over the following exact ordered byte stream:

1. Length-prefixed UTF-8 string `PUBLIC_LIVE_AFFINE_V2_COST_SEMANTIC_1`.
2. u64le DY, DU, assembly initial kind (LiveActual0/AlgebraTest1); chosen30-coordinate
   initial as f64le; u64le term count.
3. For each ordered term: length-prefixed name/units; u64le rows; all F/f0/ell/c0
   scalar bits in the stream order above; u64le addition count; for each addition,
   u64le sample ID, parent-row count and every ordered parent-row index, then C bits.
4. u64le DU and all evaluation_U bits.

String lengths/integers are8-byte unsigned little-endian. Each finite IEEE754
double contributes its exact64 bits in little-endian, including signed zero.
No float text formatting, normalization, weight tuning, row reordering, duplicate
addition deduplication or nominal state replacement is allowed. The approved
semantic digest also binds the chosen initial kind/shift and evaluation point.
Its correspondence to the opaque file requires independent future codec/freeze
review; this source-only reader interface is not a complete lossless file reader.

All terms support full arbitrary F, offsets, linear rewards and constants. Sample
additions embed C into explicit parent rows and use native full selector
`zsample=A_s*X_cell+B_s*u_cell+d_s`. Repeated records/parent rows accumulate in
declared order. Units/name are required provenance, not selected research weights.
