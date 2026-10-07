# Independent coupled friction-box QP oracle

Verdict: **PASS_NOMINAL_COUPLED_BOX_QP_ALGEBRA_ONLY**. This is an independent small-dimensional mathematical checker using the previously archived public nominal model. It supplies no physical prediction accuracy, domain enlargement, controller integration, stopping guarantee or Phase5 acceptance. No plant state/rollout, fitting, authoritative source modification or Git action occurred.

The [executable oracle](../../scripts/phase5/root_coupled_friction_box_oracle.py) reads the nominal inspection-MJCF seven-axis M and static friction parameters from the root public-design JSON. It reconstructs `R=(1-d)/d*dof_invweight0`, `H=M^-1+diag(R)` and `B=2/(dmax*timeconst)`. The seven friction bounds remain `(1.137,1.137,1.137,1.137,.763,.44,.248)` N·m. H is SPD, eigenvalues `.4057551…14.9630800`. Floating inversion asymmetry is symmetrized for the quadratic cost; original unsymmetrized H is retained and used for final KKT checks.

For each declared synthetic drive `ell`, the oracle enumerates all `3^7=2187` lower/free/upper active sets. Bound coordinates are fixed at ±eta; free coordinates solve

\[
H_{FF}f_F=-\ell_F-H_{FB}f_B.
\]

It checks the original box and `g=Hf+ell`: `g_F=0`, `g_lower>=0`, `g_upper<=0`. Positive definiteness makes the accepted primal solution unique even when multiple active-set descriptions coincide. The explicit algebra check tolerance is `1e-10`; it is not a physical-limit relaxation. Synthetic velocities and corresponding `tau=M*(ell-Bv)` are recorded only to show the drive decomposition; these are not executable actuator commands.

Seven fixed fixtures cover zero drive, full lower/upper saturation, a strict mixed active set, a clipping counterexample and exact lower/upper thresholds. Maximum original KKT residual is `8.881784197001252e-16`, with no box violation.

The clipping counterexample sets unconstrained force to `eta*(2,.2,-.15,.1,-.05,.1,-.1)` and `ell=-H*f_unconstrained`. Coordinatewise clipping puts the first force at `1.137` and leaves the others unchanged. Although box-feasible, it leaves a free-coordinate stationarity residual `2.4830885643067635` rad/s². Its objective exceeds the coupled optimum by `1.0401903638171301`; its largest force error is `.8306899291879629` N·m. Thus an actual nominal-matrix algebra example disproves independent clipping as a coupled box-QP solver.

Within a fixed active set and fixed friction bounds, the exact directional sensitivity is

\[
df_B=0,\qquad df_F=-H_{FF}^{-1}\big[(dH)f+d\ell\big]_F.
\]

Three ell-axis directions and one symmetric H direction were checked by fresh central finite differences (`h=1e-6`), explicitly requiring unchanged active sets and SPD. Maximum error is `1.3881690935635405e-10`. These tests differentiate H and ell algebra; they do not supply the separate state derivatives of M, bias or actuator force required by a future causal transition module.

At a threshold, a bound coordinate can have zero multiplier. The oracle declares a saturated-side derivative and uses a `1e-10` classification tolerance solely for numerical branch labeling. Both threshold fixtures have two valid active-set descriptions but one primal solution. Opposite one-sided ell derivatives differ by `.7693888968152152`; the selected saturated-side derivative matches its appropriate one-sided limit. A unique ordinary derivative is not claimed. A future implementation must declare its own compatible convention rather than interpret central differences across a branch change as a Jacobian.

Detailed arrays, fixtures, KKT checks and sensitivities are in [JSON](coupled_friction_box_root_oracle_20261007.json). Unique output directory `results/phase5-reference/root-coupled-friction-box-oracle-20261007-v1` contains source/input snapshots, `oracle.json` and a READY manifest. Source startup bytes are fixed and rechecked before publication; final source SHA is `1ff0291f990361968eadfde18d3732e87d08d0091b6c11603fab42ae995d6103`. This oracle remains independent of the developer's future prototype and of any validation-output-based model selection.

The inspected [force comparison image](../../figures/phase5/phase5_coupled_friction_box_oracle.png) displays this same counterexample and frozen box limits; no new solve or data scan was performed. Synthetic/public-model/nonphysical scope and original KKT residuals are visible. [Figure provenance](../../figures/phase5/phase5_coupled_friction_box_oracle.json) retains M/R/H, drive, both force vectors and source/input/PNG hashes. The standard Matplotlib renderer is [plot_coupled_friction_box_oracle.py](../../scripts/phase5/plot_coupled_friction_box_oracle.py), fixed source SHA `1ec3a67ed0891132fa84534c6e66a88c0c692057709cc8ef5fe894a41b21046c`. PNG SHA is `42b967e2a8e1f397d433bb476e690f0a86fabe05cc72f097946a9dd251bbd1d1`. It was generated separately under Dell `/home/codextransfer/clean-audits/coupled-friction-box-plot-20261007-v1`; a byte-verified Mac copy and its separate READY manifest are retained at `results/phase5-reference/root-coupled-friction-box-plot-20261007-v1`. The earlier mathematics READY payload remains unchanged.
