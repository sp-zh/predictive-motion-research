#!/usr/bin/env python3
"""Validate the retained ROS lock and build tag-free Skopeo source references."""
import argparse
import json
import re
import sys
from pathlib import Path

REPOSITORY = "docker.io/library/ros"
DIGEST = r"sha256:[0-9a-f]{64}"


def locked_source(original):
    name, separator, digest = original.rpartition("@")
    if not separator:
        raise ValueError("locked ROS source is missing @sha256 digest")
    if not re.fullmatch(DIGEST, digest):
        raise ValueError("locked ROS source requires a lowercase 64-hex sha256 digest")
    if not re.fullmatch(r"docker\.io/library/ros(?::jazzy-ros-base-noble)?", name):
        raise ValueError("source must be docker.io/library/ros, optionally tagged jazzy-ros-base-noble")
    return {"original": original, "index_reference": f"{REPOSITORY}@{digest}"}


def dockerfile_source(path):
    values = re.findall(r"^FROM\s+(\S+)\s*(?:#.*)?$", path.read_text(), re.MULTILINE)
    if len(values) != 1:
        raise ValueError("development Dockerfile must contain exactly one explicit locked FROM")
    return locked_source(values[0])["original"]


def platform_reference(original, index):
    locked_source(original)
    if index.get("schemaVersion") != 2 or index.get("mediaType") not in (
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.index.v1+json",
    ):
        raise ValueError("source must return a schema-2 Docker manifest list or OCI index")
    selected = [entry for entry in index.get("manifests", [])
                if entry.get("platform", {}).get("os") == "linux"
                and entry.get("platform", {}).get("architecture") == "amd64"]
    if len(selected) != 1:
        raise ValueError("exactly one linux/amd64 platform manifest required")
    digest = selected[0].get("digest", "")
    if not re.fullmatch(DIGEST, digest):
        raise ValueError("amd64 platform manifest requires a lowercase 64-hex sha256 digest")
    return f"{REPOSITORY}@{digest}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("original", "index", "platform"))
    parser.add_argument("value", help="Dockerfile path for original; locked source otherwise")
    parser.add_argument("index_path", nargs="?", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "original":
            print(dockerfile_source(Path(args.value)))
        elif args.operation == "index":
            print(locked_source(args.value)["index_reference"])
        else:
            if args.index_path is None:
                raise ValueError("platform reference requires the inspected source index JSON")
            print(platform_reference(args.value, json.loads(args.index_path.read_text())))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Invalid locked ROS source reference: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
