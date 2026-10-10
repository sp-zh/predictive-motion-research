#!/usr/bin/env python3
"""Record/check dependency definitions, never compare the image commit to HEAD."""
import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

DEFINITIONS = (
    "scripts/phase0/setup_linux.sh", "scripts/check_ci_environment.py",
    "docker/Dockerfile.ci", "docker/Dockerfile.ci.dockerignore",
)
BASE_PATTERN = r"ghcr\.io/sp-zh/predictive-motion-research-ros-base@sha256:[0-9a-f]{64}"
PINOCCHIO = "4.1.0-1noble.20260826.071113"


def definitions(root):
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in DEFINITIONS}


def definition_digest(hashes):
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def inventory():
    return subprocess.check_output(
        ["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\n"], text=True)


def check_host():
    release = dict(line.split("=", 1) for line in Path("/etc/os-release").read_text().splitlines()
                   if "=" in line)
    if release.get("ID", "").strip('"') != "ubuntu" or release.get("VERSION_ID", "").strip('"') != "24.04":
        raise ValueError("Ubuntu 24.04 required")
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise ValueError("linux/amd64 required")
    if not Path("/opt/ros/jazzy/setup.bash").is_file():
        raise ValueError("ROS Jazzy required")
    version = subprocess.check_output(
        ["dpkg-query", "-W", "-f=${Version}", "ros-jazzy-pinocchio"], text=True)
    if version != PINOCCHIO:
        raise ValueError(f"Pinocchio {PINOCCHIO} required, got {version}")


def check_record(root, metadata_dir):
    metadata = json.loads((metadata_dir / "metadata.json").read_text())
    hashes = definitions(root)
    if metadata["definitions"] != hashes or metadata["environment_sha256"] != definition_digest(hashes):
        raise ValueError("environment definitions differ")
    if not re.fullmatch(BASE_PATTERN, metadata["base_image"]):
        raise ValueError("base must be a project GHCR registry digest")
    if metadata["platform"] != "linux/amd64" or metadata["ros"] != "jazzy" or metadata["ubuntu"] != "24.04":
        raise ValueError("image platform/ROS/Ubuntu metadata differs")
    check_host()
    packages = (metadata_dir / "installed-packages.tsv").read_text()
    if hashlib.sha256(packages.encode()).hexdigest() != metadata["packages_sha256"] or packages != inventory():
        raise ValueError("installed package inventory differs")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["record", "check", "hash"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--metadata-dir", type=Path, default=Path("/usr/local/share/predictive-motion-ci"))
    parser.add_argument("--source-commit")
    parser.add_argument("--base-image")
    args = parser.parse_args()
    try:
        if args.mode == "hash":
            print(definition_digest(definitions(args.root)))
        elif args.mode == "check":
            metadata = check_record(args.root, args.metadata_dir)
            print("CI dependency environment verified: " + metadata["environment_sha256"])
        else:
            if not args.source_commit or not re.fullmatch(r"[0-9a-f]{40}", args.source_commit):
                raise ValueError("a full source commit is required")
            if not args.base_image or not re.fullmatch(BASE_PATTERN, args.base_image):
                raise ValueError("a locked project GHCR base image is required")
            check_host()
            hashes, packages = definitions(args.root), inventory()
            args.metadata_dir.mkdir(parents=True, exist_ok=True)
            (args.metadata_dir / "installed-packages.tsv").write_text(packages)
            metadata = dict(source_repository="https://github.com/sp-zh/predictive-motion-research",
                            source_commit=args.source_commit, base_image=args.base_image,
                            platform="linux/amd64", ros="jazzy", ubuntu="24.04",
                            definitions=hashes, environment_sha256=definition_digest(hashes),
                            packages_sha256=hashlib.sha256(packages.encode()).hexdigest())
            (args.metadata_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"CI dependency image needs updating or repair: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
