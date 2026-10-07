#!/usr/bin/env python3
"""Collect version evidence without exposing credentials or full environment."""
import argparse
import datetime
import importlib.metadata
import json
import platform
import shutil
import subprocess
from pathlib import Path


def command(argv):
    try:
        result = subprocess.run(argv, text=True, capture_output=True, timeout=20)
        return {'command': argv, 'exit_code': result.returncode, 'stdout': result.stdout.strip(), 'stderr': result.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'command': argv, 'error': str(exc)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    packages = {}
    for name in ['numpy', 'pandas', 'matplotlib', 'pytest', 'mujoco', 'pin', 'toppra']:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    inventory = {
        'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'platform': platform.platform(), 'machine': platform.machine(),
        'python': platform.python_version(), 'python_packages': packages,
        'tools': {name: shutil.which(name) for name in ['c++','cmake','ninja','git','colcon','ros2','docker','FreeCADCmd']},
        'commands': [command(argv) for argv in [
            ['c++','--version'], ['cmake','--version'], ['git','--version'],
            ['dpkg-query','-W','ros-jazzy-rclcpp','ros-jazzy-pinocchio','ros-jazzy-moveit-servo','ros-jazzy-xacro','ros-jazzy-coal','libyaml-cpp-dev','libeigen3-dev','libgtest-dev'],
        ]],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
