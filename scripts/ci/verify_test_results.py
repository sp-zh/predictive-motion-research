#!/usr/bin/env python3
"""Audit native GTest XML only; CTest/colcon wrapper counts are not added."""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def audit(root):
    expected = {'plant_test': 4, 'kinematics_test': 7, 'ik_test': 7, 'nullspace_test': 6}
    found = {}
    names = []
    for path in (root / 'build').glob('**/test_results/**/*.gtest.xml'):
        key = path.name.removesuffix('.gtest.xml')
        if key in found:
            raise ValueError(f'duplicate native report: {key}')
        cases = list(ET.parse(path).getroot().iter('testcase'))
        for case in cases:
            if (case.find('failure') is not None or case.find('error') is not None
                    or case.find('skipped') is not None or case.get('status') == 'notrun'
                    or case.get('result') in ('skipped', 'suppressed')):
                raise ValueError(f'failed/skipped test: {case.attrib}')
            names.append(case.get('classname', '') + '.' + case.get('name', ''))
        found[key] = len(cases)
    # Matches the current CI build options, not all optional research targets.
    if found != expected:
        raise ValueError(f'baseline test inventory changed: expected {expected}, got {found}; review explicitly')
    log = (root / 'results/ci-image/full-test.log').read_text()
    if not re.search(r'Ran 8 tests in [^\n]+\n\s*\n?OK\b', log):
        raise ValueError('all 8 paired-statistics tests must run and pass')
    for marker in ['NUMERICAL_PASS samples=2000 seed=42 h=1e-6',
                   'INSTALLED_EIGEN_ONLY_CONSUMER_PASS', 'INSTALLED_EIGEN_ONLY_NULLSPACE_CONSUMER_PASS']:
        if marker not in log:
            raise ValueError(f'missing integration/numerical evidence: {marker}')
    return dict(native_gtest_cases=names, native_gtest_count=sum(found.values()),
                paired_statistics_count=8, skipped=0,
                integration_scope='unchanged scripts/ci.sh; its zero exit is required separately')


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[2]
    try:
        result = audit(root)
        (root / 'results/ci-image/test-inventory.json').write_text(json.dumps(result, indent=2) + '\n')
        print('Verified 24 native GTest cases + 8 statistics tests; no skipped cases')
    except (OSError, ValueError, ET.ParseError) as exc:
        raise SystemExit(f'incomplete CI validation: {exc}') from exc
