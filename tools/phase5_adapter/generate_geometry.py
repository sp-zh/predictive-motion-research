"""Separate Phase5 conservative cover; original Phase4 assets are never modified."""
from pathlib import Path
import json,math,hashlib,xml.etree.ElementTree as ET
import numpy as np
r=Path(__file__).resolve().parents[2];base=r/'experiments/generated/phase4';out=r/'experiments/generated/phase5';out.mkdir(exist_ok=True)
config=json.loads((base/'geometry.json').read_text());cell=.008;config['cover_cell_m']=cell
tree=ET.parse(base/'servo_arm.urdf').getroot();parents={}
for joint in tree.findall('joint'):
 child=joint.find('child').attrib['link'];parent=joint.find('parent').attrib['link'];origin=joint.find('origin');offset=np.linalg.norm([float(x) for x in origin.attrib.get('xyz','0 0 0').split()]) if origin is not None else 0.;parents[child]=(parent,float(offset))
def chain(frame):
 total=0.;seen=set()
 while frame in parents:
  assert frame not in seen;seen.add(frame);frame,length=parents[frame];total+=length
 return total
bounds=[];cover_count=0
for asset in config['arm']:
 lines=Path(asset['file']).read_text().splitlines();vertices=int(lines[0].split()[0]);radius=max(np.linalg.norm([float(x) for x in line.split()]) for line in lines[1:1+vertices]);bounds.append(chain(asset['frame'])+radius)
primitive_proofs=[]
for p in config['primitives']:
 if p['body']!='inspection_tool':continue
 size=p['size_m'];center=float(np.linalg.norm(p['local_position_m']))
 if p['type']=='box':
  counts=[max(1,math.ceil(2*h/cell)) for h in size];cell_radius=float(np.linalg.norm([h/n for h,n in zip(size,counts)]));radius=center+float(np.linalg.norm(size))+cell_radius;count=math.prod(counts);inflation=cell_radius
 elif p['type']=='cylinder':
  count=max(1,math.ceil(2*size[1]/cell));half_slice=size[1]/count;radius=max(center+math.hypot(*size),center+size[1]-half_slice+math.hypot(size[0],half_slice));inflation=math.hypot(size[0],half_slice)-size[0]
 else:count=1;radius=center+size[0];inflation=0.
 bounds.append(chain(config['tool_frame'])+radius);cover_count+=count;primitive_proofs.append({'name':p['name'],'cover_spheres':count,'conservative_radial_inflation_m':inflation,'global_point_bound_m':chain(config['tool_frame'])+radius})
config['motion_radius_bound_m']=float(max(bounds)+1e-9);config['phase4_geometry_sha256']=hashlib.sha256((base/'geometry.json').read_bytes()).hexdigest();config['scope']='Independent Phase5 cover encloses the same physical primitives; no set ordering against the Phase4 cover is assumed; all true primitives and arm hulls retained'
(out/'geometry.json').write_text(json.dumps(config,indent=2)+'\n')
(out/'cover_proof.json').write_text(json.dumps({'cell_m':cell,'total_spheres':cover_count,'primitive_proofs':primitive_proofs,'point_radius_bound_m':config['motion_radius_bound_m'],'proof':'Each box cell circumsphere contains its full cell; each cylinder axial-slice sphere contains its full slice including end caps. All original components retained. Point lever bound sums all chain origin lengths plus full cover-point radius.','phase4_geometry_sha256':config['phase4_geometry_sha256']},indent=2)+'\n')
print(json.dumps({'spheres':cover_count,'radius':config['motion_radius_bound_m']}))
