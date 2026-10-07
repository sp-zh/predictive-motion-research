"""Verify persistence and SI mesh exports in a separate FreeCAD process."""
import json
import os
from pathlib import Path
import FreeCAD as App
import Mesh
import Part
import generate_inspection  # Provides the saved FeaturePython proxy types.

root = Path(os.environ['PM_PROJECT_ROOT'])
output = Path(os.environ.get('PM_CAD_OUTPUT', root/'cad/generated'))
doc = App.openDocument(str(output/'inspection.FCStd'))
tool = doc.getObject('InspectionTool')
assert isinstance(tool.Proxy, generate_inspection.InspectionTool), 'Lost tool proxy'
assert isinstance(doc.getObject('InspectionFixture').Proxy, generate_inspection.InspectionFixture), 'Lost fixture proxy'
z_before = tool.Shape.BoundBox.ZMax
tool.Length = tool.Length.Value + 20
doc.recompute()
assert tool.Shape.BoundBox.ZMax > z_before, 'Saved tool is not parametric'
for name in ['tool', 'fixture']:
    shape = Part.read(str(output/(name+'.step')))
    assert shape.isValid() and shape.Volume > 0, 'Invalid STEP roundtrip'
    mesh = Mesh.Mesh(str(output/(name+'_visual.stl')))
    assert abs(mesh.BoundBox.ZMax*1000-shape.BoundBox.ZMax) < 0.5, 'Mesh scale or STEP bounds mismatch'
App.closeDocument(doc.Name)
(output/'persistence_evidence.json').write_text(json.dumps({'fresh_process_proxy_restore':True,'parameter_recompute':True,'step_roundtrip':True,'stl_units_m':True},indent=2)+'\n')
print('CAD_PERSISTENCE_AND_UNITS_PASS')
