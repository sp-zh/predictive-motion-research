"""Run inside locked FreeCAD Python runtime; create parametric CAD and SI meshes."""
import hashlib
import json
import math
import os
from pathlib import Path

import FreeCAD as App
import Part
import MeshPart


class InspectionTool:
    def __init__(self, feature):
        feature.Proxy = self

    def execute(self, feature):
        length = feature.Length.Value
        radius = feature.ShaftRadius.Value
        thickness = feature.AdapterThickness.Value
        adapter = Part.makeCylinder(feature.AdapterRadius.Value, thickness)
        for angle in [0, math.pi / 2, math.pi, 3 * math.pi / 2]:
            center = App.Vector(feature.BoltCircleRadius.Value * math.cos(angle), feature.BoltCircleRadius.Value * math.sin(angle), 0)
            adapter = adapter.cut(Part.makeCylinder(feature.BoltHoleRadius.Value, thickness, center))
        shaft = Part.makeCylinder(radius, length, App.Vector(0, 0, thickness))
        body = Part.makeBox(feature.BodyX.Value, feature.BodyY.Value, feature.BodyZ.Value, App.Vector(-feature.BodyX.Value / 2, -feature.BodyY.Value / 2, thickness))
        tip = Part.makeSphere(feature.TipRadius.Value, feature.TCPOffset)
        parts = [adapter, shaft, body, tip]
        if feature.CameraBracket:
            parts.append(Part.makeBox(30, 8, 35, App.Vector(feature.BodyX.Value / 2, -4, thickness)))
        feature.Shape = Part.makeCompound(parts)

    def dumps(self):
        return None

    def loads(self, state):
        return None


class InspectionFixture:
    def __init__(self, feature):
        feature.Proxy = self

    def execute(self, feature):
        origin = feature.Origin
        base = Part.makeBox(feature.BaseX.Value, feature.BaseY.Value, feature.BaseZ.Value, origin)
        wall_z = origin.z + feature.BaseZ.Value
        left_y = origin.y + (feature.BaseY.Value - feature.ChannelWidth.Value) / 2 - feature.WallThickness.Value
        right_y = origin.y + (feature.BaseY.Value + feature.ChannelWidth.Value) / 2
        left = Part.makeBox(feature.BaseX.Value, feature.WallThickness.Value, feature.WallHeight.Value, App.Vector(origin.x, left_y, wall_z))
        right = Part.makeBox(feature.BaseX.Value, feature.WallThickness.Value, feature.WallHeight.Value, App.Vector(origin.x, right_y, wall_z))
        rear = Part.makeBox(feature.RearX.Value, feature.RearY.Value, feature.RearZ.Value, App.Vector(origin.x + feature.BaseX.Value - feature.RearX.Value, origin.y + feature.BaseY.Value, wall_z))
        feature.Shape = Part.makeCompound([base, left, right, rear])

    def dumps(self):
        return None

    def loads(self, state):
        return None


def length_property(obj, name, value):
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f'{name} must be finite and positive')
    obj.addProperty('App::PropertyLength', name, 'Parameters')
    setattr(obj, name, value * 1000)


def export_mesh(shape, path, deflection_mm, angular_deflection=0.2):
    if not shape.isValid() or shape.Volume <= 0:
        raise ValueError('Invalid or empty exported shape')
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=deflection_mm, AngularDeflection=angular_deflection, Relative=False)
    if mesh.CountFacets <= 0:
        raise ValueError('Empty exported mesh')
    scale = App.Matrix()
    scale.scale(0.001, 0.001, 0.001)
    mesh.transform(scale)
    mesh.write(str(path))
    return {'facets': mesh.CountFacets, 'bounds_m': [mesh.BoundBox.XMin, mesh.BoundBox.YMin, mesh.BoundBox.ZMin, mesh.BoundBox.XMax, mesh.BoundBox.YMax, mesh.BoundBox.ZMax]}


