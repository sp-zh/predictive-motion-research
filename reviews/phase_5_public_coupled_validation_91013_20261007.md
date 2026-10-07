# Single seed91013 conditional development validation

Phase5 remains unaccepted. One approved simulation-only run of previously seen curated accepted-reference input; not hardware, unseen waveform, untouched final holdout, task completion, main-MPC or uniform accuracy-domain acceptance. Model, collector, seed, reference, guards and all 256 prospectively frozen dependencies remain unchanged. No fitting or rerun. Root approval binds schema2/protocol/frozen SHA and previously remote-verified checkpoint 3d41fdd5b274ac7931af8f03dbc1ea95c2b19571.

Collector return code 0, wall 11.265209851s; frozen scorer CLI exit 0; gate `PASS_FRESH_CURATED_CONDITIONAL_TRACE_ONLY`. All raw files/stdout/stderr, execution identity, scoring reports/partials/failures and combined scorer tool output are retained. Offline scorer wall time was not directly measured and is not an online-performance result.

Full roster: 2501 control cycles, 5002 physical 2ms substeps; 500 warmup/195 motion/233 recorded-braking/1572 hold/1 shared-stop cycles. 2002 unique tracking/stop attempts, native/API/finite/history/original-row checks pass; one tracking candidate is superseded by stop. Original max SI=1.1662493193398404e-10 <=1e-7; max command age=0.018382032s<=.05. All five consumed sidecar hashes match capture. 1996 full-cycle 4ms deadline misses: this does not establish 250Hz.

Every full 4ms-aligned window starts from measured q/v once and then uses its own predicted states with recorded future accepted targets as conditional inputs. Future actual q/v are endpoint scores only. All warmup/motion/brake/hold/shared-stop windows and crossings are retained, including the dominant hold-only stratum; overlapping windows are not independent trials. Warmup must be finite, complete and failure-free; its accuracy thresholds are descriptive. Active short/long thresholds are unchanged.

| Horizon ms | Active complete windows | Max q error rad | Max v error rad/s | RMS q | RMS v | Failed windows |
|---|---:|---:|---:|---:|---:|---:|
| 2 | 2001 | 8.8817842e-16 | 3.40873163e-15 | 3.63810408e-17 | 1.75856994e-16 | 0 |
| 4 | 2001 | 8.8817842e-16 | 3.76348258e-15 | 5.57839349e-17 | 1.97820715e-16 | 0 |
| 40 | 1992 | 1.77635684e-15 | 6.09528961e-15 | 1.10226609e-16 | 3.94153943e-16 | 0 |
| 800 | 1802 | 1.77635684e-15 | 6.65422915e-15 | 1.52866806e-16 | 7.55786667e-16 | 0 |

Warmup windows: [500, 500, 500, 500]; failures 0. Force-QP max original KKT=2.220446049250313e-15, max iterations=3; recorded repeated prediction branches {'0': 6732293, '-1': 69729, '1': 44979}; clamps {'controls': 0, 'forces': 0}. Near-roundoff agreement on this fixed-parameter trace is evidence for the scoped public baseline, not a general numerical certificate.

Minimum recorded clearance 0.015563429721572567m, maximum physical velocity 0.029926917865789479rad/s, no contacts. Terminal shared stop at tick2500/time10.004s, after long hold; source w/v thresholds satisfied. It is not a moving-state stop challenge. Actual q/v and accepted derivatives, physical derivative guards, SI/history and timing remain distinct quantities. Exact geometry tail-row count/per-solve options and accepted-solve H/g are not directly captured; source hashes/recorded rows/summary do not authenticate unlogged forces or independently reconstruct nonlinear guard checks. The full limitation list remains in the scorer report.

New plots use actual raw/report data and retain the deadline failures. The final-state image uses actual last recorded q/v/target with existing MuJoCo3.3.7 OSMesa and mj_forward only, not new dynamics/control stepping. Geometry is metres, q radians, v rad/s, plotted clearance mm/timing ms; upstream FR3 asset SHA manifest and unchanged renderer/model provenance are recorded. No complete task trajectory exists here, so no task-success video is added. Previous scalar-model/collector failures, v1 scorer false-PASS evidence and Phase4 accepted renders/videos remain intact. Root independently reviews selected model forecasts and the full capture/identity roster, then backs up source/review/figures and two verified archive copies; neither backup nor conditional gate is Phase5 acceptance.
