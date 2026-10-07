# Independent root review: scalar finite-output C++ v3

Verdict: **PASS_ISOLATED_SCALAR_FINITE_OUTPUT_V3**. The reproduced v2 generic-API nonfinite-output defect is fixed. This is a finite-arithmetic rejection change to the existing scalar model; coefficients, local domain, transition equations and branch conventions are unchanged. Prediction accuracy failures remain retained. This does not establish coupled dynamics, physical prediction accuracy, stopping safety, CTRL001 closure or Phase5 acceptance.

The [independent audit](../../scripts/phase5/audit_causal_servo_finite_v3.py) first checked every producer frozen source/binary/input identity against the imported checkpoint. All imported `tools/phase5_causal_servo_v3` bytes equal their Mac working copies. Header SHA is `87d1b7599cd5fd870017028fa2ffa6535ec08de7cfffb698e0ab5d2fb2cc2e6b`; original root branch packet remains SHA `8f09f79a23a6be6f3785dc76612c9a1f43b90b038e1fb248d616116dcb1276f7`, tied to fixed oracle source `c63f524d2002323ca635574addcf8ef04a498154ea171ac5a58deda088853710` and model `984ee85d086aeba7da8260a20b21b301e23dfd2c698a6c61ace0ff956bbec1bb`.

A fresh isolated Linux CMake Release build compiled all four original targets successfully. Exported compile commands independently confirm `-Wall -Wextra -Werror`. Build logs, original inputs, fresh output, binary hashes and failed horizon partial-output records are preserved under `/home/codextransfer/clean-audits/causal-servo-finite-v3-independent-20261007-v1`; numerical records are imported into the unique Mac output directory.

The source adds finite checks to derived target error, command/progress state, smooth/drive force, denominator, gain, physical derivatives/state, physical Jacobian/affine defect, cycle and cell A/B/defect composition, and every returned transition. The CLI additionally checks horizon offsets/control/initial sensitivities and numerical serialization. Checks reject arithmetic failures rather than changing model parameters or domain boundaries.

Actual fresh results:

- The identical root v2 counterexample still passes parameter validation but now throws before returning a transition.
- All seven existing cycle/cell overflow regressions throw `std::overflow_error` at the expected stage. The deliberately finite one-cycle positive case passes; its two-cycle composition fails at cell A propagation.
- Both existing horizon fixtures exit with code 3: `nonfinite horizon control sensitivity product` and `nonfinite horizon initial sensitivity`. Partial JSON is retained as failure evidence and is not a valid successful reference/output packet.
- All 78 existing malformed public-entry checks and ten domain/mesh rejections pass.
- Eight fixed branch cases still match state/A/B/defect and both 2 ms branch vectors, including ±threshold saturated→interior transitions; maximum numerical difference is `5.825201432330118e-15` against predeclared `5e-12`.
- Both nonuniform nominal horizon cases match all states, cell matrices/defects, condensed offsets, control sensitivities and initial sensitivities; maximum difference is `2.2709265024012382e-14`. Fresh numeric results match producer's recorded v3 nominal output exactly.

No new test design, parameter sweep, fitting or plant run was introduced. At exact clip thresholds the saturated-side Jacobian remains a declared nonunique-derivative convention. Rejecting nonfinite arithmetic does not guarantee conditioning, useful sensitivity magnitude, real-time computation or physical model accuracy. Command/history/position/geometry guards remain outside this isolated component.

[Detailed JSON](causal_servo_finite_v3_root_review_20261007.json) records the identities, compile commands and rejection/parity results. `results/phase5-reference/root-causal-servo-finite-v3-independent-20261007-v1` has immutable source snapshot, fresh output and READY manifest. Final audit source SHA is `0414b39cbcf83d46e4bb73cce69234b82b991df9451966006a72eff423e7e4a5`. Producer sources, earlier failure records and earlier READY payloads were not modified; root coordinates the milestone backup.