def generate(config_file, output):
    config = json.loads(config_file.read_text())
    if config['units'] != 'm':
        raise ValueError('CAD inputs must use metres')
    tool_cfg, fixture_cfg = config['tool'], config['fixture']
    if tool_cfg['adapter_radius'] <= tool_cfg['bolt_circle_radius'] + tool_cfg['bolt_hole_radius']:
        raise ValueError('Bolt holes must lie inside adapter perimeter')
    if fixture_cfg['channel_width'] + 2 * fixture_cfg['wall_thickness'] >= fixture_cfg['base_dimensions'][1]:
        raise ValueError('Fixture channel and walls do not fit base')
    if len(tool_cfg['tcp_offset']) != 3 or not all(math.isfinite(v) for v in tool_cfg['tcp_offset']):
        raise ValueError('Invalid TCP offset')
    output.mkdir(parents=True, exist_ok=True)
    doc = App.newDocument('InspectionAssembly')
    tool = doc.addObject('Part::FeaturePython', 'InspectionTool')
    for name, key in [('Length','length'),('ShaftRadius','shaft_radius'),('AdapterRadius','adapter_radius'),('AdapterThickness','adapter_thickness'),('BoltCircleRadius','bolt_circle_radius'),('BoltHoleRadius','bolt_hole_radius'),('TipRadius','tip_radius')]:
        length_property(tool, name, tool_cfg[key])
    for name, value in zip(['BodyX','BodyY','BodyZ'], tool_cfg['sensor_body_dimensions']):
        length_property(tool, name, value)
    tool.addProperty('App::PropertyVector', 'TCPOffset', 'Parameters')
    tool.TCPOffset = App.Vector(*[v * 1000 for v in tool_cfg['tcp_offset']])
    tool.addProperty('App::PropertyBool','CameraBracket','Parameters')
    tool.CameraBracket = tool_cfg['camera_bracket']
    InspectionTool(tool)
    fixture = doc.addObject('Part::FeaturePython', 'InspectionFixture')
    for name, value in zip(['BaseX','BaseY','BaseZ'], fixture_cfg['base_dimensions']):
        length_property(fixture,name,value)
    for name, key in [('ChannelWidth','channel_width'),('WallThickness','wall_thickness'),('WallHeight','wall_height')]:
        length_property(fixture,name,fixture_cfg[key])
    for name, value in zip(['RearX','RearY','RearZ'],fixture_cfg['rear_guard_dimensions']):
        length_property(fixture,name,value)
    fixture.addProperty('App::PropertyVector','Origin','Parameters')
    fixture.Origin=App.Vector(*[v * 1000 for v in fixture_cfg['origin']])
    InspectionFixture(fixture)
    doc.recompute()
    if not tool.Shape.isValid() or not fixture.Shape.isValid():
        raise ValueError('Invalid CAD shape')
    if tool.Shape.Volume <= 0 or fixture.Shape.Volume <= 0:
        raise ValueError('CAD parts must have positive volume')
    evidence = {'freecad_version': App.Version(), 'input_sha256': hashlib.sha256(config_file.read_bytes()).hexdigest(), 'cad_units': 'mm', 'mesh_units':'m', 'objects':{}}
    for name, obj in [('tool',tool),('fixture',fixture)]:
        Part.export([obj],str(output/(name+'.step')))
        collision_shape = obj.Shape
        if name == 'tool':
            # Fill bolt holes for a conservative, simpler collision adapter.
            collision_shape = obj.Shape.fuse(Part.makeCylinder(obj.AdapterRadius.Value,obj.AdapterThickness.Value)).removeSplitter()
        evidence['objects'][name]={'volume_mm3':obj.Shape.Volume,'visual':export_mesh(obj.Shape,output/(name+'_visual.stl'),0.2),'collision':export_mesh(collision_shape,output/(name+'_collision.stl'),1.0,0.5)}
    doc.saveAs(str(output/'inspection.FCStd'))
    # Recompute after a parameter change proves FeaturePython parametric behavior.
    original_bounds = tool.Shape.BoundBox.ZMax
    original_length = tool.Length.Value
    tool.Length = original_length + 20
    doc.recompute()
    if tool.Shape.BoundBox.ZMax <= original_bounds:
        raise ValueError('Length change did not recompute tool geometry')
    tool.Length = original_length
    doc.recompute()
    doc.saveAs(str(output/'inspection.FCStd'))
    center_y=fixture_cfg['origin'][1]+fixture_cfg['base_dimensions'][1]/2
    path={'units':'m','frame':'world','type':'line','start':[fixture_cfg['origin'][0]+0.02,center_y,fixture_cfg['origin'][2]+fixture_cfg['base_dimensions'][2]+fixture_cfg['inspection_height']],'end':[fixture_cfg['origin'][0]+fixture_cfg['base_dimensions'][0]-0.02,center_y,fixture_cfg['origin'][2]+fixture_cfg['base_dimensions'][2]+fixture_cfg['inspection_height']],'orientation_definition':'pending feasible fixed tool orientation at kinematics validation; not a benchmark yet'}
    (output/'inspection_path.json').write_text(json.dumps(path,indent=2)+'\n')
    evidence['parametric_recompute_test']=True
    export_names=['fixture.step','tool.step','inspection.FCStd','inspection_path.json','fixture_visual.stl','fixture_collision.stl','tool_visual.stl','tool_collision.stl']
    evidence['exports']={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in export_names}
    (output/'cad_evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))
    App.closeDocument(doc.Name)


if __name__ == '__main__':
    project = Path(os.environ.get('PM_PROJECT_ROOT', Path(__file__).resolve().parents[2]))
    config_file = Path(os.environ.get('PM_CAD_CONFIG', project/'cad/source/inspection.json'))
    output = Path(os.environ.get('PM_CAD_OUTPUT', project/'cad/generated'))
    generate(config_file,output)
