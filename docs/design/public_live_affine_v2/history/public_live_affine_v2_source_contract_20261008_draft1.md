# Live typed public model to affine horizon: proposed source contract v2

SOURCE/DESIGN ONLY, pending independent review. Backup prerequisite:
3f98f69fbe040802f0887d6a80ea5005a2fc1ad9. No source in the old module, frozen
ec1 inputs, old profiles, model or main is changed. No build/kernel/model/plant/
solver/scorer call. Phase5 NOT_ACCEPTED; Phase6 NOT_STARTED; original FD FAIL kept.

## Requirement and current boundary

Original prompt section16 asks configurable nominal N20, approximately .5–1s;
section36 gives N20/.8s; section41's1.5s is a later study example, not permission
to execute that study. Current verified affine v1 covers fixed N1/N4 diagnostics,
maxcells16/maxsamples512. Its native path normalizes reconstructed archived
map/state carriers, pins old f1 probe ELF and a source file SHA, and does not
exercise a new actual Model construction/rollout. Merely increasing those old
limits or pretending a new consumer ELF is f1 cannot implement this contract.

## Typed boundary and provenance

Use a new namespace/module. The physical observed snapshot supplies q7/v7;
accepted history separately supplies C7/w7/previous accepted alpha7; committed
virtual progress supplies s/r/previous accepted b. Pack z=[q,v,C,w,s,r]30 and
u=[alpha7,b]8. Never set C=q or w=v to conceal history disagreement. Add explicit
boundary tick, completed-command sequence and observation/history association;
distinguish issue time from represented completed boundary. In-flight/partial,
stale or mismatched snapshots refuse a new forecast. This transaction binding is
required caller data, not an established property of the old untimestamped API.

Proposed entry points (declarations only):

```
planMesh(HorizonSpec, ResourcePolicyV2) -> CycleMesh
makeInvocation(ObservedPhysical, AcceptedCommandHistory, ProgressHistory,
               CycleMesh, nominal_alpha_b) -> PublicInvocation
forecastPublic(PinnedModelHandle&, PublicInvocation, ReviewedRunPermission)
               -> OwnedPublicForecast
adaptPublic(OwnedPublicForecast, ResourcePolicyV2, CaptureMode)
               -> CertifiedAffineView | RefusalWithOriginalResult
assembleAffine(CertifiedAffineView, actual_initial, explicit_cost_terms, budget)
               -> assembly + full per-term/sum cost
first4msRequest(current_history, candidate_alpha_b) -> CommandProposal
```

OwnedPublicForecast owns/moves the genuine extension::Result plus invocation.
The permitted forecast function calls that verified handle's Model::rollout;
the adapter itself consumes the result without another model call. Preserve the
full raw value/error/friction/clip/prefix data; avoid copying raw matrices unless
charged. A fake/reconstructed fixture has a separate source kind and cannot
claim this live invocation evidence. All claims about segment/ball/admissibility/
execution/safety/uniform accuracy/controller readiness remain false.

Pinned identity binds actual new producer ELF/build manifest, unchanged model
source/API, derivative policy, XML/constants SHA, ModelMetadata (nq/nv/joints/
frames/masses/armature/damping/gravity/R/B and units), and SDK/runtime manifest.
Create it through the reviewed startup identity check; do not accept a caller's
standalone certificate-true flag or invented nonempty fileSHA. Live kind uses
this manifest and invocation digest; archived kind retains fileSHA/old f1 ID.
Old v1 loader and proof stay unchanged. An identity check does not establish
physical model accuracy, correct controller integration or finite trust radius.

## Exact command timing and complete-map validation

Public source law h=.004: w_next=w+h*alpha; C_next=C+h*w_next. Both new C/w are
held for the two .002s physical substeps. C uses h² alpha, not .5h² alpha. The
progress law separately uses s_next=s+h*r+.5h²*b, r_next=r+h*b, and each half's
own cell-origin polynomial reference. Preserve literal cycle/half roundoff.

When nominal alpha/b is used, compare first request C/w/s/r to the FIRST complete
4ms cycle endpoint. A 40ms cell endpoint is not the next command. For a solved
candidate different from nominal, derive the request from current history and
candidate u0, not nominal future states; this emits no actual command or physical
q/v prediction certificate. Alpha_applied=(accepted_w_next-w_previous)/.004;
command jerk=(alpha_applied-alpha_previous)/.004. At any held-cell boundary use
that same feedback lattice, not the prior coarse cell duration. B history is
accepted progress acceleration. Old previous_model_acceleration does not replace
either history. Supervisor projection changes require logging/revalidation and
warm invalidation; do not silently commit the unprojected forecast/history.

The old main instead requests measured.v+dt*a0 and applies
Caccepted+=dt*velocity, distinguishing model/command acceleration afterward.
Its a0, old rows and validator must not be relabeled as this new alpha. This
unit defines a boundary; later controller/main changes need a separate gate.

Require value.success/has_final_state, extension_jacobian_success and first
uncertified=-1, exact N/sumcycles/2sumcycles rosters and indices/timestamps,
literal origin/input/value endpoint parity and finite nominal defect identities.
Wholecell and every prefix use native cell_A/cell_B/cell_defect/cell_origin.
Map.A/B/defect/origin remain cycle-local even in Result.cell_maps. Failed or
unsupported prefixes return the ORIGINAL result and no full problem/cost/usable
command. No shortened horizon, fabricated tail, fallback double integrator,
trial-origin reset, overwritten defect or tie of independent cell controls.

