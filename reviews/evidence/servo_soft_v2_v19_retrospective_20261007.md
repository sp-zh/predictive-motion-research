# Retrospective soft-v2 forecast on observed v19-full

Scope: fixed-model retrospective conditional forecast, not fresh holdout, model fit, physical plant execution, domain enlargement or controller acceptance. No production predictor was called. Future q/v never initialize the model inside a window; only the initial preceding measured endpoint and subsequent accepted targets are used.

Model SHA `984ee85d086aeba7da8260a20b21b301e23dfd2c698a6c61ace0ff956bbec1bb`; raw SHA `113a5a1c82e97d6a624656b78fc6383363a76bccf8cc149406071fc57216ee2a`; oracle source SHA `05030fdeecd7342203f0fccab3d1f5e57d42bf5c4026082f7298fa7660c195cc`. Original domain and coefficients are unchanged. Warmup, path, stopping and crossing windows are all retained. Tick0 is unscorable because the first pre-step physical velocity is absent from this raw schema; every remaining complete4ms-boundary window is scored.

| Horizon | All scored windows | Max q error [rad] | Max v error [rad/s] | Actual-domain-bad windows | Forecast-domain-bad windows |
|---|---:|---:|---:|---:|---:|
| 0.002s | 900 | 5.054480e-06 | 2.527240e-03 | 388 | 388 |
| 0.004s | 900 | 9.429715e-06 | 2.187617e-03 | 388 | 388 |
| 0.040s | 891 | 1.920197e-05 | 5.383537e-04 | 388 | 388 |
| 0.800s | 701 | 2.652911e-05 | 3.167424e-04 | 388 | 388 |

The main path lasts0.556s, so no0.8s path-only window exists. Every0.8s path-start window necessarily includes stopping. The JSON retains each complete window, its phase sequence, signed joint endpoint errors and all domain counts; no stopping/out-of-domain window is discarded. Fully in-domain subset metrics are retrospective descriptions only, not a new accuracy gate.

Any forecast initialized or propagated outside the declared q/v/target-minus-q box is unvalidated numerical stress evidence. Passing a box is also not proof of uniform box accuracy. These observations do not authorize widening bounds, selecting coefficients on this already seen trace, or treating old physical output as prospective validation.

Domain counts distinguish raw rows from overlapping window/substep evaluations. Both pre/post states are checked. Source startup identity is fixed and source/model/raw bytes are checked unchanged before publication. Only the independent developer may collect prospective validation or integrate the C++ contract; this diagnostic does not close CTRL-001 or Phase5.
