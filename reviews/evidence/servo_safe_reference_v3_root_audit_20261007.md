# Independent safe-reference v3 audit

**Recorded QP/history checks pass; expanded model accuracy fails; Phase5 remains pending.**

Every actual exported A/l/u row is multiplied by its own exported candidate using an independent original-SI calculation. All 2,002 solves have native SOLVED and API success; all 2,001 applied histories match recorded commands and retain discrete signed speed recovery. H/g are not directly captured for every solve.

| Horizon | Windows | Maximum q error [rad] | Maximum v error [rad/s] | Original gate | Hold-only windows |
|---|---:|---:|---:|---|---:|
| 0.002s | 2001 | 5.39282315e-07 | 2.69641158e-04 | FAIL | 1572 |
| 0.004s | 2001 | 1.16250506e-06 | 3.11611373e-04 | FAIL | 1572 |
| 0.04s | 1992 | 1.62197430e-05 | 5.29564259e-04 | PASS | 1563 |
| 0.8s | 1802 | 3.82276886e-05 | 4.55474826e-04 | PASS | 1373 |

Maximum metric discrepancy against the producer: 8.674e-19. Maximum actual SI-row violation: 1.63993263e-10; original acceptance remains 1e-7.

The scalar-box force minimizer is reconstructed independently from the frozen parameters. Each forecast initializes once from its starting measured state; later physical states serve only as endpoint comparisons. Every complete active 4ms-boundary window is retained. Short gates remain q=1e-6/v=1e-4; long gates remain q=1e-4/v=1e-3.

The trace includes 1.712s of reference movement/braking and a long hold. Its final new stop starts already near rest. This is a recorded fixture result, not a new moving-stop challenge, domain-wide proof, main MPC pass, or timing acceptance. The model and declared local domain remain unchanged.
