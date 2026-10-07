# Benchmark definitions and measurement boundaries

Status: scenario-family specification. No successful trials or method rankings exist yet. Detailed frozen geometry/path parameters are produced and validated during baseline development.

| Family | Required mechanism | Primary measures |
|---|---|---|
| Singularity funnel | feasible initial state with poor-conditioning future path; redundancy can change risk | scaled/raw sigma_min, condition, tracking, joint speed, early posture change |
| Joint-limit trap | locally feasible redundancy choices diverge into different future feasibility | physical/normalized margin, intervention lead time, completion, slowdown |
| Constrained inspection | long-tool TCP pose path, fixture near elbow/wrist, self/environment pairs | independent clearance, actual contacts, pose error, progress speed |
| High-speed paths | circle, helix, figure-eight, spline and high-curvature path | pose error, executed derivatives/limits, completion and cycle tails |
| Online path change | changes delivered at specified simulated time with matched available information | latency, overshoot, jerk, fallback and feasibility |
| Combined stress | frozen mixture after independent families work | failure mode breakdown and all relevant measures |
| Moving obstacle extension | declared perfect preview before uncertain prediction | intervention lead time and executed clearance; outside first mandatory result |

Each scenario manifest identifies model/base/TCP transforms, obstacle geometry, allowed collision pairs, initial q/dq, path/orientation interpolation, tool parameter hash, start/terminal speed, safe clearance, sample schedule, duration cap and success thresholds. Feasibility probes are retained, including intentionally infeasible scenarios for failure handling.

All methods receive equivalent robot limits and geometry. Pair exclusions are explicit and reviewed; disabling robot self-collision or ignoring tool collision would invalidate inspection results. Joint acceleration/jerk values lacking manufacturer provenance are labeled experimental bounds.

Future-risk intervention is measured relative to a declared hazard threshold crossing predicted by a nominal fixed-speed rollout. Log prediction timestamp, preview time-to-hazard, controller action and executed outcome. Current-state threshold crossings alone cannot substantiate future constraint prediction.

Cross-robot comparison changes physical models/limits/TCP and task reach scaling explicitly. Universal controller tuning stays fixed when practical; any change is logged and analyzed. FR3-vs-iiwa performance is not pooled into one ranking without per-robot results.
