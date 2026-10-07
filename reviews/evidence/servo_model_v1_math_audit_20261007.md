# Independent causal servo-model v1 mathematical audit

Date: 2026-10-07. **FAIL_MODEL_INELIGIBLE independently reproduced; Phase 5 remains unaccepted.** No new plant/fitting trials, model coefficients, controller integration, authoritative Dell edits, external-chat messages, commit or push. This review checks the frozen empirical model and recorded development data; it does not validate FR3 predictive control, robust error bounds, task accuracy, stopping or online timing.

Reproducer: `scripts/phase5/audit_servo_model_v1_math.py`. The effective-input hashes, full recomputed metrics, worst windows and training-only residual diagnostics are in `servo_model_v1_math_audit_20261007.json`. It ran in the unique Dell directory `/home/codextransfer/clean-audits/servo-model-v1-math-20261007/output-v3/`; the JSON was copied to Mac and its oracle source SHA verified. Thirteen effective source/model/data/metadata inputs are hashed. This is not another verification of the larger 176-input archive closure, which remains separately documented by root.

## Identity, timing and causal semantics

The model SHA is `904460b19cd1014b624e15a6e2dd8827f07a590db08c3d60f86ce896e8a19200` before and after the audit. It matches the validation pre-run freeze and both pre/post-run execution hashes. Model creation UTC is 05:37:18.791802; validation freeze UTC is 05:37:53.238024 on 2026-10-07. The runner writes/materializes that freeze before launching seed 91012. The model, fitting/evaluation script, validation runner, synthetic test source and identification C++ source match their effective frozen hashes. The actual runner is `scripts/phase5/run_servo_validation_v1.py`, and synthetic tests are `scripts/phase5/servo_model_v1_test.py`; no corresponding runner exists under `tests/`.

Training is seed 91011, raw SHA `ab9d14efa1a5886c0683db25345f24d5cacd55343e2768eb60536fa180a11dce`. Validation is seed 91012, raw SHA `3331840951457d0219cc0c461ea1339cead478211727c3ffc8579a7e2f847912`. Training identification uses exactly 4,000 excitation substeps; warmup and stopping are excluded from fitting. The frozen coefficients satisfy the standardized training normal equations to maximum absolute residual 6.624e-14, without refitting. Metadata records the separate seeds and unmodified model; the validation code performs evaluation only. These development seeds are distinct from final research evaluation.

The C++ fixture updates and accepts target c before `plant.step()`, then records measured q/v immediately before each 2 ms step. The same target is held for both substeps of a 4 ms command. Therefore `c-q_before` and `v_before` are causal features for the next physical velocity. Independent raw checks verify contiguous clocks, physical state chains and identical targets inside each hold; `q_post=q_before+.002*v_post` agrees to about 4.44e-16 rad.

The model is

```
v_next = E(c-q) + Vv + d
q_next = q + δ v_next, δ=.002 s
P = [[I-δE, δV], [-E, V]]
Q = [[δE], [E]], affine = [δd,d].
```

All stored matrices exactly match independent reconstruction. Held-target spectral radius is independently 0.9962970240626702, below one. Stability does not establish an accurate forced response.

Each forecast starts at a 4 ms boundary in excitation/stopping, initializes once from that boundary's measured physical state, and propagates `y_next=Py+Qc+d` using the known accepted target sequence. It never resets to future physical states. Only the final measured state scores the endpoint. The independent matrix-based implementation also matches individual scalar-window propagation and reconstructs error through `error_next=P error-residual`, where residuals use measured transitions only for the **diagnostic error decomposition**. Residuals never enter the forecast. This is conditional recorded-input validation; it does not show that arbitrary future MPC target sequences are accurately predicted.

## Independently reproduced horizon results

| Horizon | Validation windows | Maximum q error [rad] | Maximum v error [rad/s] | Frozen horizon gate |
|---|---:|---:|---:|---|
| 2 ms | 2,219 | 1.1459151e-7 | 5.7295755e-5 | PASS |
| 4 ms | 2,219 | 2.6248388e-7 | 7.3946183e-5 | PASS |
| 40 ms | 2,210 | 1.4166897e-5 | 6.0979233e-4 | PASS |
| 800 ms | 2,020 | 4.4366573e-4 | 1.8569966e-3 | FAIL |

