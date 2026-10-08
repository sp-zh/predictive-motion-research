# Root predeclaration: physical2ms step derivatives

Scope: the frozen public C++ v2 physical transition only, before augmented
chain rules, main-controller integration or new plant execution. Last complete
component backup f381ba096ba25dd6914d338406df055c58dd5ded is remotely verified.
No derivative numerical tests have run in this root predeclaration.

The independent read-only math review confirms full M(q), full nonlinear
bias n(q,v), nested control/actuator/joint-force clamps and constant implicit
D=passive-biasv. With tau=actuator-passive*v-n, W=M^-1,H=W+diagR,
ell=W*tau+B*v, K=M+.002diagD, f the box optimum, a=K^-1(tau+f),
v+=v+.002a and q+=q+.002v+. On a fixed strict friction branch, bound df=0
and free df=-H_FF^-1(dH*f+dell)_F; dW=-W*dM*W and
dell=dW*tau+W*dtau+B*dv. Then da=K^-1(dtau+df-dM*a).
Derivatives must follow the forward solver's symmetrization convention and
retain original-H KKT validation. Constant parsed armature contributes once
to M and has zero configuration derivative.

Pinocchio RNEA derivatives at acceleration0 can provide full n_q/n_v.
Differences in dtau_dq at constant nominal accelerations x=W*(tau+f) and a
versus acceleration0 provide dM*x and dM*a contractions. These directions
are held constant inside the primitive derivative evaluation; their state
sensitivities are accounted for by the surrounding differential equations.
The installed SDK implementation and armature contract must be checked before
claiming this construction validated.

Classical derivatives require declared strict branch margins: free friction
has positive lower/upper force slack, lower bound has positive original gradient,
upper bound negative gradient. eta0 is a fixed equality, df=0, without a gradient
sign condition. Exact-bound zero-gradient and any control/force clip threshold
cannot be called unique-Jacobian points from labels or aggregate clip counts.
Use explicit unsupported status or declared one-sided/selected-face derivatives
labelled NONSMOOTH. Record each nested clip layer and branch/margin. Check finite
intermediates, factorization, condition estimates, scaled solve residuals and
all14x21 Jacobian entries; forward finite/LLT success alone is insufficient.

Root's prospective independent finite differences use all21(q7,v7,C7) columns
at both fixed epsilon1e-6 and3e-7 in each column's SI units. Report both results,
without selecting the better epsilon; each perturbation must preserve the
same strict branch and physical limit-free support. Threshold fixtures use
separate signed differences and explicit derivative-support semantics, not
an across-switch central difference claimed as a classical Jacobian.

Useful model-derived synthetic fixtures, declared before tests, are: all-free
f=0,g=0,v=0,tau=0; and a mixed friction force f=(-eta0,+eta1,.2eta2,0,0,0,0)
with original gradient g=(+.1,-.1,0,0,0,0,0). At a fixed known valid q, derive
ell=-H*f+g and tau=M*ell (v=0), then solve the public affine actuator equation
for C. These use current public M/bias/parameters and preset mathematical
forces, not fitted plant observations. They must be checked for declared clip
and joint support before use. Existing seen-state fixtures, strict force clips,
weak-active force thresholds and malformed/overflow cases remain separate
predeclared scopes. No successful physical task, timing or Phase5 acceptance
follows from local derivative checks.