## Configurable mesh with explicit lattice semantics

Authoritative cycles are positive canonical integers, h=.004/physics=.002 fixed.
UniformExact rejects total_cycles not divisible by N. BalancedInteger uses
cycles[k]=floor((k+1)*T/N)-floor(k*T/N), T integer, T>=N. ExplicitCycles preserves
caller order and exact sum. UI seconds are converted via exact decimal/rational
validation, not nearest integer floating rounding; reports record actual ticks.

- N20/.8s: T200, all20 cells10 cycles,400 physical samples.
- N20/1.5s: T375, [18,19,19,19] repeated5,750 physical samples; explicitly
  nonuniform72/76ms, not uniform75ms. Design support only, no study execution.
- .1/.5/1s are on the4ms lattice; .25/.75s are not. ExactOnly rejects the latter.
  A future opt-in CoverAtLeast policy may report .252/.752s respectively, with
  requested and actual durations both explicit and shared across comparison
  methods. It needs its own reviewed study protocol; it is not enabled here.

## Resource policy and capture design

Proposed independently versioned public envelope: nx30/nu8, maxcells32,
max_total_cycles375, maxsamples750; positive configurable N<=min(32,T), not a
hardcoded N20. Candidate hard ceilings for review:32 terms,8192 total factor
rows,12m entries per matrix,64m simultaneously owned numeric elements,
512m cumulative charged elements/case and1024m/batch,256MiB serialized diagnostic
bytes. These are PROPOSED ceilings, not v1 changes or runtime/timing evidence.
Plan exact dimensions/checked products/model-result upper storage, copy and
workspace/output charges before materialization; bind case planned ceiling into
every reservation, including failures. No failed-case refund or auto cap growth.
Native SDK internal allocation is not instrumented today: its bounded result
storage plan is separate from a claim about all allocator/process RAM usage.

Default Compact keeps literal raw/prefix inventory and boundary o/M/P, exposes
sample views by streaming o/M/P from the cell origin, and forms local feature
rows without allocating a dense selector over all y for every sample. Retain or
stream requested factors/sufficient outputs for independent checking. DenseAudit
is explicit and refuses a complete plan that exceeds quotas; never silently omit
requested samples/terms. For N20, DX630/DU160/DY790: v1 dense lifted sample
selectors alone store400*30*790=9.48m doubles, above its8m cumulative cap;
750 selectors alone store17.775m. Thus cap-only edits are insufficient.

Retain independent lifted L/E/f/P elimination as an audit path; native compact
assembly still uses actual offsets and independent per-cell inputs. Resource
support means valid shape/configuration can be admitted under a declared plan;
it does not promise complete strict-branch support for every nominal rollout.

## Explicit cost mapping and separate unsupported promises

Full .5||F y+f0||²+ell^T y+c0, per-term and ordered sum, raw H plus literal
symmetric-part derivatives remain the reviewed algebra. Costs name physical q/v,
accepted C/w, command alpha and virtual s/r/b separately. Task rows select q/s:
ebar+Jq(q-qbar)+Js(s-sbar); use explicit residual scaling and actual mesh weights.
Import old w||m z+c||² only with F=sqrt(2w)m/f0=sqrt(2w)c and separate linear
rewards. No default weight tuning/import is authorized. Physical sampled a is
(v_after-v_before)/.002; physical jerk needs its own prior physical a. Alpha is
not physical qdd/effort. Old q Bernstein/double-integrator enclosures, geometry,
trust/admission, stopping, terminal equilibrium, solver/SCP/main and deadlines
are not inherited by the adapter. v=w=r=0 alone is not physical equilibrium.

## Independent preregistered tests and version sequence

Before any run: source/interface independent review and backup, distinct target,
empty schema/build scope, pinned XML/constants/SDK/consumer/metadata/inputs/
policy and full new freeze with copy verification. No new run in this unit.

First structural fixtures: real native carrier normalization vs independently
serialized/reference projections, N1/N4 regression, N20/T200 and N20/T375 shape
plans, nonuniform order and first-cell multi-cycle history mismatch. Live-call
proof requires separately authorized actual Model invocation, not archived
reconstruction labeled live. Complete long-horizon derivative support is unknown;
preserve/refuse failures rather than force a passing fixture or shrink the roster.
Root separately checks lifted/compact all sample o/M/P and full costs/gradients/
constants under nonzero actual/nominal/history/desired offsets and distinct inputs.

Negatives: fake f1 producer identity/fileSHA, wrong XML/constants/metadata, stale
history/in-flight tick, C=q/w=v reset, .5h² command law, whole40ms first request,
coarse-denominator jerk, local-lastcycle fields, prefix-to-full promotion,
fractional/zero/negative/wrong-sum mesh, implicit .25/.75 rounding, excessive
factor/sample/output/copy budgets, nonfinite/intermediate overflow, dropped
linear/constants/initial/sample sensitivities or false scope claims. Freeze
rosters/gates BEFORE outputs; no repairs, outcome selection or epsilon tuning
after first results. The ec1 algebra proof and all old failures remain historical.
