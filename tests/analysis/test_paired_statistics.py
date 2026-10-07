#!/usr/bin/env python3
"""Analytic/roster tests for analysis math; fixtures are not experiment results."""
import importlib.util
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('paired', root / 'analysis/scripts/aggregate_paired_trials.py')
paired = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paired)


class PairedStatistics(unittest.TestCase):
    def fixture(self):
        schedule, records = [], []
        # One seed has one trial and the other has three: equal-seed weighting
        # yields delta3, whereas a pooled-trial mean would incorrectly yield4.5.
        for seed, variants, delta in [('a', 1, 0), ('b', 3, 6)]:
            for variant in range(variants):
                key = {'seed': seed, 'variant': str(variant)}
                schedule.append(key)
                records += [dict(key, method='base', code='OK', error='2'),
                            dict(key, method='test', code='OK' if seed == 'a' else 'FAIL',
                                 error=str(2 + delta))]
        return schedule, records

    def analyze(self, schedule, records, draws=1000):
        return paired.aggregate(schedule, records, ['base', 'test'], 'base', ['error'],
                                ['seed', 'variant'], 'method', 'seed', 'code', 'OK', draws, 44)

    def test_unequal_cluster_size_and_known_quantiles(self):
        schedule, records = self.fixture()
        result = self.analyze(schedule, records)
        method = result['methods']['test']
        self.assertEqual(method['completed_runs'], 1)
        self.assertEqual(method['expected_runs'], 4)
        self.assertEqual(method['equal_seed_weight_completion']['mean_of_seed_means'], .5)
        difference = result['comparisons']['test']['continuous_differences']['error']
        self.assertEqual(difference['method_minus_baseline']['mean_of_seed_means'], 3)
        self.assertEqual(difference['method_minus_baseline']['percentile_95'], [0, 6])
        self.assertEqual(paired.quantile([1, 4, 10], .25), 2.5)

    def test_missing_scheduled_run_is_failure_not_dropped(self):
        schedule, records = self.fixture()
        records = [r for r in records if not (r['method'] == 'test' and r['seed'] == 'b' and r['variant'] == '2')]
        result = self.analyze(schedule, records)
        self.assertEqual(result['methods']['test']['status_counts'], {'OK': 1, 'FAIL': 2, 'MISSING_RUN': 1})
        self.assertEqual(result['comparisons']['test']['paired_completion_table']['baseline_only'], 3)
        metric = result['comparisons']['test']['continuous_differences']['error']
        self.assertEqual(metric['observed_finite_pairs'], 3)
        self.assertEqual(metric['missing_or_nonfinite_pairs'], 1)

    def test_constant_paired_difference_and_zero_difference(self):
        schedule, records = self.fixture()
        for row in records:
            row['error'] = '5' if row['method'] == 'test' else '2'
            row['code'] = 'OK'
        result = self.analyze(schedule, records)
        comparison = result['comparisons']['test']
        self.assertEqual(comparison['completion_difference']['percentile_95'], [0, 0])
        self.assertEqual(comparison['continuous_differences']['error']['method_minus_baseline']['percentile_95'], [3, 3])

    def test_duplicate_or_unscheduled_observation_rejected(self):
        schedule, records = self.fixture()
        with self.assertRaises(ValueError):
            self.analyze(schedule, records + [records[0]])
        with self.assertRaises(ValueError):
            self.analyze(schedule, records + [dict(records[0], seed='not-scheduled')])

    def test_nonfinite_and_no_metric_pairs_are_explicit(self):
        schedule, records = self.fixture()
        for row in records:
            if row['method'] == 'test':
                row['error'] = 'nan'
        metric = self.analyze(schedule, records)['comparisons']['test']['continuous_differences']['error']
        self.assertIsNone(metric['method_minus_baseline'])
        self.assertEqual(metric['missing_or_nonfinite_pairs'], 4)

    def test_exact_binomial_boundaries_not_degenerate(self):
        zero = paired.exact_binomial_interval(0, 20)
        all_completed = paired.exact_binomial_interval(20, 20)
        self.assertAlmostEqual(zero[1], 1 - math.pow(.025, 1 / 20), places=12)
        self.assertAlmostEqual(all_completed[0], math.pow(.025, 1 / 20), places=12)
        self.assertEqual(zero[0], 0)
        self.assertEqual(all_completed[1], 1)
        self.assertGreater(zero[1], 0)
        self.assertLess(all_completed[0], 1)
        with self.assertRaises(ValueError):
            paired.exact_binomial_interval(1, 0)

    def test_nist_published_binomial_example(self):
        # NIST PRC7.2.4.1 gives 4/20, 90%: (0.071354, 0.401029), rounded.
        lower, upper = paired.exact_binomial_interval(4, 20, .9)
        self.assertAlmostEqual(lower, .071354, delta=2e-6)
        self.assertAlmostEqual(upper, .401029, delta=2e-6)

    def test_empty_cli_schedule_cannot_produce_success_output(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'schedule.csv').write_text('seed,variant\n')
            (folder / 'trials.csv').write_text('seed,variant,method,code,error\n')
            result = subprocess.run([sys.executable, str(root / 'analysis/scripts/aggregate_paired_trials.py'),
                                     '--schedule', str(folder / 'schedule.csv'),
                                     '--trials', str(folder / 'trials.csv'), '--methods', 'base,test',
                                     '--baseline', 'base', '--pair-columns', 'seed,variant',
                                     '--group-columns', 'variant', '--success-code', 'OK',
                                     '--output', str(folder / 'output.json')],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('schedule is empty', result.stderr)
            self.assertFalse((folder / 'output.json').exists())


if __name__ == '__main__':
    unittest.main()
