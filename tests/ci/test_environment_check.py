#!/usr/bin/env python3
"""Host-free negative controls for the fail-closed environment checker."""
import hashlib
import importlib.util
import json
import re
import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("checker", ROOT / "scripts/check_ci_environment.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class EnvironmentCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in checker.DEFINITIONS:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
        self.metadata_dir = self.root / "metadata"
        self.metadata_dir.mkdir()
        self.packages = "ros-jazzy-pinocchio\t" + checker.PINOCCHIO + "\n"
        self.metadata = dict(definitions=checker.definitions(self.root),
                             base_image="ghcr.io/sp-zh/predictive-motion-research-ros-base@sha256:" + "a" * 64,
                             platform="linux/amd64", ros="jazzy", ubuntu="24.04",
                             packages_sha256=hashlib.sha256(self.packages.encode()).hexdigest())
        self.metadata["environment_sha256"] = checker.definition_digest(self.metadata["definitions"])
        (self.metadata_dir / "installed-packages.tsv").write_text(self.packages)
        self.save()

    def save(self):
        (self.metadata_dir / "metadata.json").write_text(json.dumps(self.metadata))

    def check(self, packages=None):
        with patch.object(checker, "check_host"), patch.object(checker, "inventory", return_value=packages or self.packages):
            return checker.check_record(self.root, self.metadata_dir)

    def test_ordinary_source_change_does_not_require_rebuild(self):
        (self.root / "algorithm.cpp").write_text("changed source")
        self.check()

    def test_dependency_drift_fails(self):
        with (self.root / checker.DEFINITIONS[0]).open("a") as stream:
            stream.write("\n# changed dependency definition\n")
        with self.assertRaisesRegex(ValueError, "definitions differ"):
            self.check()

    def test_mutable_base_fails(self):
        self.metadata["base_image"] = "ghcr.io/sp-zh/predictive-motion-research-ros-base:latest"
        self.save()
        with self.assertRaisesRegex(ValueError, "registry digest"):
            self.check()

    def test_package_drift_fails(self):
        with self.assertRaisesRegex(ValueError, "package inventory"):
            self.check("different-package\t1\n")

    def test_wrong_architecture_metadata_fails(self):
        self.metadata["platform"] = "linux/arm64"
        self.save()
        with self.assertRaisesRegex(ValueError, "platform/ROS/Ubuntu"):
            self.check()

    def test_missing_manifest_fails(self):
        (self.metadata_dir / "metadata.json").unlink()
        with self.assertRaises(FileNotFoundError):
            self.check()


class ExitPropagation(unittest.TestCase):
    def run_candidate(self, install_status, test_status, diagnostic_status):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts/phase0").mkdir(parents=True)
            (root / "scripts/run_ci_image.sh").write_bytes((ROOT / "scripts/run_ci_image.sh").read_bytes())
            (root / "scripts/phase0/setup_linux.sh").write_text(f"exit {install_status}\n")
            (root / "scripts/ci.sh").write_text(f"touch tests-executed\nexit {test_status}\n")
            (root / "scripts/collect_environment.py").write_text(
                f"from pathlib import Path\nPath('diagnostics-executed').touch()\nraise SystemExit({diagnostic_status})\n")
            result = subprocess.run(["bash", "scripts/run_ci_image.sh", "copy-base"], cwd=root,
                                    capture_output=True, text=True)
            return result.returncode, (root / "tests-executed").exists(), (root / "diagnostics-executed").exists()

    def test_failed_install_stops_tests_and_keeps_failure(self):
        self.assertEqual(self.run_candidate(37, 0, 0), (37, False, True))

    def test_failed_tests_keep_nonzero_even_if_diagnostics_fail(self):
        self.assertEqual(self.run_candidate(0, 73, 42), (73, True, True))

    def test_diagnostic_failure_after_success_is_visible(self):
        self.assertEqual(self.run_candidate(0, 0, 42), (42, True, True))

    def test_success_runs_tests_and_diagnostics(self):
        self.assertEqual(self.run_candidate(0, 0, 0), (0, True, True))


class WorkflowReference(unittest.TestCase):
    def test_daily_image_and_recorded_reference_agree(self):
        text = (ROOT / ".github/workflows/ci.yml").read_text()
        image = re.search(r"^      image: (\S+)$", text, re.MULTILINE).group(1)
        recorded = re.search(r"^          CI_IMAGE_REFERENCE: (\S+)$", text, re.MULTILINE).group(1)
        self.assertEqual(image, recorded)
        self.assertRegex(image, r"@sha256:[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
