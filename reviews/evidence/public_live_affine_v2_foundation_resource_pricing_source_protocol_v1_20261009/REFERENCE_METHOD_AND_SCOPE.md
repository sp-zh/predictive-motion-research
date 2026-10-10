# Independent shape-pricing reference — source proposal only

No production function was called. The reference uses Python arbitrary-precision
integers and a named dimensional ledger. Each entry records a field/work-bank
shape and a multiplicity; category totals are reduced after the inventory is
enumerated. The C++ test compares frozen literals, not values returned by a
second implementation at runtime. The production source supplies the admission
contract and conservative allowances, not experimental expected outputs.

The layout basis is:

- X contains N+1 states of 30 coordinates; U contains N independent 8-coordinate
  controls; Y is their concatenation. There are 2T physical sample records.
- Each raw map contains two 30x30 A matrices, two 30x8 B matrices, five state
  vectors, one 8-vector and three logical indices: 2441 slots. Substep values
  contain four joint vectors, progress/time, friction/branch/status fields and
  three indices: 52 slots. Retained cycle/cell/final states and 9-slot controls
  complete the raw inventory. No Model is constructed to obtain these counts.
- Normalized borrowed maps have 1238 coordinates plus 3 cell or 5 sample topology
  values. Boundary o/M/P and embedding T/t come from the affine source contract.
- Input F/f0/ell/c0, addition C, selected-parent indices and record topology are
  separate ledger entries. Retained Fc/fc and term/canonical H/g/ell/c entries
  form the condensed inventory, including zero-row linear terms.
- Declared conservative factor and sample work banks are counted by shape.
  Initial ownership plus one sample pass plus K terms and one canonical-sum work
  operation, together with addition scratch, produce cumulative charges. This
  does not grant optional replay or validate actual work-buffer allocation.
- Output pricing includes input/used factors, retained condensed data and direct
  plus condensed evaluations for K+1 groups. The foundation envelope prices two
  scalar slots per evaluation side while the public evaluation view exposes one
  value. That surplus remains a conservative allowance; no extra numeric result
  is invented. DenseAudit adds L/E/f/I0, work/solution, selectors and both sample
  representations to the priced live/charge/output envelopes.
- Binary/JSON use the declared 8/34 bytes-per-slot allowances and fixed 8 MiB
  metadata reservation. These are planning bounds, not exact writer bytecounts
  or physical memory measurements.

Source references: foundation.hpp/resources.cpp and SOURCE_REVIEW.md;
normalization/SOURCE_REVIEW.md; affine/SOURCE_REVIEW.md;
cost/SOURCE_REVIEW.md and quadratic_cost.hpp; raw Map/Substep declarations in
the existing coupled augmented source; capture_inventory emitted shape roles.
No cost, affine, capture, SDK or Model API is invoked by this reference.

The 85 fixed groups contain 51 prospective accepts and 34 prospective refusals.
The only observed fields in future accepts are the 11 public Count getters and
the mode/encoding getters. Private component totals explain those aggregate
expectations; individual private banks are not independently observable and
must not be called runtime-passed. Rejects require the frozen first
invalid_argument reason and no returned plan or automatic mode fallback.

Two independent refusal targets are unreachable under the current base-factory
shape caps. Largest matrix products are 10,207,232 / 980,100 / 318,976, each below
12,000,000. The monotone cumulative upper bound is 241,832,203, below 512,000,000.
The reachability record retains their proofs and deferred scope. Malformed
earlier-domain inputs would not isolate these guards. Whole live and output
refusals are reachable and included; no hard cap is increased or bypassed.

MemberCapture wrappers, permission factories, actual cost evaluation, numerical
matrix/buffer materialization, complete allocator/SDK/RSS behavior and all
identity/context/Model/controller/plant/main/scorer gates remain outside this
proposal. Phase5 is NOT_ACCEPTED and Phase6 NOT_STARTED.
