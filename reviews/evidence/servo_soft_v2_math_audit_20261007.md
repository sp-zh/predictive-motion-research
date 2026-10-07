# Independent soft-friction v2 mathematical audit

Verdict: **PASS_LOCAL_RECORDED_INPUT_PREDICTION**. This is a component verdict for the frozen model under the new recorded validation input sequence. **Phase 5 remains unaccepted.** No main-controller integration, new plant/fitting trial, coefficient mutation, authoritative Dell edit, external-chat message or Git operation was performed. Old v1's model gate remains FAIL.

Reproducer: `scripts/phase5/audit_servo_soft_v2_math.py`; effective inputs/results: `servo_soft_v2_math_audit_20261007.json`. Execution used the unique Dell directory `/home/codextransfer/clean-audits/servo-soft-v2-math-20261007/output-v2/`. The independent script derives force from the scalar box-constrained quadratic; it never calls the production predictor or fitting code. Output was copied to Mac and its source hash checked. Parent owns the milestone backup.

## Scalar formula, units and scope

For one scalar hinge define mass-like effective parameter m>0, gain k, damping D, bias g, impedance I in (0,1), force limit η and reference decay B. Let `s=k(c-q)-Dv+g`. The scalar box objective is

```
min_|f|<=η  0.5(1/m+R)f² + (s/m+Bv)f,
R=(1-I)/(I m).
```

Its unique force is `f=-clip(I(s+m Bv),-η,η)`. With δ=.002 s, the frozen transition is `v+=v+δ(s+f)/(m+δD)`, `q+=q+δv+`. Units are consistent: c,q in radians, v in rad/s, k in Nm/rad, D in Nm·s/rad, s/f/g/η in Nm, B in 1/s and m in kg·m² for a scalar angular coordinate. The denominator includes both actuator velocity gain and passive joint damping.

