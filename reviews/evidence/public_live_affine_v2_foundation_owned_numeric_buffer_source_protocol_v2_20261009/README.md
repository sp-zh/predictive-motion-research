# OwnedNumericBuffer finite source proposal v1

13 frozen groups cover public zero/data/size behavior, explicit initialized
mutable and const reads, move constructor/assignment/selfmove, same/different
ledger ownership, release/no-refund accounting and surviving shared observers.
The last group requires a moved-from CaseBudget constructor refusal before any
numeric array is allocated. No test was compiled, linked or run in preparation.

Every future array is explicitly initialized before reads; the maximum is 64
doubles per buffer and 128 simultaneously. Pointer comparisons only concern the
still-owned transferred array. No uninitialized or dangling data is accessed.
The fixed expected header and snapshot roster derive from declared operations
and exact binary-rational literals, not production outputs.

Private deallocation order is a static source fact, not a public counter proof.
True allocation-failure cleanup and host-size overflow are deferred: no forced
OOM, global allocation replacement, wrappers or fake factories are proposed.
Old 66/85 test sweeps are not repeated. Small mesh/base empty-factor setup is
only necessary accounting support for these new initialized-buffer cases.

Compile, final link and runtime require separate review, backup, freeze and
explicit bounded dispatch. The exact host candidates stay outside public Git.
No Model, SDK, cost/affine evaluation, permission, controller or physics enters
this proposal. Existing visual evidence retains its scope. Phase5 remains
NOT_ACCEPTED and Phase6 NOT_STARTED.
