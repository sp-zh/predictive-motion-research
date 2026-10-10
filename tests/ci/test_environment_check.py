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
spec_audit = importlib.util.spec_from_file_location("audit", ROOT / "scripts/ci/verify_test_results.py")
audit = importlib.util.module_from_spec(spec_audit)
spec_audit.loader.exec_module(audit)
spec_source = importlib.util.spec_from_file_location("source", ROOT / "scripts/ci/ros_source_reference.py")
source = importlib.util.module_from_spec(spec_source)
spec_source.loader.exec_module(source)


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


class TestInventory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.folder = self.root / "build/example/test_results/example"
        self.folder.mkdir(parents=True)
        for name, count in (("plant_test", 4), ("kinematics_test", 7), ("ik_test", 7), ("nullspace_test", 6)):
            cases = "".join(f'<testcase classname="{name}" name="case{i}" status="run"/>' for i in range(count))
            (self.folder / (name + ".gtest.xml")).write_text("<testsuites><testsuite>" + cases + "</testsuite></testsuites>")
        (self.folder / "CTest.xml").write_text('<testsuite tests="9999"/>')
        self.log = self.root / "results/ci-images/full-ci.log"
        self.log.parent.mkdir(parents=True)
        self.log.write_text("Ran 8 tests in 0.039s\n\nOK\nNUMERICAL_PASS samples=2000 seed=42 h=1e-6\nINSTALLED_EIGEN_ONLY_CONSUMER_PASS\nINSTALLED_EIGEN_ONLY_NULLSPACE_CONSUMER_PASS\n")

    def test_native_reports_counted_once(self):
        self.assertEqual(audit.audit(self.root)["native_gtest_count"], 24)

    def test_skipped_native_report_fails(self):
        path = self.folder / "plant_test.gtest.xml"
        path.write_text(path.read_text().replace('status="run"/>', 'status="notrun"><skipped/></testcase>', 1))
        with self.assertRaisesRegex(ValueError, "failed/skipped"):
            audit.audit(self.root)

    def test_missing_report_fails(self):
        (self.folder / "plant_test.gtest.xml").unlink()
        with self.assertRaisesRegex(ValueError, "inventory changed"):
            audit.audit(self.root)

    def test_statistics_skip_fails(self):
        self.log.write_text(self.log.read_text().replace("OK\n", "OK (skipped=1)\n"))
        with self.assertRaisesRegex(ValueError, "statistics"):
            audit.audit(self.root)


class RosSourceReference(unittest.TestCase):
    def setUp(self):
        self.original = source.dockerfile_source(ROOT / "docker/Dockerfile")
        self.index = {"schemaVersion": 2,
                      "mediaType": "application/vnd.oci.image.index.v1+json",
                      "manifests": [{"digest": "sha256:" + "b" * 64,
                                     "platform": {"os": "linux", "architecture": "amd64"}}]}

    def test_real_tag_digest_preserves_locked_digest(self):
        self.assertIn("ros:jazzy-ros-base-noble@sha256:", self.original)
        normalized = source.locked_source(self.original)["index_reference"]
        self.assertEqual(normalized, "docker.io/library/ros@" + self.original.rpartition("@")[2])
        self.assertEqual(normalized.rpartition("@")[2], "sha256:066420e07f60aa18262f2479981def87ebcfcec42eefb0c0c57c4a46098348ca")

    def test_publisher_cli_uses_same_reference_logic(self):
        # These are the actual commands used by publish_ci_images.sh, without invoking publication.
        script = ROOT / "scripts/ci/ros_source_reference.py"
        original = subprocess.check_output(["python3", str(script), "original", str(ROOT / "docker/Dockerfile")], text=True).strip()
        normalized = subprocess.check_output(["python3", str(script), "index", original], text=True).strip()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.json"
            path.write_text(json.dumps(self.index))
            platform = subprocess.check_output(["python3", str(script), "platform", original, str(path)], text=True).strip()
        self.assertEqual(normalized, source.locked_source(original)["index_reference"])
        self.assertEqual(platform, "docker.io/library/ros@sha256:" + "b" * 64)

    def test_platform_never_reintroduces_tag(self):
        ref = source.platform_reference(self.original, self.index)
        self.assertEqual(ref, "docker.io/library/ros@sha256:" + "b" * 64)
        self.assertNotIn(":jazzy", ref)

    def test_missing_digest_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing @sha256"):
            source.locked_source("docker.io/library/ros:jazzy-ros-base-noble")

    def test_malformed_digest_rejected(self):
        for digest in ("sha256:abc", "sha256:" + "g" * 64, "sha512:" + "a" * 64, "sha256:" + "A" * 64, ""):
            with self.subTest(digest=digest), self.assertRaisesRegex(ValueError, "64-hex sha256"):
                source.locked_source("docker.io/library/ros@" + digest)

    def test_disallowed_source_rejected(self):
        for name in ("example.com:5000/library/ros", "docker.io/other/ros", "docker.io/library/ros:latest"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "source must be"):
                source.locked_source(name + "@sha256:" + "a" * 64)

    def test_bad_platform_digest_rejected(self):
        self.index["manifests"][0]["digest"] = "sha256:bad"
        with self.assertRaisesRegex(ValueError, "platform manifest requires"):
            source.platform_reference(self.original, self.index)

    def test_ambiguous_or_missing_amd64_rejected(self):
        for manifests in ([], self.index["manifests"] * 2):
            with self.subTest(manifests=manifests), self.assertRaisesRegex(ValueError, "exactly one"):
                source.platform_reference(self.original, dict(self.index, manifests=manifests))


if __name__ == "__main__":
    unittest.main()