MuJoCo 3.3.7 treats friction loss as a force box with zero position residual. Its fixed-tag implementation uses impedance regularization, zero friction stiffness and reference decay `2/(d_max*timeconst)`, with a safety floor on timeconst. Its DOF regularizer uses `dof_invweight0`; full inverse inertia couples constraints. Therefore replacing that scalar approximation and inverse inertia by the same fitted 1/m is an **empirical diagonal surrogate assumption**, not an exact FR3 mass matrix. [Fixed 3.3.7 constraint source](https://github.com/google-deepmind/mujoco/blob/3.3.7/src/engine/engine_core_constraint.c).

The scalar implicit damping denominator follows the implicit-in-velocity form with damping derivative -D; constraint-force derivatives are excluded from that integration matrix. The complete robot has omitted coupling and configuration-dependent terms. [Fixed 3.3.7 computation documentation](https://mujoco.readthedocs.io/en/3.3.7/computation/index.html). Positive fitted m values .074263–1.366440 kg·m² and inactive fit bounds do not turn them into measured physical body inertias or establish general stability/safe holding.

Independent inheritance-aware XML inspection exactly matches public k, D, η, I and B arrays, and confirms radians and `implicitfast`. Gains are 4500/3500/2000, passive damping adds .21 to velocity gains 450/350/200, η varies by joint, I=.9 and B=105.2631579/s. The model's XML and robot-configuration identities match the prospective freeze. These checks apply to this XML's supported standard reference/default branch; they do not validate arbitrary actuator transmissions, solver overrides or other integration settings.

## Branch derivatives and held-target composition

Let gain `a=δ/(m+δD)`. In the interior force branch,

```
∂v+/∂q = -a(1-I)k
∂v+/∂v = 1-a[(1-I)D+I m B]
∂v+/∂c = a(1-I)k.
```

In either saturated branch replace `(1-I)` by 1 and drop the `I m B` term. The q+ derivatives follow `q+=q+δv+`. These independently derived expressions match the production tangent formula. Centered finite differences on explicitly synthetic interior and both saturated fixtures give maximum errors 8.653e-11 for 2 ms and 2.488e-10 for the composed 4 ms Jacobian. The scalar box KKT residual on all replayed forecasts is at most 4.441e-16.

The same accepted target c is held for both 2 ms substeps. Evaluate the second branch at the first predicted physical state; compose `P4=P2 P1`, `Q4=P2 Q1+Q2`, with affine offset composed similarly. This remains valid across a branch change when each local derivative exists. Updating command c/w at both 2 ms substeps would change the actual 4 ms interface. At either exact clipping threshold the forward map is continuous but has no unique ordinary Jacobian; the production strict-interior test chooses a saturated-side derivative, not a smoothness certificate. Future SCP integration must evaluate the exact forward model/branches and retain nonlinear verification.

## Identity, fresh waveform and independent replay

Model SHA is `984ee85d086aeba7da8260a20b21b301e23dfd2c698a6c61ace0ff956bbec1bb`, unchanged before/after validation and this audit, matching the pre-run freeze. Model creation is 2026-10-07 05:54:21.973828 UTC; validation freeze is 05:55:50.377993 UTC. The frozen runner writes/materializes its freeze before invoking the new validation-only C++ executable. Model/predictor/test/runner/scorer/trace-reader, C++ fixture, configuration, XML and robot configuration hashes match the freeze.

Training remains the completed seed91011 excitation trace. The new seed91012 validation raw SHA is `c435bea765c9a12e73bc12d12e2dfa7b6cbb6ddf877f1d519d9056810b21f03c`. Its separately frozen profile is 8 s, amplitude .0006 rad, frequency `.73+.103j` Hz and phase `.27j`. The new C++ fixture reads those values and rejects training mode. The old seed91012 raw remains SHA `3331840951457d0219cc0c461ea1339cead478211727c3ffc8579a7e2f847912`, unchanged. This is prospective development validation after earlier failures, not a final research holdout or evidence of many independent trials.

Every window initializes measured physical q/v once at a 4 ms command boundary and uses only known subsequent accepted targets. Future physical states are used only for scoring. The raw clock, state chain and two-substep hold are verified. Validation contains 1,000 warmup, 4,000 excitation and 446 stopping substeps; warmup is excluded from scoring.

| Horizon | Overlapping windows | Maximum q error [rad] | Maximum v error [rad/s] | Gate |
|---|---:|---:|---:|---|
| 2 ms | 2,223 | 4.0414577e-8 | 2.0207289e-5 | PASS |
| 4 ms | 2,223 | 8.5393594e-8 | 2.3499780e-5 | PASS |
| 40 ms | 2,214 | 2.5273695e-6 | 8.0233243e-5 | PASS |
| 800 ms | 2,024 | 1.1901389e-5 | 8.4368502e-5 | PASS |

Independent report discrepancies are at most 1.085e-19. The 800 ms q worst window starts tick1159 on index2; v worst starts tick2310 on index0. All windows pass the unchanged frozen limits. Zero measured domain violations and zero predicted domain violations across the checked 800 ms windows were independently verified. These are overlapping windows of one forced trace, not 2,024 independent experiments.

## Domain coverage and main-controller implication

The actual validation physical q spans only .0007445–.0010132 rad per joint; accepted target spans about .0012 rad (±.0006 command amplitude). Physical |v| reaches .00358924 rad/s, below the declared .005 bound. Observed target-minus-q spans are about .0007551–.0010185 rad, around nonzero offsets caused by the position servo. The frozen q box adds .002 rad on each side of training extrema; target-error bounds add .0003. Passing a trace inside those enlarged boxes does not demonstrate accuracy at every point in either box or across arbitrary combinations of q,v,c.

Most joints remained in the interior friction branch throughout the replay; only indices1 and6 exercised saturation. Synthetic derivative fixtures check the algebra in every branch, but do not establish physical prediction accuracy for unvisited branch/state combinations.

The previous high-Q preparation moves physical joints up to .002823 rad. A direct coverage comparison with all 278 old path substeps shows actual violations of **the soft-v2 declared domain**, using pre-step physical q/v and current accepted target:

| Domain field | Joint indices with violation counts |
|---|---|
| Physical q | index3: 21 |
| Physical v | indices0/1/2/3: 47/77/73/142 |
| Accepted target minus physical q | indices0/1/2/3: 77/79/98/155 |

Therefore simple amplitude comparison is insufficient: the old preparation already leaves both observed support and parts of the declared model box. The corrected main controller must log and enforce model-domain coverage for measured initialization and every predicted substep. If that preparation/motion range is still intended, obtain prospectively frozen expanded development excitation/validation rather than extrapolating the present PASS. Alternatively, an explicitly scoped controller variant may restrict its model use to the present domain and retain failures when required motion cannot fit. Enlarging metadata bounds alone supplies no new accuracy evidence.

This audit accepts only recorded-input prediction under the new waveform. Root still needs the corrected C++ command/physical contract, a complete main-controller diagnostic with meaningful progress and executed 10 mm accuracy, failure/stop behavior, timing and independent Phase 5 review. The component PASS does not establish hardware, task, online, arbitrary-command, uncertainty or safe-hold certification.
