#!/usr/bin/env python3
"""Record/check dependency definitions, not the current project commit."""
import argparse
import hashlib
import json
import platform
import re
import shlex
import subprocess
from pathlib import Path

DEFINITIONS = (
    'docker/Dockerfile.ci', 'docker/Dockerfile.ci.dockerignore',
    'docker/ros-base-source.txt', 'scripts/phase0/setup_linux.sh',
    'scripts/ci/check_environment.py',
)
METADATA = Path('/usr/local/share/predictive-motion-ci')
BASE_PATTERN = r'ghcr\.io/sp-zh/predictive-motion-research-ros-base@sha256:[0-9a-f]{64}'


def definition_hashes(root):
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in DEFINITIONS}


def dependency_specs(root):
    # Use the existing installation script as the only apt package definition.
    script = (root / 'scripts/phase0/setup_linux.sh').read_text().replace('\\\n', ' ')
    installs = [shlex.split(line) for line in script.splitlines()
                if line.startswith('DEBIAN_FRONTEND=noninteractive apt-get install ')]
    if len(installs) != 1:
        raise ValueError('expected one apt-get install in setup_linux.sh; update the parser explicitly')
    return [word for word in installs[0][3:] if not word.startswith('-')]


def installed_packages():
    result = subprocess.run(
        ['dpkg-query', '-W', '-f=${binary:Package}\t${Version}\t${Status}\n'],
        check=True, capture_output=True, text=True)
    rows = [line.split('\t') for line in result.stdout.splitlines()]
    packages = {name: version for name, version, status in rows if status == 'install ok installed'}
    return packages


def required_packages(root, installed):
    required = {}
    for spec in dependency_specs(root):
        name, _, pinned = spec.partition('=')
        version = installed.get(name, installed.get(name + ':amd64'))
        if not version or (pinned and version != pinned):
            raise ValueError(f'{spec}: installed version is {version!r}')
        required[name] = version
    return required


def verify_base():
    os_release = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines()
                      if '=' in line)
    if os_release.get('ID', '').strip('"') != 'ubuntu' or os_release.get('VERSION_ID', '').strip('"') != '24.04':
        raise ValueError('Ubuntu 24.04 required')
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise ValueError('only Linux x86_64 / linux/amd64 is validated')
    if not Path('/opt/ros/jazzy/setup.bash').is_file():
        raise ValueError('ROS Jazzy setup.bash is missing')
    subprocess.run(['bash', '-c', 'source /opt/ros/jazzy/setup.bash && test "$ROS_DISTRO" = jazzy && command -v ros2'], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--metadata', type=Path, default=METADATA)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--base-only', action='store_true')
    parser.add_argument('--base-ref')
    parser.add_argument('--source-commit')
    args = parser.parse_args()
    try:
        if args.base_ref and not re.fullmatch(BASE_PATTERN, args.base_ref):
            raise ValueError('a pinned project GHCR ROS base manifest digest is required')
        verify_base()
        if args.base_only:
            return
        hashes = definition_hashes(args.root)
        packages = installed_packages()
        required = required_packages(args.root, packages)
        if args.write:
            if not args.base_ref or not re.fullmatch(r'[0-9a-f]{40}', args.source_commit or ''):
                raise ValueError('base digest and full build-source commit are required')
            record = dict(schema=1, source='https://github.com/sp-zh/predictive-motion-research',
                          source_commit=args.source_commit, base_ref=args.base_ref,
                          platform='linux/amd64', ubuntu='24.04', ros='jazzy',
                          definitions=hashes, required_packages=required,
                          installed_packages=packages)
            args.metadata.mkdir(parents=True, exist_ok=True)
            (args.metadata / 'environment.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
        else:
            record = json.loads((args.metadata / 'environment.json').read_text())
            if record['schema'] != 1 or record['platform'] != 'linux/amd64' or record['ubuntu'] != '24.04' or record['ros'] != 'jazzy':
                raise ValueError('invalid environment metadata')
            if not re.fullmatch(BASE_PATTERN, record['base_ref']):
                raise ValueError('unlocked base image in metadata')
            if record['definitions'] != hashes:
                changed = [name for name in DEFINITIONS if record['definitions'].get(name) != hashes[name]]
                raise ValueError('environment definitions changed: ' + ', '.join(changed))
            if record['required_packages'] != required:
                raise ValueError('installed dependency versions differ from the image inventory')
        print('CI environment verified: linux/amd64, Ubuntu 24.04, ROS Jazzy; dependency definitions match')
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        parser.exit(1, f'dependency image needs updating (依赖镜像需要更新): {exc}\n')


if __name__ == '__main__':
    main()
