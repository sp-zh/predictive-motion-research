"""Offline common-model assets; runtime only reads config/model/measured joints."""
from pathlib import Path
import struct, json, hashlib, itertools, sys
import numpy as np
from scipy.spatial import ConvexHull
import xml.etree.ElementTree as ET
root = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[2]
out = root/'experiments/generated/phase4'
out.mkdir(exist_ok=True)
manifest = json.loads((root/'experiments/generated/inspection/scene_manifest.json').read_text())
arm = ET.parse(root/'models/fr3/fr3_arm.urdf')
robot = arm.getroot()
for link in robot.findall('link'):
    for elem in list(link):
        if elem.tag in ('collision','visual'): link.remove(elem)
assets = []
for i in range(8):
    source = root/f'.vendor/menagerie/franka_fr3/assets/link{i}.stl'
    raw = source.read_bytes(); count = struct.unpack_from('<I',raw,80)[0]
    if len(raw) != 84+50*count: raise ValueError('Expected binary STL')
    verts = np.array([struct.unpack_from('<9f',raw,84+50*j+12) for j in range(count)]).reshape(-1,3)
    verts = np.unique(verts,axis=0)
    hull = ConvexHull(verts)
    faces=[]
    for tri,equation in zip(hull.simplices,hull.equations):
        tri=tri.copy()
        if np.dot(np.cross(verts[tri[1]]-verts[tri[0]],verts[tri[2]]-verts[tri[0]]),equation[:3])<0:
            tri[[1,2]]=tri[[2,1]]
        faces.append(tri)
    path=out/f'link{i}_hull.txt'
    with path.open('w') as f:
        f.write(f'{len(verts)} {len(faces)}\n')
        for v in verts: f.write(' '.join(format(float(x),'.17g') for x in v)+'\n')
        for tri in faces: f.write(' '.join(str(int(x)) for x in tri)+'\n')
    stl=out/f'link{i}_hull.stl'
    with stl.open('wb') as f:
        f.write(b'Phase4 common Menagerie convex hull'.ljust(80,b'\0')); f.write(struct.pack('<I',len(faces)))
        for tri in faces:
            v=verts[tri]; n=np.cross(v[1]-v[0],v[2]-v[0]); n/=np.linalg.norm(n)
            f.write(struct.pack('<12fH',*n,*v.ravel(),0))
    link=robot.find(f"link[@name='fr3_link{i}']")
    ET.SubElement(ET.SubElement(ET.SubElement(link,'collision'),'geometry'),'mesh',filename=stl.as_uri())
    # All original vertices belong to the generated hull; no source simplification.
    containment=np.max(verts@hull.equations[:,:3].T+hull.equations[:,3])
    assets.append({'frame':f'fr3_link{i}','file':str(path),'source_sha256':hashlib.sha256(raw).hexdigest(),
                   'generated_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                   'max_vertex_containment_error_m':float(containment),'vertices':len(verts),'triangles':len(faces)})
tool=ET.SubElement(robot,'link',name='inspection_tool')
joint=ET.SubElement(robot,'joint',name='inspection_tool_joint',type='fixed')
ET.SubElement(joint,'parent',link='fr3_link8'); ET.SubElement(joint,'child',link='inspection_tool')
ET.SubElement(joint,'origin',xyz='0 0 0',rpy='0 0 0')
for p in manifest['collision_primitives']:
    if p['body']!='inspection_tool':continue
    c=ET.SubElement(tool,'collision',name=p['name'])
    ET.SubElement(c,'origin',xyz=' '.join(map(str,p['local_position_m'])),rpy='0 0 0')
    g=ET.SubElement(c,'geometry'); size=p['size_m']
    if p['type']=='box': ET.SubElement(g,'box',size=' '.join(str(2*x) for x in size))
    elif p['type']=='cylinder': ET.SubElement(g,'cylinder',radius=str(size[0]),length=str(2*size[1]))
    else: ET.SubElement(g,'sphere',radius=str(size[0]))
ET.SubElement(robot,'link',name='inspection_tcp')
j=ET.SubElement(robot,'joint',name='inspection_tcp_joint',type='fixed')
ET.SubElement(j,'parent',link='inspection_tool');ET.SubElement(j,'child',link='inspection_tcp')
ET.SubElement(j,'origin',xyz='0 0 .32',rpy='0 0 0')
arm.write(out/'servo_arm.urdf',encoding='unicode',xml_declaration=True)
srdf=ET.Element('robot',name='fr3')
group=ET.SubElement(srdf,'group',name='arm')
ET.SubElement(group,'chain',base_link='fr3_link0',tip_link='inspection_tcp')
for i in range(7):
    ET.SubElement(srdf,'disable_collisions',link1=f'fr3_link{i}',link2=f'fr3_link{i+1}',reason='Adjacent')
ET.SubElement(srdf,'disable_collisions',link1='fr3_link7',link2='inspection_tool',reason='Fixed assembly')
ET.ElementTree(srdf).write(out/'servo_arm.srdf',encoding='unicode',xml_declaration=True)
parents={j.find('child').get('link'):(j.find('parent').get('link'),np.linalg.norm(np.array(list(map(float,j.find('origin').get('xyz','0 0 0').split()))))) for j in robot.findall('joint')}
def chain_length(frame):
    length=0.0
    while frame in parents:
        frame,offset=parents[frame];length+=offset
    return length
reach_bounds=[]
for asset in assets:
    f=(out/f"link{assets.index(asset)}_hull.txt").read_text().splitlines()[1:1+asset['vertices']]
    radius=max(np.linalg.norm(list(map(float,line.split()))) for line in f)
    reach_bounds.append(chain_length(asset['frame'])+radius)
for p in manifest['collision_primitives']:
    if p['body']=='inspection_tool':
        s=p['size_m']; center_radius=np.linalg.norm(p['local_position_m'])
        if p['type']=='box':
            half=np.array(s);counts=np.maximum(1,np.ceil(2*half/.004).astype(int));cell_radius=np.linalg.norm(half/counts)
            radius_bound=center_radius+np.linalg.norm(half)+cell_radius
        elif p['type']=='cylinder':
            count=max(1,int(np.ceil(2*s[1]/.004)));half_width=s[1]/count
            physical=center_radius+np.hypot(*s)
            cover=center_radius+s[1]-half_width+np.hypot(s[0],half_width)
            radius_bound=max(physical,cover)
        else:radius_bound=center_radius+s[0]
        reach_bounds.append(chain_length('inspection_tool')+radius_bound)
motion_radius=float(max(reach_bounds)+1e-9)
config={'schema':1,'arm':assets,'primitives':manifest['collision_primitives'],
        'tool_frame':'fr3_link8','floor_z':0.0,'cover_cell_m':.004,
        'cover_method':'box intersecting cells with circumspheres; cylinder axial slice circumspheres; tip exact sphere',
        'motion_radius_bound_m':motion_radius,'reach_bound_proof':'sum of URDF fixed/joint origin lengths plus local point radius, including cell cover inflation; any joint-to-point lever <= this global chain bound',
        'exclusions':['adjacent arm links only','fr3_link0 versus floor: intentional base mounting',
                      'tool versus fr3_link7: rigid mount','intra-tool and intra-fixture: fixed compounds'],
        'source_manifest_sha256':hashlib.sha256((root/'experiments/generated/inspection/scene_manifest.json').read_bytes()).hexdigest()}
(out/'geometry.json').write_text(json.dumps(config,indent=2)+'\n')
robotcfg={'urdf':str(root/'models/fr3/fr3_arm.urdf'),
          'joint_names':[f'fr3_joint{i}' for i in range(1,8)],'fixed_joint_positions':{},
          'tcp_parent_frame':'fr3_link8','flange_T_tcp':{'translation':[0,0,.32],'quaternion_xyzw':[0,0,0,1]},
          'world_T_base':{'translation':[0,0,0],'quaternion_xyzw':[0,0,0,1]}}
import yaml
robotcfg.pop('flange_T_tcp');robotcfg.pop('world_T_base')
robotcfg.update(tcp_translation=[0,0,.32],tcp_quaternion_xyzw=[0,0,0,1],
                base_translation=[0,0,0],base_quaternion_xyzw=[0,0,0,1])
(out/'robot.yaml').write_text(yaml.safe_dump(robotcfg))
