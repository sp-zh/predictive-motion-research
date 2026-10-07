#!/usr/bin/env python3
"""Aggregate a declared trial schedule without dropping absent or failed runs.

Input is a flat trial-summary CSV, not trajectory samples. Resampling uses whole
seed clusters and the same draw across methods. Output is descriptive evidence;
the caller must identify diagnostic versus frozen research evaluation data.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import random
import statistics
import sys


def quantile(values, probability):
    values = sorted(values)
    position = (len(values) - 1) * probability
    lo = math.floor(position)
    hi = math.ceil(position)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def exact_binomial_interval(completed, total, confidence=.95):
    """Clopper-Pearson interval, conditional on independent Bernoulli seeds.

    Invert binomial CDFs as in NIST Handbook PRC 7.2.4.1. Log terms avoid
    overflow in binomial coefficients; fixed bisection has no solver dependency.
    """
    if total < 1 or completed < 0 or completed > total or not 0 < confidence < 1:
        raise ValueError('Invalid binomial interval input')
    alpha = 1 - confidence

    def cdf(cutoff, probability):
        if probability <= 0:
            return 1.0
        if probability >= 1:
            return float(cutoff >= total)
        terms = [math.lgamma(total + 1) - math.lgamma(k + 1) - math.lgamma(total - k + 1)
                 + k * math.log(probability) + (total - k) * math.log1p(-probability)
                 for k in range(cutoff + 1)]
        maximum = max(terms)
        return min(1.0, math.exp(maximum) * math.fsum(math.exp(x - maximum) for x in terms))

    def root(cutoff, target):
        lo, hi = 0.0, 1.0
        for _ in range(64):
            middle = (lo + hi) / 2
            if cdf(cutoff, middle) > target:
                lo = middle
            else:
                hi = middle
        return (lo + hi) / 2

    return [0.0 if completed == 0 else root(completed - 1, 1 - alpha / 2),
            1.0 if completed == total else root(completed, alpha / 2)]


def aggregate(schedule, records, methods, baseline, metrics, pair_columns,
              method_column, cluster_column, status_column, success_code,
              resamples, bootstrap_seed):
    if len(set(methods)) != len(methods) or baseline not in methods:
        raise ValueError('Methods must be unique and include the baseline')
    if cluster_column not in pair_columns:
        raise ValueError('Cluster identity must be part of the trial identity')
    expected = {}
    for row in schedule:
        key = tuple(row[name] for name in pair_columns)
        if key in expected:
            raise ValueError('Duplicate scheduled trial: ' + repr(key))
        expected[key] = row[cluster_column]
    if not expected:
        raise ValueError('Empty schedule')
    observed = {}
    for row in records:
        key = tuple(row[name] for name in pair_columns)
        method = row[method_column]
        if key not in expected or method not in methods:
            raise ValueError('Unscheduled trial or method: ' + repr((key, method)))
        if (key, method) in observed:
            raise ValueError('Duplicate observed trial: ' + repr((key, method)))
        observed[key, method] = row
    clusters = sorted(set(expected.values()))
    keys = {cluster: [key for key in expected if expected[key] == cluster] for cluster in clusters}

    def success(key, method):
        row = observed.get((key, method))
        return int(row is not None and row.get(status_column) == success_code)

    def value(key, method, metric):
        row = observed.get((key, method))
        if row is None or not row.get(metric):
            return None
        result = float(row[metric])
        return result if math.isfinite(result) else None

    # Store the draws once so every comparison uses identical resampled clusters.
    rng = random.Random(bootstrap_seed)
    draws = [[rng.randrange(len(clusters)) for _ in clusters] for _ in range(resamples)]

    def interval(seed_means):
        present = [i for i, cluster in enumerate(clusters) if cluster in seed_means]
        if not present:
            return None
        samples = []
        for draw in draws:
            selected = [seed_means[clusters[i]] for i in draw if i in present]
            if selected:
                samples.append(statistics.fmean(selected))
        return {'mean_of_seed_means': statistics.fmean(seed_means.values()),
                'percentile_95': [quantile(samples, .025), quantile(samples, .975)] if samples else None,
                'clusters_with_data': len(present),
                'bootstrap_draws_with_data': len(samples)}

    summaries, comparisons = {}, {}
    for method in methods:
        codes = {}
        for key in expected:
            row = observed.get((key, method))
            code = (row.get(status_column) or 'MISSING_STATUS') if row else 'MISSING_RUN'
            codes[code] = codes.get(code, 0) + 1
        rate_means = {cluster: statistics.fmean(success(key, method) for key in keys[cluster])
                      for cluster in clusters}
        seed_completed = sum(all(success(key, method) for key in keys[cluster]) for cluster in clusters)
        summaries[method] = {'expected_runs': len(expected),
                             'completed_runs': sum(success(key, method) for key in expected),
                             'status_counts': codes,
                             'equal_seed_weight_completion': interval(rate_means),
                             'seed_all_variants_completed': {
                                 'completed_seeds': seed_completed, 'total_seeds': len(clusters),
                                 'exact_binomial_95': exact_binomial_interval(seed_completed, len(clusters)),
                                 'assumption': 'independent Bernoulli seed clusters; one outcome is all scheduled variants completing',
                                 'estimand': 'probability a seed completes every variant; distinct from mean variant completion fraction'}}
        if method == baseline:
            continue
        table = {'both_completed': 0, 'method_only': 0, 'baseline_only': 0, 'neither_completed': 0}
        for key in expected:
            a, b = success(key, method), success(key, baseline)
            label = 'both_completed' if a and b else 'method_only' if a else 'baseline_only' if b else 'neither_completed'
            table[label] += 1
        differences = {cluster: statistics.fmean(success(key, method) - success(key, baseline)
                                                 for key in keys[cluster]) for cluster in clusters}
        continuous = {}
        for metric in metrics:
            seed_means, pairs = {}, 0
            for cluster in clusters:
                deltas = []
                for key in keys[cluster]:
                    a, b = value(key, method, metric), value(key, baseline, metric)
                    if a is not None and b is not None:
                        deltas.append(a - b)
                pairs += len(deltas)
                if deltas:
                    seed_means[cluster] = statistics.fmean(deltas)
            continuous[metric] = {'method_minus_baseline': interval(seed_means),
                                  'observed_finite_pairs': pairs,
                                  'missing_or_nonfinite_pairs': len(expected) - pairs,
                                  'conditioning': 'finite paired values, including recorded failed trials; absent values are not imputed'}
        comparisons[method] = {'paired_completion_table': table,
                               'completion_difference': interval(differences),
                               'continuous_differences': continuous}
    return {'scope': 'trial-summary aggregation; does not establish research validity or independence of seeds',
            'baseline': baseline, 'cluster_count': len(clusters),
            'low_cluster_count': len(clusters) < 10,
            'low_cluster_count_policy': 'below 10 clusters is flagged for review; no power claim follows from passing this flag',
            'estimand': 'mean of seed means; equal seed weight regardless of trials per seed',
            'bootstrap': {'algorithm': 'Python random.Random MT19937; whole-seed draws shared across methods',
                          'seed': bootstrap_seed, 'draws': resamples, 'interval': 'percentile 95%; linear empirical quantiles'},
            'methods': summaries, 'comparisons': comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--schedule', type=Path, required=True)
    parser.add_argument('--trials', type=Path, required=True)
    parser.add_argument('--methods', required=True)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--pair-columns', required=True)
    parser.add_argument('--group-columns', required=True,
                        help='Stratify comparisons, e.g. robot,scenario; must be part of pair identity')
    parser.add_argument('--method-column', default='method')
    parser.add_argument('--cluster-column', default='seed')
    parser.add_argument('--status-column', default='code')
    parser.add_argument('--success-code', required=True)
    parser.add_argument('--metrics', default='')
    parser.add_argument('--resamples', type=int, default=10000)
    parser.add_argument('--bootstrap-seed', type=int, default=4405)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.resamples < 1:
        parser.error('resamples must be positive')
    if args.output.exists() or args.output.is_symlink():
        parser.error('output already exists; refuse replacing an analysis identity')
    schedule_bytes = args.schedule.read_bytes()
    trial_bytes = args.trials.read_bytes()
    schedule = list(csv.DictReader(io.StringIO(schedule_bytes.decode(), newline='')))
    records = list(csv.DictReader(io.StringIO(trial_bytes.decode(), newline='')))
    if not schedule:
        parser.error('expected trial schedule is empty')
    pair_columns = args.pair_columns.split(',')
    group_columns = args.group_columns.split(',')
    if not set(group_columns).issubset(pair_columns):
        parser.error('group columns must be part of pair identity')
    groups = sorted(set(tuple(row[name] for name in group_columns) for row in schedule))
    if any(tuple(row[name] for name in group_columns) not in groups for row in records):
        parser.error('observed row has an unscheduled group')
    reports = []
    for group in groups:
        selected_schedule = [row for row in schedule if tuple(row[name] for name in group_columns) == group]
        selected_records = [row for row in records if tuple(row[name] for name in group_columns) == group]
        result = aggregate(selected_schedule, selected_records, args.methods.split(','), args.baseline,
                           [m for m in args.metrics.split(',') if m], pair_columns,
                           args.method_column, args.cluster_column, args.status_column,
                           args.success_code, args.resamples, args.bootstrap_seed)
        reports.append({'group': dict(zip(group_columns, group)), 'statistics': result})
    report = {'groups': reports}
    report['provenance'] = {'python': sys.version, 'argv': sys.argv,
                            'schedule_sha256': hashlib.sha256(schedule_bytes).hexdigest(),
                            'trials_sha256': hashlib.sha256(trial_bytes).hexdigest(),
                            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps([{'group': item['group'], 'clusters': item['statistics']['cluster_count'],
                       'completed': {method: value['completed_runs'] for method, value in item['statistics']['methods'].items()}}
                      for item in reports], indent=2))


if __name__ == '__main__':
    main()
