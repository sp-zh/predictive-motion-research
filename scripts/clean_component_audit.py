#!/usr/bin/env python3
"""Build an exported source snapshot in rootless Podman and retain evidence.

This executes the component CI recipe. It cannot close the final research
reproducibility audit, which additionally requires benchmark/metrics/figures.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET


def now():
    return datetime.now(timezone.utc).isoformat()


def unpack(bundle, destination):
    packed = bundle / 'source.tar.gz'
    digest = hashlib.sha256(packed.read_bytes()).hexdigest()
    if (bundle / 'READY').read_text().strip() != digest:
        raise ValueError('READY does not identify the complete archive')
    expected = (bundle / 'source.tar.gz.sha256').read_text().split()
    if expected != [digest, 'source.tar.gz']:
        raise ValueError('Archive hash manifest mismatch')
    with tarfile.open(packed) as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive member')
        for member in members:
            path = PurePosixPath(member.name)
            if (not member.isfile() or path.is_absolute() or '..' in path.parts
                    or not path.parts or path.parts[0] != 'predictive_motion'
                    or member.size > 100 * 1024 * 1024):
                raise ValueError('Unsafe source archive member: ' + member.name)
        manifest = archive.extractfile('predictive_motion/SOURCE.sha256').read()
        if manifest != (bundle / 'SOURCE.sha256').read_bytes():
            raise ValueError('Internal and external source manifests differ')
        hashes = {}
        for line in manifest.decode().splitlines():
            value, name = line.split('  ', 1)
            if name in hashes:
                raise ValueError('Duplicate manifest path')
            hashes[name] = value
        if set(names) != {'predictive_motion/' + name for name in hashes} | {'predictive_motion/SOURCE.sha256'}:
            raise ValueError('Archive includes unmanifested files')
        for member in members:
            content = archive.extractfile(member).read()
            relative = member.name[len('predictive_motion/'):]
            if relative != 'SOURCE.sha256' and hashlib.sha256(content).hexdigest() != hashes[relative]:
                raise ValueError('Source hash mismatch: ' + relative)
            path = destination.joinpath(*PurePosixPath(member.name).parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            path.chmod(0o755 if member.mode & 0o111 else 0o644)
    return digest


def collect_gtest_evidence(output, container, run):
    """Copy existing test results from the reviewed image; do not rerun tests."""
    counts, files = {}, {}
    for package in ['predictive_motion_sim', 'predictive_motion_kinematics', 'predictive_motion_control']:
        target = output / 'test-results' / package
        target.parent.mkdir(parents=True, exist_ok=True)
        run(['podman', 'cp', container + ':/workspaces/predictive_motion/build/'
             + package + '/test_results', str(target)], 'copy-' + package + '-tests.log')
        count = 0
        for path in sorted(target.rglob('*.gtest.xml')):
            tree = ET.parse(path)
            cases = list(tree.iter('testcase'))
            if any(case.find('failure') is not None or case.find('error') is not None
                   or case.find('skipped') is not None for case in cases):
                raise RuntimeError('Failed or skipped GTest case in ' + str(path))
            count += len(cases)
            files[path.relative_to(output).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        if not count:
            raise RuntimeError('No actual GTest cases retained for ' + package)
        counts[package] = count
    summary = {'actual_gtest_cases_by_package': counts,
               'actual_gtest_cases_total': sum(counts.values()), 'xml_sha256': files,
               'scope': 'existing container build test artifacts; no additional execution'}
    (output / 'unit-test-evidence.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True,
                        help='New native Linux directory; refuses existing paths')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {'started_utc': now(), 'scope': 'component CI only; final research reproducibility pending',
              'status': 'IN_PROGRESS', 'commands': []}
    container = None

    def run(argv, log_name, capture=False):
        record = {'argv': argv, 'started_utc': now(), 'log': log_name}
        report['commands'].append(record)
        with (output / log_name).open('w') as stream:
            if capture:
                process = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stream.write(process.stdout)
                if process.stderr:
                    record['stderr_log'] = log_name + '.stderr.log'
                    (output / record['stderr_log']).write_text(process.stderr)
            else:
                process = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT)
        record.update(exit_code=process.returncode, ended_utc=now())
        if process.returncode:
            raise RuntimeError('Command failed; see ' + log_name)
        return process.stdout.strip() if capture else None

    try:
        if not shutil.which('podman'):
            raise RuntimeError('Podman unavailable; no container build executed')
        if os.getuid() == 0:
            raise RuntimeError('Run as the ordinary project user for a rootless audit')
        report['source_archive_sha256'] = unpack(args.bundle.resolve(), output / 'context')
        info_text = run(['podman', 'info', '--format=json'], 'podman-info.json', capture=True)
        if not json.loads(info_text)['host']['security']['rootless']:
            raise RuntimeError('Podman is not running rootless')
        context = output / 'context/predictive_motion'
        image = 'localhost/predictive-motion-component:' + report['source_archive_sha256'][:16]
        report['image_tag'] = image
        run(['podman', 'build', '--platform=linux/amd64', '--no-cache',
             '-f', str(context / 'docker/Dockerfile'), '-t', image, str(context)], 'container-build.log')
        run(['podman', 'image', 'inspect', image], 'image-inspect.json')
        run(['podman', 'run', '--rm', '--network=none', image, 'bash', '-c',
             'cat /etc/os-release; uname -a; dpkg-query -W; c++ --version; cmake --version'],
            'container-environment.log')
        container = run(['podman', 'create', image], 'container-create.log', capture=True)
        run(['podman', 'cp', container + ':/workspaces/predictive_motion/results',
             str(output / 'component-results')], 'copy-evidence.log')
        report['actual_gtest_cases'] = collect_gtest_evidence(output, container, run)['actual_gtest_cases_total']
        report['status'] = 'COMPONENT_BUILD_PASS_FINAL_AUDIT_PENDING'
    except Exception as error:
        report.update(status='FAIL', error=str(error))
    finally:
        if container:
            try:
                run(['podman', 'rm', container], 'container-cleanup.log')
            except Exception as error:
                report.update(status='FAIL', cleanup_error=str(error))
        report['ended_utc'] = now()
        (output / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'COMPONENT_BUILD_PASS_FINAL_AUDIT_PENDING' else 1


if __name__ == '__main__':
    raise SystemExit(main())
