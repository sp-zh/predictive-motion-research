# Independent augmented-servo affine unit oracle

Status: **SYNTHETIC_AFFINE_ORACLE_PASS; Phase 5 remains unaccepted.** No robot runs, fitting trials, privileged simulator rollout or authoritative Dell edits. This is an independent transition/elimination oracle for future C++ checks, not evidence that an FR3 servo model is valid. The parent coordinates the milestone commit/push.

Source: `scripts/phase5/augmented_servo_reference.py`, Python standard library only. Frozen output: `results/phase5-reference/augmented-servo-oracle-20261007-v3/{oracle.json,summary.json,READY.json}`. READY hashes were verified on Mac; the two data files total 324,172 bytes. V1/v2 are earlier successful local intermediate outputs, not robot failures or final source identities. V3 includes full transitions, global state/control sensitivities, lifted dynamics matrix/RHS, condensed quadratic cost, complete command/physical histories and terminal counterexamples.

## Exact affine command/physical transition

Let measured physical y=(q,v), accepted command target c, accepted velocity w and input α=command acceleration. All vectors have n joint entries. For an actual command duration δ with a held target, the physical model supplies `(Pδ,Qδ,dδ)`:

```
w+ = w + δ α
c+ = c + δ w+ = c + δ w + δ² α
y+ = Pδ y + Qδ c+ + dδ
```

For z=(y,c,w), this is `z+=Fδ z+Bδ α+fδ`, with block matrices

```
       [ Pδ  Qδ   δ Qδ ]        [ δ² Qδ ]        [ dδ ]
Fδ =   [  0   I    δ I ]   Bδ = [ δ² I  ]   fδ = [  0 ]
       [  0   0      I ]        [  δ I  ]        [  0 ]
```

For microsteps δ1...δL at constant cell α, multiply F in chronological transition order. Cell `A=F_L...F_1`, `B=sum_i(F_L...F_(i+1))B_i` and `d=sum_i(F_L...F_(i+1))f_i`. Empty products are identities. The independent closed-form command endpoint is `w+=w+hα`, `c+=c+h w+0.5(h²+sum_i δ_i²)α`. For h=mΔ with Δ=4 ms this gives `c+=c+h w+0.5(h²+hΔ)α`; each 40 ms cell composes ten target updates.

For a noninteger cell h=mΔ+ε, this oracle explicitly starts a fresh cell update grid and applies m full updates followed by one endpoint update of duration ε. That final event uses `w+=εα,c+=εw+` and separately supplied `Pε,Qε,dε`. It does **not** linearly interpolate the 4 ms matrices. This formal fractional policy is not automatically the fixed-4 ms runtime policy. A deployment should restrict preview cells to integer command periods or separately declare/verify how its actual update grid treats fractional cell boundaries; silently treating fractional target events as actual 4 ms commands is invalid.

The synthetic physical fixture is the exact critically damped scalar servo on each joint: `qddot=γ²(c-q)-2γv+g`. It uses distinct declared γ and nonzero g, with exact held-target matrices

```
Pδ = exp(-γδ) [[1+γδ, δ], [-γ²δ, 1-γδ]]
Qδ = [1-P00, -P10]^T
dδ = Qδ g/γ².
```

Direct stepping instead evaluates the scalar equilibrium/displacement solution, avoiding transition matrix multiplication. No fixture parameter is inferred from the FR3.

## Executed checks

Three fixtures cover n=1 uniform 40 ms cells, n=1 mesh `[.007,.041,.023,.040,.009]`, and n=3 mesh `[.009,.040,.017,.041,.027]`. Fresh physical q,v differ from accepted c,w, previous command acceleration differs from physical acceleration, and every physical transition has a nonzero affine offset. Across these fixtures:

| Check | Maximum absolute discrepancy |
|---|---:|
| Direct scalar stepping versus affine physical/command rollout | 2.776e-16 |
| Control sensitivity versus centered finite difference | 4.424e-12 |
| Initial-state sensitivity versus centered finite difference | 1.245e-11 |
| Generic pivoted elimination of lifted state equations versus condensed maps | 1.111e-16 |
| Original lifted dynamics residual on direct states | 1.104e-16 |
| Accepted command acceleration identity | 3.886e-16 |
| Closed-form endpoint target moment | 2.776e-17 |
| Full synthetic quadratic objective after state substitution | 5.205e-18 |

