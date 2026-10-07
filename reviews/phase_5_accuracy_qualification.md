# Phase5 motion accuracy and independent review qualification

The unchanged v14 motion prefix contains195 predictive commits /390 plant
substeps. Actual progress advances to s=0.06029618753193305, r=0.006045132810726585.
Motion does not imply Cartesian accuracy or model/plant trajectory identity.
At4ms endpoints max physical-vs-accepted command velocity discrepancy is
0.0037852902935823687rad/s; requested model q
vs measured plant q differs by up to
7.3362029535672946e-06rad. The latter is a
one-step requested model prediction, not the accepted persistent command target
or a measured whole-horizon model error. Maximum accepted speed is
0.018099972694195197rad/s.

Measured Euclidean TCP position error reaches
0.012076000088711406m. The component's declared10mm
position envelope is therefore violated at
138 executed substeps.
Rotation error is separately reported, max0.0054843757809423495rad;
no new angular acceptance threshold is invented. The100micrometre local-model
consistency tolerance is not a plant tracking guarantee. Accuracy tuning remains
development work; held-out seeds and final research seeds have not been used.
The failed primary and unsafe old fallback remain negative evidence.

Root's independent fixed-cone consumer reports5 analytic and1000 random states,
955 feasible/45 rejected, no boundary ambiguity, max all-K oracle bound error
6.4948046940571658e-15. It independently confirms only core speed continuation.
The full moving-stop component replay is now available separately in
reviews/phase_5_moving_stop_executor_review.md and
results/phase5/development/moving-stop-v1:1390 original substeps reproduced with
zero q/dq mismatch, followed by233 actual stopping cycles. Root's independent
moving replay acceptance remains pending. These results do not certify generic
position/collision stopping, hardware behavior or online timing.

Root's Cholesky whitening experiment remains negative numerical evidence:
six condensed cases all TIME_LIMIT at1s, with extra preconditioning/setup and
dense fill. The original CSV is copied with SHA in manifest.json. No whitening
change is adopted as a controller performance improvement.
