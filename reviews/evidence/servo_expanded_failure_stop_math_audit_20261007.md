# Independent expanded validation failure/stop mathematics audit

Verdict: **VERIFIED_RETAINED_FAILURE_AND_COMMAND_GEOMETRY_CONFLICT; NOT_STOPPING_PASS**. Phase 5 remains unaccepted. The soft model's earlier local recorded-input prediction PASS does not cover this failed expanded trial. Old v1/configuration-affine failures remain retained. No new plant replay, fitting, authoritative code/model/config edit, external-chat message or Git operation was performed by this reviewer.

Independent reproducer: `scripts/phase5/audit_servo_expanded_failure_stop.py`; results and effective-input hashes: `servo_expanded_failure_stop_math_audit_20261007.json`. Offline execution ran only under `/home/codextransfer/clean-audits/servo-expanded-stop-math-20261007/output-v3/`. The final source/output identity was checked on Mac. Parent owns the milestone backup.

## Two different QPs, with an exact shared conflict

The original expanded raw SHA is `b913b712590be96eeec031a0b62a88e42d462ed2ac13d87ddf6b8a5d648a29e2`, 1,708 physical substep rows at ticks0–853, ending time3.416 s. It ends with no contact and true clearance .0132723321 m. The next tick854 **reconstructed** QP is an offline assembly from the final recorded encoder and accepted command histories. Its state age0 is explicitly an offline convention; no original runtime matrix was captured and no reconstructed command was issued.

The separately executed stop replay first reproduces the past target sequence, including warmup, then captures the actual shared stopping QP at that final state. Its constraint matrix is 67×7, while the reconstructed tracking matrix is 29×7. Their first 21 command rows are byte-value identical. All 29 reconstructed rows are exact coefficient/bound/label subsets of the actual stop's 67 rows. The stop adds 38 geometry rows because its shared fallback activation radius expands beyond .03 m to account for command-target versus measured-position separation. In particular reconstructed covers37/38/39 map to stop rows59/61/63.

Both Hessians are exactly I; the tracking gradient is `-request`, while the stopping gradient is zero. Therefore changing the objective cannot resolve their common infeasible constraint subset. The two freezes share 190 input paths; 188 have identical declared hashes. Shared core source and controller-library bytes were independently checked. The changed paths are the diagnostic CMakeLists and CMakeCache; verified immutable cache blobs differ only by an absent versus empty `_Python3_Interpreter_REASON_FAILURE` entry. This is no claim that every artifact in the larger closure was reverified here.

## Scalar command bounds and exact support proof

For each joint, accepted velocity w and acceleration a_prev constrain next velocity z by

```
w - a_max Δ <= z <= w + a_max Δ
w + Δ a_prev - J_max Δ² <= z <= w + Δ a_prev + J_max Δ²
```

The shared command box also intersects velocity and measured/accepted position limits. Here Δ=.004 s, a_max=1 rad/s², J_max=20 rad/s³, velocity cap=.0625 rad/s and position margin=.005 rad. The explicit additional derivative rows have coefficients 1/Δ=250/s and 1/Δ²=62500/s²; their bounds are in acceleration and jerk units. Independent reconstruction from the final histories agrees with all explicit derivative rows, and the tight intervals agree to 3.47e-18 rad/s. All seven scalar boxes are nonempty. Their exact decimal bounds and active row identities are saved in the JSON. The command-only native-SOLVED candidate has original-row violation zero.

The auditor independently extracts signed scalar intervals from **all 21 command rows**, using exact rational arithmetic on their stored decimal coefficients/bounds. For a geometry row `A_i z>=l_i`, the exact maximum over this Cartesian box is `sum_j A_ij*(upper_j if A_ij>=0 else lower_j)`. Consequently any positive `l_i-max` proves infeasibility without a QP/LP solver.

| Cover | Geometry lower bound [m/s] | Exact box support maximum [m/s] | Positive deficit [m/s] |
|---|---:|---:|---:|
| 37 | -.019226403622487273 | -.022856098144581700 | .003629694522094427 |
| 38 | -.015978487818587003 | -.020990613967262307 | .005012126148675302 |
| 39 | -.015640955717845552 | -.020647626800504510 | .005006671082658957 |