The 800 ms limits remain 1e-4 rad and 1e-3 rad/s. The validation position worst window starts tick839 (joint index1); velocity worst starts tick2313 (index1). The training 800 ms diagnostic also fails: 1,991 windows, q maximum 4.1925807e-4 rad and v maximum 2.0709584e-3 rad/s, with worst starts tick2274 and tick2343, both joint index1. These maxima are not simultaneous errors on every joint.

All reported metrics agree with independent recomputation within 1.857e-14. Error propagation from one-step residuals agrees within 1.604e-13. This identifies accumulated model mismatch, with no teacher forcing or speculative solver attribution. Both datasets have zero measured active-state local-box violations. The existing box check concerns recorded physical state coverage; it is not a robust forecast tube or a general target-error feature-domain certificate. Training contains 1,000 warmup/4,000 excitation/380 stopping rows; validation contains 1,000/4,000/438. Forecast scoring excludes warmup but includes stopping by its frozen policy.

## Training-only residual/deadband/conditioning findings

No validation outcome was used to select the following residual features or strata, and no new model was fitted. Statistics use only the 4,000 seed91011 excitation rows. The current 15-column standardized design is full rank, condition number 74.2344; the unscaled design is 149,999. The target-minus-position and velocity features on the same joint are strongly correlated (.98059–.99826). Standardization addresses units but does not remove those correlations or confer a unique mechanical interpretation on E/V.

Joint index1 has one-step velocity residual RMSE 1.15637e-5 rad/s and maximum 5.15216e-5. Its lag-one residual correlation is .22559; several other joint residuals have correlations .53–.82. Thus residual samples cannot be treated as independent white prediction noise merely because the least-squares mean residual is near zero.

The fixed velocity strata at ±1e-5, ±1e-4 and ±1e-3 rad/s do not support a simple dominant Coulomb-sign correction. For index1, mean true-minus-predicted residual is +1.497e-6 at v<-1e-3, -2.680e-6 for 1e-4<=v<1e-3, and +2.322e-6 at v>=1e-3. This is not a single sign-reversing offset. Only 11/4,000 index1 samples have next physical velocity within ±1e-5 while the prediction is outside that interval. This diagnostic does not prove absence of friction/deadband, but it gives weak support for making a friction switch the first correction.

A stronger training association is omitted **configuration dependence**. Residual correlation with measured configuration of joint index1 is -.644, -.438, -.683, +.607, +.733, +.377 for outputs0–5, respectively. These are descriptive correlations, not proof of gravity or inertia as the cause. Velocity-sign correlations among their strongest alternatives are much smaller, typically below .07. Adding all seven centered physical configuration features gives a 22-column design of full rank22 and standardized condition 256.120; this was a design/SVD check only, not a coefficient fit.

The smallest well-supported next causal class to **test on training** is therefore a local configuration-dependent affine offset:

```
v_next = E(c-q) + Vv + G(q-q_ref) + d
q_next = q + δ v_next
```

Choose q_ref from the training record and preserve separate accepted c/w state. Forecast q, rather than future measured q, supplies the new term throughout every window. The physical transition changes to `P=[[I+δ(G-E),δV],[G-E,V]]`; Q and the affine offset become `[δE;E]` and `[δ(d-G q_ref); d-G q_ref]`. This removes the intentionally translation-invariant local assumption, without changing the common physics or introducing robot-specific controller branches. A configuration term might capture local gravitational/other bias variation; that physical interpretation remains a hypothesis.

Fit and assess this class only under a newly recorded training protocol, check full rank/conditioning and stable held transition, freeze it before fresh development validation, and retain v1's failures. Reusing already inspected seed91012 may be a regression but must not be called an untouched model-selection holdout. Do not add validation-selected features, relax error limits, integrate v1, or infer a stopping certificate from spectral radius. The next class is not validated by this audit. Meaningful executed progress, 10 mm accuracy, timing and the independent Phase 5 root gate remain pending.
