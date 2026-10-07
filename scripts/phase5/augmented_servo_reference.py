#!/usr/bin/env python3
"""Independent affine command/physical servo oracle; synthetic fixtures, no FR3 validity."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def zero(n, m):
    return [[0.0] * m for _ in range(n)]


def eye(n):
    a = zero(n, n)
    for i in range(n):
        a[i][i] = 1.0
    return a


def mm(a, b):
    return [[sum(x * y for x, y in zip(row, col)) for col in zip(*b)] for row in a]


def mv(a, x):
    return [sum(u * v for u, v in zip(row, x)) for row in a]


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def madd(a, b):
    return [add(x, y) for x, y in zip(a, b)]


def err(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


def flat(a):
    return [x for row in a for x in row]


def split(h, dt):
    """Each cell starts a command-update grid; remainder uses its own δ update."""
    if not (h > 0 and dt > 0):
        raise ValueError("positive durations required")
    m = math.floor(h / dt)
    remainder = h - m * dt
    if abs(remainder - dt) < 1e-14:
        m, remainder = m + 1, 0.0
    if abs(remainder) < 1e-14:
        remainder = 0.0
    return [dt] * m + ([remainder] if remainder else [])


def physical_matrices(gamma, gravity, delta):
    # Exact critically damped synthetic servo qddot=γ²(c-q)-2γv+g.
    # Nonzero affine offset g is declared, not fitted to robot data.
    n = len(gamma)
    p, q, d = zero(2 * n, 2 * n), zero(2 * n, n), [0.0] * (2 * n)
    for j, (g, force) in enumerate(zip(gamma, gravity)):
        e = math.exp(-g * delta)
        p[j][j], p[j][n+j] = e * (1 + g * delta), e * delta
        p[n+j][j], p[n+j][n+j] = -e * g * g * delta, e * (1 - g * delta)
        q[j][j], q[n+j][j] = 1 - p[j][j], -p[n+j][j]
        d[j], d[n+j] = q[j][j] * force / (g*g), q[n+j][j] * force / (g*g)
    return p, q, d


def microstep(gamma, gravity, delta):
    # z=[physical q,v, accepted target c, accepted velocity w]; u=α.
    n = len(gamma)
    p, q, d = physical_matrices(gamma, gravity, delta)
    f, b, o = zero(4*n, 4*n), zero(4*n, n), d + [0.0] * (2*n)
    for i in range(2*n):
        f[i][:2*n] = p[i]
        for j in range(n):
            f[i][2*n+j] = q[i][j]
            f[i][3*n+j] = delta * q[i][j]
            b[i][j] = delta**2 * q[i][j]
    for j in range(n):
        f[2*n+j][2*n+j], f[2*n+j][3*n+j] = 1, delta
        f[3*n+j][3*n+j] = 1
        b[2*n+j][j], b[3*n+j][j] = delta**2, delta
    return f, b, o


def compose(gamma, gravity, h, dt):
    n = len(gamma)
    f, b, d = eye(4*n), zero(4*n, n), [0.0] * (4*n)
    for delta in split(h, dt):
        p, q, offset = microstep(gamma, gravity, delta)
        f, b, d = mm(p, f), madd(mm(p, b), q), add(mv(p, d), offset)
    return f, b, d


def direct(initial, controls, mesh, dt, gamma, gravity, previous_alpha, previous_physical_acc):
    # Independent scalar closed form, avoiding transition matrix multiplication.
    n = len(gamma)
    z = initial[:]
    states, history = [z[:]], []
    old_alpha, old_acc = previous_alpha[:], previous_physical_acc[:]
    time = 0.0
    for k, h in enumerate(mesh):
        alpha = controls[k*n:(k+1)*n]
        for delta in split(h, dt):
            old_v, old_w = z[n:2*n], z[3*n:4*n]
            for j, (g, force) in enumerate(zip(gamma, gravity)):
                z[3*n+j] += delta * alpha[j]
                z[2*n+j] += delta * z[3*n+j]
                equilibrium = z[2*n+j] + force / (g*g)
                displacement, velocity = z[j] - equilibrium, z[n+j]
                e = math.exp(-g * delta)
                z[j] = equilibrium + e*((1+g*delta)*displacement + delta*velocity)
                z[n+j] = e*(-g*g*delta*displacement + (1-g*delta)*velocity)
            command_acc = [(z[3*n+j]-old_w[j])/delta for j in range(n)]
            command_jerk = [(command_acc[j]-old_alpha[j])/delta for j in range(n)]
            physical_acc = [(z[n+j]-old_v[j])/delta for j in range(n)]
            physical_jerk = [(physical_acc[j]-old_acc[j])/delta for j in range(n)]
            time += delta
            history.append({"cell": k, "time_s": time, "delta_s": delta,
                            "physical_q": z[:n], "physical_v": z[n:2*n],
                            "accepted_target_c": z[2*n:3*n], "accepted_velocity_w": z[3*n:4*n],
                            "command_acceleration": command_acc, "command_jerk": command_jerk,
                            "physical_mean_acceleration": physical_acc,
                            "physical_mean_jerk": physical_jerk})
            old_alpha, old_acc = command_acc, physical_acc
        states.append(z[:])
    return states, history


def gaussian(a, rhs):
    """Generic pivoted lifted-state elimination, independent of forward recurrence."""
    n, width = len(a), len(rhs[0])
    m = [row[:] + b[:] for row, b in zip(a, rhs)]
    for k in range(n):
        pivot = max(range(k, n), key=lambda i: abs(m[i][k]))
        m[k], m[pivot] = m[pivot], m[k]
        assert abs(m[k][k]) > 1e-15
        factor = m[k][k]
        m[k] = [v/factor for v in m[k]]
        for i in range(k+1, n):
            factor = m[i][k]
            if factor:
                for j in range(k, n+width):
                    m[i][j] -= factor*m[k][j]
    x = zero(n, width)
    for i in range(n-1, -1, -1):
        x[i] = [m[i][n+j] - sum(m[i][k]*x[k][j] for k in range(i+1, n))
                for j in range(width)]
    return x


def audit_case(name, n, mesh):
    dt = .004
    gamma = [7.0 + 2*j for j in range(n)]
    gravity = [.13 - .03*j for j in range(n)]
    initial = ([.03+.02*j for j in range(n)] + [-.012+.003*j for j in range(n)] +
               [.041+.023*j for j in range(n)] + [.008-.004*j for j in range(n)])
    previous_alpha = [.021+.007*j for j in range(n)]
    previous_physical_acc = [-.11+.02*j for j in range(n)]
    controls = [(-1 if k % 2 else 1)*(.05+.013*k+.009*j)
                for k in range(len(mesh)) for j in range(n)]
    nx, nu = 4*n, n*len(mesh)
    transitions = [compose(gamma, gravity, h, dt) for h in mesh]
    offsets, sensitivities, initial_sens = [initial[:]], [zero(nx, nu)], [eye(nx)]
    for k, (f, b, d) in enumerate(transitions):
        offsets.append(add(mv(f, offsets[-1]), d))
        current = mm(f, sensitivities[-1])
        for i in range(nx):
            for j in range(n):
                current[i][k*n+j] += b[i][j]
        sensitivities.append(current)
        initial_sens.append(mm(f, initial_sens[-1]))
    states, history = direct(initial, controls, mesh, dt, gamma, gravity,
                             previous_alpha, previous_physical_acc)
    affine_error = max(err(z, add(o, mv(s, controls)))
                       for z, o, s in zip(states, offsets, sensitivities))
    hfd = 1e-5
    control_sensitivity_error = initial_sensitivity_error = 0.0
    for j in range(nu):
        up, um = controls[:], controls[:]
        up[j] += hfd
        um[j] -= hfd
        plus = direct(initial, up, mesh, dt, gamma, gravity, previous_alpha, previous_physical_acc)[0]
        minus = direct(initial, um, mesh, dt, gamma, gravity, previous_alpha, previous_physical_acc)[0]
        for k in range(len(states)):
            control_sensitivity_error = max(control_sensitivity_error,
                max(abs((plus[k][i]-minus[k][i])/(2*hfd)-sensitivities[k][i][j]) for i in range(nx)))
    for j in range(nx):
        zp, zm = initial[:], initial[:]
        zp[j] += hfd
        zm[j] -= hfd
        plus = direct(zp, controls, mesh, dt, gamma, gravity, previous_alpha, previous_physical_acc)[0]
        minus = direct(zm, controls, mesh, dt, gamma, gravity, previous_alpha, previous_physical_acc)[0]
        for k in range(len(states)):
            initial_sensitivity_error = max(initial_sensitivity_error,
                max(abs((plus[k][i]-minus[k][i])/(2*hfd)-initial_sens[k][i][j]) for i in range(nx)))
    lifted_n = nx*len(states)
    l, rhs = zero(lifted_n, lifted_n), zero(lifted_n, nu+1)
    for k in range(len(states)):
        for i in range(nx):
            l[k*nx+i][k*nx+i] = 1
            if k == 0:
                rhs[i][-1] = initial[i]
            else:
                f, b, d = transitions[k-1]
                for j in range(nx):
                    l[k*nx+i][(k-1)*nx+j] = -f[i][j]
                for j in range(n):
                    rhs[k*nx+i][(k-1)*n+j] = b[i][j]
                rhs[k*nx+i][-1] = d[i]
    eliminated = gaussian(l, rhs)
    condensed = [srow+[offset] for s, o in zip(sensitivities, offsets)
                 for srow, offset in zip(s, o)]
    elimination_error = err(flat(eliminated), flat(condensed))
    state_stack = flat(states)
    rhs_value = mv(rhs, controls+[1.0])
    lifted_residual = err(mv(l, state_stack), rhs_value)
    command_acc_error = max(abs(row["command_acceleration"][j]-controls[row["cell"]*n+j])
                            for row in history for j in range(n))
    target_formula_error = 0.0
    for k, h in enumerate(mesh):
        moment = .5*(h*h + sum(d*d for d in split(h, dt)))
        for j in range(n):
            predicted = states[k][2*n+j]+h*states[k][3*n+j]+moment*controls[k*n+j]
            target_formula_error = max(target_formula_error, abs(predicted-states[k+1][2*n+j]))
    # A synthetic quadratic tracking objective verifies full-state substitution,
    # including nonzero offsets. Target intentionally differs from initial state.
    desired = [.01*(j+1) for j in range(nx)]
    weights = [1+.1*j for j in range(nx)]
    cost_direct = .5*sum(w*(x-t)**2 for z in states for x,t,w in zip(z,desired,weights))
    cost_direct += .005*sum(u*u for u in controls)
    hessian, gradient, constant = zero(nu, nu), [0.0]*nu, 0.0
    for o, s in zip(offsets, sensitivities):
        for i in range(nx):
            delta = o[i]-desired[i]
            constant += .5*weights[i]*delta*delta
            for a in range(nu):
                gradient[a] += weights[i]*s[i][a]*delta
                for b in range(nu):
                    hessian[a][b] += weights[i]*s[i][a]*s[i][b]
    for j in range(nu):
        hessian[j][j] += .01
    cost_condensed = .5*sum(u*v for u,v in zip(controls,mv(hessian,controls)))
    cost_condensed += sum(u*g for u,g in zip(controls,gradient)) + constant
    cost_error = abs(cost_direct-cost_condensed)
    assert affine_error < 1e-12 and elimination_error < 1e-12 and lifted_residual < 1e-12
    assert control_sensitivity_error < 1e-9 and initial_sensitivity_error < 1e-9
    assert command_acc_error < 1e-12 and target_formula_error < 1e-12 and cost_error < 1e-12
    return {"name":name,"n":n,"mesh_s":mesh,"microsteps_s":[split(h,dt) for h in mesh],
            "gamma_per_s":gamma,"gravity_offset":gravity,"initial":initial,"controls":controls,
            "previous_command_acceleration":previous_alpha,"previous_physical_acceleration":previous_physical_acc,
            "states":states,"history":history,"transitions":transitions,
            "condensed_offsets":offsets,"condensed_control_maps":sensitivities,
            "initial_state_maps":initial_sens,"lifted_dynamics_matrix":l,"lifted_rhs_affine":rhs,
            "condensed_quadratic":{"hessian":hessian,"gradient":gradient,"constant":constant,
                                   "direct_objective":cost_direct,"condensed_objective":cost_condensed},
            "checks":{"direct_vs_affine":affine_error,"control_sensitivity_fd":control_sensitivity_error,
                      "initial_sensitivity_fd":initial_sensitivity_error,"lifted_elimination":elimination_error,
                      "lifted_dynamics_residual":lifted_residual,"command_acceleration_identity":command_acc_error,
                      "endpoint_target_moment":target_formula_error,"objective_substitution":cost_error}}


def stopping_counterexample():
    gamma, gravity, c = 10.0, .13, .04
    qeq = c + gravity/gamma**2
    initial = [qeq+.001, 0.0, c, 0.0]
    mesh = [.004]*400
    states, history = direct(initial, [0.0]*400, mesh, .004, [gamma], [gravity], [0.0], [0.0])
    first = history[0]["physical_v"][0]
    max_speed = max(abs(z[1]) for z in states)
    tolerance = 1e-4  # Existing physical-stop observation threshold, fixture scope.
    settling = next(row["time_s"] for i,row in enumerate(history)
                    if all(abs(r["physical_v"][0]) <= tolerance for r in history[i:]))
    assert abs(first) > tolerance and max_speed > tolerance
    return {"scope":"Synthetic critically damped hold with terminal v=w=0 but nonzero equilibrium residual",
            "initial":initial,"gamma_per_s":gamma,"gravity_offset":gravity,
            "first_4ms_velocity":first,"peak_hold_velocity":max_speed,
            "declared_physical_stop_tolerance_rad_s":tolerance,"settles_below_tolerance_s":settling,
            "initial_equilibrium_position_error":.001,
            "warning":"Finite sampled settling check only; no robot, collision or universal invariant-set claim"}


def terminal_equality_reference():
    gamma, gravity, dt = [7.0], [.13], .004
    initial = [.03, -.012, .041, .008]
    forced_alpha = -initial[3]/dt
    single = direct(initial, [forced_alpha], [dt], dt, gamma, gravity, [.021], [-.11])[0][-1]
    rows = []
    for name, mesh in [("two_microstep_horizon",[dt,dt]),
                       ("twenty_40ms_cells",[.04]*20)]:
        sensitivity = zero(4,len(mesh))
        for k,h in enumerate(mesh):
            f,b,_ = compose(gamma,gravity,h,dt)
            sensitivity = mm(f,sensitivity)
            for i in range(4):
                sensitivity[i][k] += b[i][0]
        physical_v, command_w = sensitivity[1], sensitivity[3]
        aa = sum(x*x for x in physical_v)
        bb = sum(x*x for x in command_w)
        ab = sum(x*y for x,y in zip(physical_v,command_w))
        largest = .5*(aa+bb+math.hypot(aa-bb,2*ab))
        smallest = (aa*bb-ab*ab)/largest
        rows.append({"name":name,"physical_v_row":physical_v,"command_w_row":command_w,
                     "physical_to_command_row_norm_ratio":math.sqrt(aa/bb),
                     "two_velocity_row_condition_number":math.sqrt(largest/smallest)})
    assert abs(single[3]) < 1e-14 and abs(single[1]) > 1e-4
    return {"scope":"Synthetic equality feasibility/scaling examples only; no authoritative QP timing claim",
            "single_microstep_initial":initial,"alpha_for_exact_command_stop":forced_alpha,
            "single_microstep_terminal":single,
            "finding":"With one scalar input exact w_next=0 fixes alpha, leaving physical v_next generally nonzero; exact joint stopping is not automatically feasible.",
            "velocity_sensitivity_rows":rows}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    cases = [audit_case("scalar_uniform",1,[.04,.04,.04]),
             audit_case("scalar_fractional_nonuniform",1,[.007,.041,.023,.04,.009]),
             audit_case("three_joint_fractional_nonuniform",3,[.009,.04,.017,.041,.027])]
    result = {"scope":__doc__,"status":"SYNTHETIC_AFFINE_ORACLE_PASS","command_dt_s":.004,
              "layout":"z=(physical q,v, accepted target c, accepted velocity w); u=command acceleration alpha",
              "fractional_policy":"Each cell starts Δ updates; final fractional δ updates w+=δα,c+=δw_next; requires separately supplied Pδ,Qδ,dδ. This fixture uses exact analytic matrices, never interpolates a 4ms matrix.",
              "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "cases":cases,"stopping_counterexample":stopping_counterexample(),
              "terminal_equality_reference":terminal_equality_reference()}
    (args.output/"oracle.json").write_text(json.dumps(result,indent=2)+"\n")
    compact = {k:v for k,v in result.items() if k != "cases"}
    compact["cases"] = [{k:v for k,v in c.items() if k in ["name","n","mesh_s","checks"]} for c in cases]
    (args.output/"summary.json").write_text(json.dumps(compact,indent=2)+"\n")
    print(json.dumps(compact,indent=2))


if __name__ == "__main__":
    main()