The rational deficits are positive and each maximizing corner is recorded. Independently allowing the original SI acceptance tolerance1e-7 on every command and geometry row still leaves all three conflicts, with deficits above .0036 m/s. Independent HiGHS feasibility solves also find both reconstructed and actual-stop matrices infeasible. This corroborates their native PRIMAL_INFEASIBLE outcomes; it does not attribute them to solver timing or conditioning.

The normalized-margin LP is a diagnostic. Its candidate violates original command-jerk row8 by **103.2693874 rad/s³**, so it is not executable and is not a feasible fallback. A negative normalized common margin does not authorize command or geometry relaxation.

## Replay and actual stop evidence

The frozen replay driver restores the initial public-model state and applies only the recorded accepted targets once per 4 ms interval. It then steps the plant and compares q/v before and after each physical substep. Recorded physical states are comparison references, not values injected into the replay plant or a future predictor.

The independent audit aligns every replay record to its original tick/substep/time: all 1,708 align exactly, and each of the six logged difference fields—q_before, v_before, q_post, v_post, target and time—is strictly zero. The final reconstructed q/v/target/command histories also match the original final row exactly. **Evidence limit:** the replay exports per-record maximum errors rather than all actual physical vectors. This reviewer independently checked those exported comparisons, original state continuity, source identity and the comparison code; it did not execute another physical replay or claim a second independently regenerated trajectory.

The actual stop has one attempted cycle, native PRIMAL_INFEASIBLE, age .001375708 s below the unchanged 50 ms guard, and **zero accepted stop commands**. `stop_raw.csv` contains only its header. The simulation ends at the unchanged3.416 s with physical speed .0345103207 rad/s and last command speed .0433971045 rad/s. The outcome is `NO_FEASIBLE_STOP_NO_COMMAND_SIMULATION_TERMINATED`, with `completed_stop=false`. This is rejection/termination evidence, not a successfully executed stop, safe hold or hardware emergency stop.

The replay uses the same `stoppingProblem`, `constrainPreviewCommand`, geometry dampers, native-SOLVED/original-row gate, both measured/accepted endpoint subdivision guards, current observation age guard and executed-monitor limits as the shared fallback block. Since the first QP is infeasible, downstream nonlinear checks and physical stop monitoring are not exercised on any new stop motion. The progress-state fallback is outside this joint-only fixture's scope.

## Physical velocity versus commanded velocity barrier semantics

For signed distance d(q), the instantaneous physical derivative is `grad(d)^T v_measured`. The implemented kinematic damper applies `grad(d)^T z_command >= -η(d-d_safe)`, with η=2/s. Gradient coefficients are m/rad, so these products and bounds are m/s. At the final state:

| Cover | Lower bound [m/s] | Gradient × physical velocity [m/s] | Gradient × last accepted velocity [m/s] |
|---|---:|---:|---:|
| 37 | -.019226404 | -.002694311 | -.017800911 |
| 38 | -.015978488 | -.000488657 | -.015513430 |
| 39 | -.015640956 | -.000049053 | -.015074185 |

Both instantaneous physical velocity and the **previous** accepted command satisfy these rows. The admitted **next** velocity interval forced by accepted acceleration/jerk history cannot satisfy them. Thus the capture is a forward command-history/geometry conflict while current clearance and instantaneous physical derivatives remain safe in the recorded checks. **Instantaneous gradient slack does not prove that subsequent accepted targets or the physical trajectory can stop.** No physical continuation after simulation termination was executed or certified. Command velocity is not exactly the physical distance derivative under the lagging position servo. This distinction neither invalidates the conservative guard nor establishes a universal barrier guarantee; relaxing it is not recommended. The corrected predictive contract must address physical dynamics, command history and future feasible stopping before claiming intervention/viability.

For future prospective expanded model validation, a previously accepted-target prefix such as v19/moving-stop can be a predefined, hashed input sequence after its permitted scene/history scope is checked. Freeze that input and the new protocol before collecting fresh physical output. Previously inspected physical output cannot be relabeled fresh independent validation, and past replay states must never become future prediction inputs. Meaningful main-controller progress, executed 10 mm accuracy, stop behavior, timing and independent Phase 5 acceptance remain pending.
