# Signed command velocity cone: independent component audit

Verdict: **PASS_ISOLATED_SIGNED_COMMAND_CONTINUATION**, limited to the declared sampled command-speed/acceleration/jerk contract. This supports prospective fixture integration with original command guards and candidate continuation verification retained. It does not certify joint position, geometry, physical stopping, a full MPC horizon, RET002 as a whole, or Phase5. No plant run, fitting, authoritative edit, or Git action was performed.

## Frozen inputs and independent execution

The Mac archives match the declared Python SHA `263126c58e090ea7f9bb5f44b41000fb3b894f1f4ff4121872cbd643afb6a62d` and C++ SHA `b13fee314f7b1717725424bdf564b478b3add9ad025da177ff54c941c2340d47`. All source-manifest members and 15 frozen source/binary/input identities were independently checked against the archived bytes. The Python in both packages is SHA `d765998f96a10a1745cd8b61e15272c66e40e52230aaa312092a615ec783d18e`; C++ header SHA `4e514fe97b0298361e81b5bdfb22793eb22cc0237aaef012c90cc8c23c3cbc97`. The retained actual raw SHA is `561d63684b3acc591acf2f287e6f7f264a340207cebe8767887b5107dadc661c`.

The independent [audit script](../../scripts/phase5/audit_signed_command_cone.py) imports no producer Python. It compiled a separate consumer of the frozen header on Dell under `/home/codextransfer/clean-audits/signed-command-cone-independent-20261007-v1`, where `long double` has 64 mantissa bits. Its reference enumerates integer prefixes with exact rational arithmetic on the actual binary-double inputs and separately steps jerk recovery to zero. This is model algebra, not a physical rollout.

## Exact command semantics and finite rows

Let accepted command history be `(w, alpha)`, timestep `h`, limits `V,A,J`, and the next selected command acceleration be `a`. Then

\[
 w^+=w+ha,\qquad |a|\le A,\qquad |a-\alpha|\le Jh.
\]

These are command quantities. Physical measured velocity and acceleration do not substitute for `w` or `alpha`. The rows alone receive only `w` and do not enforce the acceleration-history/jerk intersection.

For `a>=0`, the least further positive displacement uses `a_j=max(0,a-jJh)`, starting with `a_0=a`; the negative case is its reflection. Before clipping to zero, the cumulative upper extremum is `w+Kh a-Jh²K(K-1)/2`. Since `|a|<=A`, checking `1<=K<=ceil(A/(Jh))+1` covers every potentially active prefix. Both signs therefore give

\[
-V-\tfrac12Jh^2K(K-1)\le w+Kha\le V+\tfrac12Jh^2K(K-1).
\]

Substitution of `w^+=w+ha` yields the producer's `K*w_next` rows with offset `(K-1)w`. Exhaustive integer bounds also yield the exact candidate acceleration interval after intersecting `[-A,A]` and `[alpha-Jh,alpha+Jh]`. Lower reflection uses `r=w+V`; upper reflection uses `r=V-w`, with signed acceleration reversed and `r` bounded in `[0,2V]`.

This establishes existence of a speed-bounded future command continuation; recovery of acceleration to zero alone can leave nonzero command speed. The numerical greedy tests additionally reach `w≈0,alpha≈0`, but are not a general finite-time stopping proof. In the explicit `(w,alpha)=(-.0008,.2)` fixture, the first command reaches `w=0` while `alpha=.2`; jerk limits force the next acceleration to at least `.12`, and velocity moves again. Eight greedy selections reach both quantities below `1e-14`, without discarding history when speed first reaches zero.

## Results and numerical boundary

The fresh audit covered 119 cases (117 valid-input cases, two invalid limit/budget cases), including reflection pairs, hard speed boundaries, unstable histories, three alternative limit sets, and actual ticks 785/792. There were 333 exact recovery checks at interval endpoints/midpoints and 1779 finite rows. There were no failures, no exact endpoint speed/jerk excess, and 111 feasible greedy histories all finished within 123 selections. The maximum interval difference from the exact unshrunk bounds was `1.3211654e-14` acceleration units, consistent with the deliberate inward margin.

`accelerationInterval` computes in long double, subtracts `64*double_epsilon*max(|bound|,Jh)` from the nonzero-distance recovery limit, and rounds the final lower/upper doubles inward using `nextafter`. However, **candidate QP row bounds are cast directly to double and are not rounded inward**; the largest observed outward row-bound difference was `7.8166806e-16` velocity units. The solver's existing `1e-7` SI tolerance is also larger than this interior margin. A solved point satisfying those rows within solver tolerance is not by itself an exact continuation certificate. Keep original derivative/position/geometry guards and explicitly check the final `(w,alpha,a,w_next)` continuation before accepting a command; do not discard candidate history or enlarge physical limits. The tested numerical claim concerns these normal-range inputs on the stated Linux precision, not every extreme finite input or every long-double ABI.

Actual tick 785 had `w=-.040700006326262854`, `alpha=-.9999999999999991`; the most favorable next acceleration is about `-.92`. Even maximal jerk recovery crosses the speed lower bound at its tenth next command (first excess `.0006000063262628202`). Tick 792 had `w=-.061980006326262695`, `alpha=-.5199999999999909`, so next acceleration must lie approximately `[-.60,-.44]`; even its most favorable immediate speed is `-.06374000632626266`, below `-.0625` by `.0012400063262626583`. Both intervals are correctly infeasible. These are actual accepted histories extracted from retained raw data; no hypothetical reconstructed command was labeled executed.

RET002 `progressStopBounds` uses control-before-state semantics, and the shifted speed component agrees algebraically with this cone. Its progress-position constraint is additional. The main controller's prefix check first advances the prefix, then applies a cone with the current control held for an additional step; that is more conservative than selecting the next jerk-limited acceleration immediately. These contracts are not completely equivalent.

Detailed immutable numbers and identities are in [the JSON review](signed_command_cone_math_audit_20261007.json); executable source, input cases, captured consumer output, source snapshot, and identity checks are retained under `results/phase5-reference/root-signed-command-cone-audit-20261007-v1`. The audit generator's final SHA is `04ec34ab52eaa0ee34ee439cdc89ddba5070d860315c0588152b069a5275d74e`.
