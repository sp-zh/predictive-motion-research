# Actual task bootstrap V2

Retained actualrepair7 source fixes the V1 bootstrap seam: three durable fsync events per physical substep, explicit returned/joint-read availability, rejection of native BADQPOS/BADQVEL/BADQACC warnings, and actual MuJoCo/URDF TCP/armframe correspondence at1e-8. A failed partial native advancement is retained; command task counters do not advance during bootstrap. The complete21-file source and actual compile/link/driver identities are archived separately. These five files are a source view, not an integrated portable control entry.

The actual1000-step hold/end check passes. Startup acceleration/jerk remain above task limits; no full physical-path, Model/QP/candidate/taskcommit or Phase5 acceptance follows. V1 failures and gaps remain immutable. Source fixes without injected crash/warning fixtures do not prove every failure mode.
