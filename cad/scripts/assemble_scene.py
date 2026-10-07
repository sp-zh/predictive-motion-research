"""Attach project CAD to pinned upstream robot without modifying robot assets."""
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[2]
cfg=json.loads((root/'cad/source/inspection.json').read_text())
sim=json.loads((root/'cad/source/simulation.json').read_text())
if cfg['units']!='m':raise ValueError('CAD inputs must use metres')
for key in ['tool_mount_translation','tool_com_m','tool_diagonal_inertia_kg_m2']:
    if len(sim[key])!=3 or not all(math.isfinite(v) for v in sim[key]):raise ValueError('Invalid '+key)
inertia=sim['tool_diagonal_inertia_kg_m2']
if not math.isfinite(sim['tool_mass_kg']) or sim['tool_mass_kg']<=0:raise ValueError('Invalid tool mass')
if min(inertia)<=0 or any(sum(inertia)-v<=v for v in inertia):raise ValueError('Invalid principal inertia')
upstream=root/'.vendor/menagerie/franka_fr3'
out=root/'experiments/generated/inspection'
out.mkdir(parents=True,exist_ok=True)
def vec(values):return ' '.join(format(float(v),'.17g') for v in values)
robot=ET.parse(upstream/'fr3.xml')
robot.getroot().find('compiler').set('meshdir',str((upstream/'assets').resolve()))
parent=robot.find(f'.//body[@name="{sim["tool_mount_parent"]}"]')
if parent is None:raise ValueError('Configured tool mount parent absent')
mount=ET.SubElement(parent,'body',name='inspection_tool',pos=vec(sim['tool_mount_translation']))
ET.SubElement(mount,'inertial',pos=vec(sim['tool_com_m']),mass=str(sim['tool_mass_kg']),diaginertia=vec(sim['tool_diagonal_inertia_kg_m2']))
t=cfg['tool']
asset=robot.getroot().find('asset')
ET.SubElement(asset,'mesh',name='inspection_tool_visual',file=str((root/'cad/generated/tool_visual.stl').resolve()))
ET.SubElement(mount,'geom',name='inspection_tool_visual',type='mesh',mesh='inspection_tool_visual',group='2',contype='0',conaffinity='0',mass='0',rgba='0.3 0.5 0.7 1')
collision=[]
def geom(body,name,kind,pos,size):
    ET.SubElement(body,'geom',name=name,type=kind,pos=vec(pos),size=vec(size),group='3',mass='0',rgba='0.2 0.4 0.7 0.2')
    collision.append({'name':name,'body':body.attrib.get('name'),'type':kind,'local_position_m':pos,'size_m':size})
th=t['adapter_thickness']
geom(mount,'tool_adapter','cylinder',[0,0,th/2],[t['adapter_radius'],th/2])
geom(mount,'tool_shaft','cylinder',[0,0,th+t['length']/2],[t['shaft_radius'],t['length']/2])
bx,by,bz=t['sensor_body_dimensions']
geom(mount,'tool_sensor','box',[0,0,th+bz/2],[bx/2,by/2,bz/2])
geom(mount,'tool_tip','sphere',t['tcp_offset'],[t['tip_radius']])
if t['camera_bracket']:geom(mount,'tool_bracket','box',[bx/2+0.015,0,th+0.0175],[0.015,0.004,0.0175])
ET.SubElement(mount,'site',name='inspection_tcp',pos=vec(t['tcp_offset']),size='0.004',rgba='1 0.2 0.2 1')
world=robot.getroot().find('worldbody')
f=cfg['fixture']; ox,oy,oz=f['origin']; x,y,z=f['base_dimensions']
fixture=ET.SubElement(world,'body',name='inspection_fixture')
ET.SubElement(asset,'mesh',name='inspection_fixture_visual',file=str((root/'cad/generated/fixture_visual.stl').resolve()))
ET.SubElement(fixture,'geom',name='inspection_fixture_visual',type='mesh',mesh='inspection_fixture_visual',group='2',contype='0',conaffinity='0',mass='0',rgba='0.7 0.55 0.3 0.6')
geom(fixture,'fixture_base','box',[ox+x/2,oy+y/2,oz+z/2],[x/2,y/2,z/2])
w=f['wall_thickness']; h=f['wall_height']; channel=f['channel_width']
geom(fixture,'fixture_left','box',[ox+x/2,oy+(y-channel)/2-w/2,oz+z+h/2],[x/2,w/2,h/2])
geom(fixture,'fixture_right','box',[ox+x/2,oy+(y+channel)/2+w/2,oz+z+h/2],[x/2,w/2,h/2])
rx,ry,rz=f['rear_guard_dimensions']
geom(fixture,'fixture_rear','box',[ox+x-rx/2,oy+y+ry/2,oz+z+rz/2],[rx/2,ry/2,rz/2])
robot.write(out/'inspection_fr3.xml',encoding='unicode')
scene=ET.parse(upstream/'scene.xml')
scene.getroot().find('include').set('file','inspection_fr3.xml')
scene.write(out/'scene.xml',encoding='unicode')
manifest={'units':'m','status':'scene generated; load/TCP/contact checks pending','robot_commit':json.loads((root/'src/predictive_motion_description/manifests/fr3.json').read_text())['commit'],'simulation_assumptions':sim,'collision_primitives':collision,'inputs':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [upstream/'fr3.xml',upstream/'scene.xml',root/'cad/source/inspection.json',root/'cad/source/simulation.json',root/'cad/generated/tool_visual.stl',root/'cad/generated/fixture_visual.stl']}}
(out/'scene_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(out/'scene.xml')