Lifted equations include initial-state rows and `z_(k+1)-A_k z_k=B_k α_k+d_k`. A generic pivoted solve eliminates all lifted states; its offset/control coefficients match the independently constructed condensed recurrence. The objective includes all state components, nonzero targets/offsets and control regularization; it is only an algebraic fixture, not a proposed research cost.

## Histories and terminal semantics

The oracle records every microstep's accepted c,w, physical q,v, mean physical acceleration/jerk, and exact command derivatives. Command acceleration is `(w+-w)/δ=α`. Command jerk is `(α-previous_accepted_α)/δ`, with the actual first update duration, including fractional events. Physical mean acceleration is `(v+-v)/δ`; physical mean jerk differentiates that quantity against its separate previous physical acceleration. These are sampled derivatives, not continuous-time extrema.

At a piecewise-constant coarse cell change, dividing `α_k-α_(k-1)` by the 40 ms cell length does not equal executed 4 ms command jerk. Either impose the actual event denominator or explicitly realize a jerk-limited ramp and recompute its affine moments. Replanning and projection must preserve accepted command history; neither a forecast α nor a measured velocity may replace that history. Physical derivative constraints remain independent of command limits.

An endpoint w_N=0 makes the **command target** stationary only if the following input is α=0, with its transition admitted by the last accepted acceleration/jerk history. Physical v_N=0 alone does not make physical state stationary. The physical equilibrium condition is `(I-P)y_eq=Qc+d`; a stopped physical state also requires its velocity component zero. The synthetic counterexample has w=v=0, a 1 mm displacement from the held-target equilibrium and γ=10/s. Holding c immediately produces v=-0.000384316 rad/s after 4 ms and a peak speed 0.00367879 rad/s. The sampled hold reaches the declared 1e-4 rad/s stop threshold permanently within the recorded tail at 0.648 s. Thus even exact `v_N=w_N=0` is not an invariant stopping condition.

## Exact terminal equalities and a declared settling alternative

Exact `v_N=w_N=0` can overconstrain a short horizon. In the one-input/one-microstep scalar fixture, w_N=0 fixes α=-2 rad/s²; resulting physical v_N=-0.00873983 rad/s, so the two equalities cannot both hold even before adding α/jerk limits. The synthetic two-microstep terminal velocity sensitivity rows have condition number 1348.98 and physical/command row-norm ratio .00167646. This demonstrates possible row-scale difficulty. It does **not** establish that the existing 0.8 s QP timeout comes from terminal equalities: the same fixture's 20-by-40 ms terminal row condition number is only 4.66952. The oracle runs no QP solver and makes no timing claim.

A separately declared development policy can replace instantaneous exact physical rest by **safe held-target settling**, while retaining all ordinary physical and command limits. First require an admitted zero-command continuation (w=0, α=0, unchanged c, valid jerk history). Let physical error `e=y-y_eq(c)` and hold transition e+=P e. For a validated model, select a stable invariant terminal error set and a finite declared tail length L. Require every tail state/uncertainty tube to obey the unchanged joint position, velocity, acceleration, jerk, collision, singularity and actual-task accuracy envelope. Require at the declared stopping time

```
|C_v P^L e| + validated_velocity_prediction_error <= v_stop
```

and the analogous position/task-error bound. The existing observed physical-stop threshold is `v_stop=1e-4 rad/s`; it is a stopping criterion, not permission to enlarge any physical safety limit. If the uncertainty allowance is unavailable or exceeds that threshold, the model cannot certify stopping. Acceptance still requires observed physical stopping and actual executed tracking.

For a quadratic terminal error set `e^T S e<=ρ`, a sufficient component velocity bound is `sqrt(ρ * a_i S^-1 a_i^T)` with `a_i` the i-th row of `C_v P^L`; add a separately justified model-error allowance. Stable hold invariance requires `P^T S P-S` negative semidefinite, with appropriate robust tightening when the model has disturbances. Geometry and task accuracy need their own certified set/tail checks; this quadratic bound alone is no collision certificate.

Alternatively, an explicitly named “stopped at horizon” condition may use a prefrozen physical velocity tolerance plus equilibrium/hold-continuation checks, rather than native equality v_N=0. Either change alters the terminal policy and feasible set; it requires a new recorded protocol, retained comparisons, original-SI validation and independent review. No terminal inequality, long tail or settling allowance is silently recommended for the current accepted-command policy. Phase 5 still requires a valid servo model, meaningful progress, executed 10 mm accuracy, timing and root acceptance.
