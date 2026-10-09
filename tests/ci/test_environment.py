#!/usr/bin/env python3
"""CI infrastructure negatives use fixtures, never numerical research runs."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENV = load('ci_environment', ROOT / 'scripts/ci/check_environment.py')
AUDIT = load('ci_audit', ROOT / 'scripts/ci/verify_test_results.py')


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ENV.DEFINITIONS:
            dest = self.root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
        self.metadata = self.root / 'metadata'
        self.packages = {spec.split('=')[0]: spec.partition('=')[2] or 'fixture-version'
                         for spec in ENV.dependency_specs(self.root)}
        self.base = 'ghcr.io/sp-zh/predictive-motion-research-ros-base@sha256:' + 'a' * 64
        self.invoke('--write', '--base-ref', self.base, '--source-commit', 'b' * 40)

    def invoke(self, *args):
        with patch.object(sys, 'argv', ['check', '--root', str(self.root), '--metadata', str(self.metadata), *args]), \
                patch.object(ENV, 'verify_base'), patch.object(ENV, 'installed_packages', return_value=self.packages), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            ENV.main()

    def rejects(self, *args):
        with self.assertRaises(SystemExit) as exc:
            self.invoke(*args)
        self.assertEqual(exc.exception.code, 1)

    def test_same_definitions_and_different_checkout_commit_pass(self):
        # Head equality is deliberately irrelevant to the immutable environment.
        self.invoke('--source-commit', 'c' * 40)

    def test_definition_change_is_nonzero(self):
        with (self.root / 'scripts/phase0/setup_linux.sh').open('a') as file:
            file.write('\n# dependency definition changed\n')
        self.rejects()

    def test_pinned_version_change_is_nonzero(self):
        self.packages['ros-jazzy-pinocchio'] = 'wrong-version'
        self.rejects()

    def test_missing_dependency_is_nonzero(self):
        del self.packages['libeigen3-dev']
        self.rejects()

    def test_mutable_base_is_nonzero(self):
        self.rejects('--write', '--base-ref', 'ghcr.io/sp-zh/predictive-motion-research-ros-base:latest', '--source-commit', 'b' * 40)

    def test_missing_metadata_is_nonzero(self):
        (self.metadata / 'environment.json').unlink()
        self.rejects()

    def test_changed_unpinned_dependency_is_nonzero(self):
        self.packages['cmake'] = 'another-version'
        self.rejects()

    def test_build_context_only_allows_environment_definitions(self):
        ignore = (ROOT / 'docker/Dockerfile.ci.dockerignore').read_text()
        allowed = {line[1:] for line in ignore.splitlines()
                   if line.startswith('!') and not line.endswith('/')}
        self.assertEqual(allowed, set(ENV.DEFINITIONS))
        recipe = (ROOT / 'docker/Dockerfile.ci').read_text()
        self.assertNotIn('COPY . ', recipe)
        self.assertNotIn('scripts/ci.sh', recipe)
        for line in recipe.splitlines():
            if line.startswith('COPY '):
                self.assertTrue(set(line.split()[1:-1]).issubset(allowed))

    def test_missing_test_reports_rejected(self):
        with self.assertRaises(ValueError):
            AUDIT.audit(self.root)

    def test_native_reports_counted_once_and_skip_rejected(self):
        folder = self.root / 'build/example/test_results/example'
        folder.mkdir(parents=True)
        for name, count in [('plant_test', 4), ('kinematics_test', 7), ('ik_test', 7), ('nullspace_test', 6)]:
            cases = ''.join(f'<testcase classname="{name}" name="case{i}" status="run"/>' for i in range(count))
            (folder / (name + '.gtest.xml')).write_text('<testsuites><testsuite>' + cases + '</testsuite></testsuites>')
        # CTest reports include wrapper counts, deliberately ignored.
        (folder / 'CTest.xml').write_text('<testsuite tests="9999"/>')
        log = self.root / 'results/ci-image/full-test.log'
        log.parent.mkdir(parents=True)
        log.write_text('Ran 8 tests in 0.039s\n\nOK\nNUMERICAL_PASS samples=2000 seed=42 h=1e-6\nINSTALLED_EIGEN_ONLY_CONSUMER_PASS\nINSTALLED_EIGEN_ONLY_NULLSPACE_CONSUMER_PASS\n')
        self.assertEqual(AUDIT.audit(self.root)['native_gtest_count'], 24)
        path = folder / 'plant_test.gtest.xml'
        path.write_text(path.read_text().replace('status="run"/>', 'status="notrun"><skipped/></testcase>', 1))
        with self.assertRaises(ValueError):
            AUDIT.audit(self.root)

    def test_test_command_nonzero_survives_candidate_runner(self):
        # Execute the real wrapper with an intentionally failing test entrypoint.
        (self.root / 'scripts/ci.sh').write_text('exit 17\n')
        (self.root / 'scripts/ci/check_environment.py').write_text('print("fixture environment")\n')
        result = subprocess.run(['bash', str(ROOT / 'scripts/ci/run_candidate.sh')], cwd=self.root,
                                env={'PATH': '/opt/homebrew/bin:/usr/bin:/bin', 'CI_IMAGE_STAGE': 'ci'},
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 17, result.stderr)


if __name__ == '__main__':
    unittest.main()
