# Evidence analysis

Python handles offline metrics, statistics and figures. Controllers do not depend on this code. A successful analysis program is not acceptance of the experiment it reads.

`scripts/aggregate_paired_trials.py` reads a declared expected-pair schedule and a trial-summary CSV. It stratifies comparisons by explicit group columns, validates pairing/method identities, rejects duplicate or unscheduled observations and counts scheduled absent runs as failures. It never uses time-series samples as experimental replicates. Each seed is one resampling cluster, with all its variants kept together and the same cluster draws shared across methods. The estimand is the mean of seed means, giving each seed equal weight even when cluster sizes differ.

Continuous paired differences use all finite paired values, including recorded failed trials. Missing/nonfinite values are reported and not imputed. Their intervals describe the available finite pairs, not all scheduled outcomes; completion denominators and paired outcome tables remain complete. Whole-seed percentile bootstrap intervals retain the number of draws with data. Inputs, script, command, Python version and named RNG/seed are hashed or recorded. Output files refuse overwrite.

At all-zero/all-one observed outcomes, a percentile bootstrap can produce a degenerate interval; it does not establish zero population uncertainty. The tool also reports a separate binary seed outcome: whether every scheduled variant for that seed completed. Its Clopper–Pearson interval inverts binomial CDFs using the [NIST Handbook procedure](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm). This interval assumes independent Bernoulli seed clusters and estimates seed-wide completion probability, distinct from the mean variant completion fraction. It does not treat correlated variants as separate binomial trials. An independent SciPy inverse-beta check covered 165 intervals with maximum endpoint difference below 8.51e-14.

The tool flags fewer than ten seed clusters for review. This flag is an analysis policy, not a power calculation or a claim that ten clusters suffice. Final research comparisons must use separate robot/scenario strata, the frozen evaluation roster and the declared success criteria. Descriptive comparisons across different task families must not replace those per-stratum results.

## Executed component diagnostic example

Phase 3 has forty evaluated trials, two seeds, two case families and two reference variants. Its `COMPLETED` code uses broad component tolerances and is not final research task success. The supplied schedule is a posthoc mechanical transcription of the already-frozen `config/phase3.yaml`, with that source hash in the companion metadata. It does not change the original experiment or its historical parameter selection.

After reproducing Phase 3 data, run:

```bash
python3 analysis/scripts/aggregate_paired_trials.py \
  --schedule benchmarks/configs/phase3_component_pair_schedule.csv \
  --trials results/phase3/evaluation/trials.csv \
  --methods none,joint,sigma_min,log_volume,combined --baseline none \
  --pair-columns seed,case,reference --group-columns case \
  --method-column objective --success-code COMPLETED \
  --metrics mean_position_error,mean_rotation_error,executed_dq_max,final_min_margin \
  --output results/phase3/paired_component_summary_reproduced.json
```

The current execution is preserved in `results/phase3/paired_component_summary_v4.json`, with exact script snapshots and input hashes. Earlier analysis outputs/source versions are retained; paired statistics are unchanged by adding the separate exact binomial interval. Across the eight scheduled pairs, completion counts are none8, joint6, sigma_min6, log_volume8 and combined4. All forty rows, including failures, remain represented. Both strata are explicitly flagged as having only two seed clusters; their intervals are diagnostic output and support no broad research claim.

Eight analytic/roster tests cover equal-seed versus pooled-trial weighting, known constant paired differences, missing scheduled runs, duplicate/unscheduled observations, nonfinite metrics, exact binomial boundary cases the published NIST example and rejection of an empty expected schedule. They passed under Mac Python 3.14.5 and Python 3.12.3 in the reviewed rootless container. The cases use clearly artificial fixtures rather than invented experiment trials:

```bash
python3 tests/analysis/test_paired_statistics.py
```

The test command is included in the current CI entry point. Its container execution used a read-only mount of just the two analysis/test source files into the previously reviewed image; it did not repeat the C++ build. The complete uncached source build has its own earlier archive identity, documented in `reviews/clean_component_environment_review.md`. Final research trial recording, time-weighted metric computation and required main figures still need integration and executed evidence.
