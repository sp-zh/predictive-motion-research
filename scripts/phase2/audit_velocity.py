"""Offline provenance check, not part of the C++ runtime controller."""
import sys
import xml.etree.ElementTree as ET
import yaml

robot = yaml.safe_load(open(sys.argv[1]))
experiment = yaml.safe_load(open(sys.argv[2]))
from pathlib import Path
urdf = Path(sys.argv[1]).parent / robot['urdf']
model = ET.parse(urdf).getroot()
names = robot['joint_names']
assert len(names) == len(experiment['velocity_limits'])
for name, configured in zip(names, experiment['velocity_limits']):
    actual = float(model.find(f"joint[@name='{name}']/limit").attrib['velocity'])
    assert actual == configured, (name, actual, configured)
print('OFFICIAL_URDF_VELOCITY_PROVENANCE_PASS')
