# Mathematical conventions and planned predictive formulation

Status: pose/Jacobian conventions and basic IK have passed component validation; redundancy has passed Phase 3 component review. Reactive constraints passed the stated Phase 4 component envelope; the explicit predictive formulation is being implemented and still requires Phase 5 validation before research claims.

## Frames and pose residual

Let T(q) = world_T_TCP and T_d(s) = world_T_desired. Define E = T(q)^(-1) T_d(s), and e = log6(E) in the current TCP body frame. Pinocchio vectors are [linear; angular]; quaternion serialization is documented per interface, with ROS xyzw and Eigen constructor wxyz explicitly converted.

Use J_LOCAL from the TCP frame; a WORLD Jacobian is not interchangeable. For q perturbations, the residual differential is A_q = -Jlog6(E^(-1)) J_LOCAL, consistent with [Pinocchio's official IK example](https://raw.githubusercontent.com/stack-of-tasks/pinocchio/v4.1.0/examples/inverse-kinematics.py). For right/body desired-path derivative nu_d = (T_d^(-1) dT_d/ds)^vee, A_s = Jlog6(E) nu_d. Both expressions must be checked by central finite differences, including rotated frames and tool offsets.

The implemented differential IK solves (-A_q) dq = K e + Jlog6(E) nu_desired, with desired twist expressed in the desired body's right tangent. This uses the actual residual derivative away from zero; e is not a Euclidean pose subtraction. Scale both sides consistently.

## Joint-margin and singularity quantities

For seven arm coordinates, range r_i = q_max_i - q_min_i must be positive. H_joint = sum_i ((q_i-q_mid_i)/r_i)^2 and gradient_i = 2(q_i-q_mid_i)/r_i^2. Report physical radian margins and normalized margins separately.

Compute singular values by SVD. Report sigma_min, condition number (infinite when rank-deficient), and the product/log product of singular values as manipulability; do not compute an unstable determinant and hide a negative result. Raw mixed translation/rotation singular values are unit-dependent. Implemented component experiments scale angular rows by the declared characteristic length L=0.3 m/rad: [linear; L*angular]. The same scale applies to task twists/residuals. Report L and unscaled indicators explicitly; neither weighted singular values nor damping are physical tracking errors.

The exact Moore–Penrose projector P = I-J^dagger J has negligible JP within tolerance. A damped projector is not an exact null-space projector and can introduce task leakage; record this distinction.

The implementation evaluates P=I-V_r V_r^T from retained right singular vectors, with relative numerical rank cutoff 1e-10. Truncating nonzero singular values permits leakage of cutoff order. Secondary joint motion is -k*P*grad H; its instantaneous joint-objective derivative is -k*||P*grad H||^2, but individual margins and finite-step tracking need separate evaluation. Sigma_min ascent and regularized log-volume ascent use declared finite differences; repeated-minimum/rank-loss flags qualify differentiability. Regularized volume is sum(log(hypot(sigma_i,epsilon))), not a guarantee of increasing sigma_min. Executed saturation/plant dynamics can disturb the primary task despite negligible raw J*P*z.

## Discrete predictive state

x = [q(7), v(7), s(1), r(1)] has dimension 16; u = [a(7), b(1)] has dimension 8. At prediction interval h:

q_next = q + h v + 0.5 h^2 a; v_next = v + h a.

s_next = s + h r + 0.5 h^2 b; r_next = r + h b.

Initial h=0.04 s, N=20. Command feedback interval is separately 0.004 s. Warm-start shift/reconstruction accounts for elapsed control time, not a fictitious one-prediction-cell jump each cycle. Jerk is (a_k-a_(k-1))/h on the preview grid; executed jerk is evaluated at the actual command/plant interval. The first jerk bound uses the previous applied acceleration and elapsed command time.

## Sequential convexification

At each nominal rollout, linearize body pose residual in (q,s), collision distances in q and optional singularity penalty in q. Assemble a coupled horizon QP with quadratic tracking, velocity/acceleration/jerk regularization, posture terms and progress reward. State dynamics are affine. Nonlinear collision/singularity terms are local approximations; nonlinear candidate evaluation and trust regions are required.

Constraints include joint position/velocity/acceleration, jerk, 0<=s<=1, r>=0, configurable progress acceleration, distances >= safe margin and configured trust regions. Collision linearization uses d(q_bar)+grad_d^T(q-q_bar). A feasible linearization is not proof of global collision avoidance. Intersample constraints need tighter margins or explicit subdivision evaluation.

Expose SCP maximum iterations, termination criteria, trust-region policy, OSQP tolerances/warm-start reset and timeout budget. Record true nonlinear violation after each accepted update. Terminal speed/stopping policy must avoid overshooting s=1; endpoint zero-speed handling must not divide by r.

The reactive QP uses the same limits and scene, with one-control-step position bounds and collision velocity damping. Prediction-disabled ablation must preserve solver weights/safety monitor as far as mathematically possible; fixed-speed ablation fixes progress rather than removing tracking information.

## Safety and evaluation

Every method shares the plant command adapter and independent constraint monitor. Log requested, accepted and executed commands separately. A solver failure triggers a configured deceleration/reactive fallback only if stopping/feasibility checks allow it; otherwise record an explicit failed run. Simulation fallback is not a hardware safety certification.
