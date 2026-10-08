# Root review: augmented cycle/cell sensitivities

Decision: selected component numerical checks PASS; Phase5 NOT_ACCEPTED and
Phase6 NOT_STARTED. This is an interior-domain reference, not main-controller
integration, a horizon planner, physical task success or timing acceptance.
The completed physical derivative prerequisite was backed up at1df8373.

The new wrapper retains the frozen augmented nonlinear value and evaluates
frozen physical derivatives at each substep's own q/v with the already-latched
held command. The two2ms derivatives are composed for each4ms cycle; command
history is distinct from physical velocity. Local maps and held-input cell
maps use corresponding nominal origins and matching affine defects. Partial
values remain intact on non-certification; only certified-prefix maps are
returned. No final uncertified matrix or replacement zero matrix is supplied.

Root independently checked4 positive cases,3 valid unsupported initial cases,
1 later progress-domain failure, and1 invalid input. The1cycle and10cycle held
cases each cover38 independent initial/input directions. The nonuniform
[1,3,2,4] cycle mesh covers30 initial plus32 distinct cell-input directions;
these inputs are not tied together. Equal-input subdivision agrees with a
single10cycle cell.555 calls to the unchanged old2fa value probe cover both
signed perturbations at epsilon1e-6 and3e-7, in batches≤96.8,346 originalfa1
single-step diagnostics independently verify every returned physical substep's
strict friction/clip signature and M/K/Hsym positive-definite condition bound.
All initial/generated C/w/s/r and each held alpha satisfy the declared strict
support domain at every perturbation. No model fit or new plant run occurred.

Both epsilons pass the per-entry5e-7+5e-6*abs(analytic) gates at every halfstep.
Worst absolute derivative difference is2.4377509430436495e-8; worst normalized
gate ratio is.04875293505246781, with acceptance≤1. Matrices contain mixed SI
derivative units, so neither number is a physical trajectory error or accuracy
claim. Additional1e-12 structural checks verify closed-form command/progress,
physical A_w=h*A_C and tiny B_alpha=h²*A_C, semiimplicit q/v identities,
independent cell/global products and matched-origin defects. This external
full-rollout multiplication is a QA oracle; the API has no horizon planner.

Read-only static review found omitted initial-domain and mass-condition checks
in the audit, corrected before its first numerical call. Root numerical
attempt1 passed with source SHA eaef92bbaf4134153c08cc74b7997a03f064047c2e2984dc2a5e15aa12d632b5
unchanged. No numeric source, policy, parameter or tolerance repair followed
results. Source/runtime/input freezing preceded all numerical forecasts.

Common actual task boundaries s=0/r=0 and terminal bounds are intentionally
outside this prototype's two-sided support. They preserve forward values but
lack a certificate here; this is not a nondifferentiability or safety proof.
Actual history must not be moved to epsilon. A separately validated boundary
or canonical-extension policy is required before main-controller startup.
Command jerk/progress slew, physical stopping/geometry, accuracy, computational
budget and full task success remain separate unresolved integration gates.

Root evidence archive8de8d50dd16029eb9752442b5862b00dd106066bd59372487cc7d3fde5b69456
has487 regular members and486 payloads; SHA-256, all payload hashes and
membership were verified on Dell D storage and Mac. Source snapshots, inputs,
outputs, strict physical diagnostics, stdout/stderr/exit codes and declared
fixtures are preserved. Archive locations and final producer closure/visual
checks are recorded in the companion checkpoint JSON.

Final producer closure: all2611 live/cache/embedded identities and3267 current
archive payloads pass independently on Dell and Mac. The original suffix-only
closure checker refused a preserved historical manifest; the exact-selector
v2 checker fixes this read-only archive parsing limitation. Original checker,
error transcript, failure record and final closure are preserved in a separate
7-regular-member archive. The producer's first incomplete publication and its
visual-record/layout/pre-freeze workflow failures also remain unchanged.
Root independently viewed both final figures and verified their data/provenance
against frozen native output. All small sources are imported for Git backup;
large evidence remains in the companion checkpoint's verified Mac/Dell paths.
