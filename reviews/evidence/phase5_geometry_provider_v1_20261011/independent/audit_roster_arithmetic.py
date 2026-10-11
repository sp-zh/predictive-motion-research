"""Saved normalized geometry configuration roster arithmetic only; no Scene/FK."""
from pathlib import Path
import json,math,hashlib
OUT=Path(__file__).resolve().parent
source=Path('/private/tmp/phase5_geometry_provider_checkpoint_v1_20261011/READONLY_GEOMETRY_CONFIG_SNAPSHOT.json')
blob=source.read_bytes();g=json.loads(blob)
objects=[{'name':v['frame'],'frame':v['frame'],'category':'arm','arm_index':k} for k,v in enumerate(g['arm'])];cover=0;cell=g['cover_cell_m']
for p in g['primitives']:
 tool=p['body']=='inspection_tool';objects.append({'name':p['name'],'frame':g['tool_frame'] if tool else 'world','category':'tool' if tool else 'fixture','arm_index':-1})
 if tool:
  if p['type']=='sphere':cover+=1
  elif p['type']=='cylinder':cover+=max(1,math.ceil(2*p['size_m'][1]/cell))
  else:cover+=math.prod(max(1,math.ceil(2*h/cell)) for h in p['size_m'])
objects.append({'name':'floor','frame':'world','category':'floor','arm_index':-1})
def excluded(a,b):
 if a['category']==b['category'] and a['category'] in ('tool','fixture'):return True
 if a['category']==b['category']=='arm' and abs(a['arm_index']-b['arm_index'])<=1:return True
 if (a['arm_index']==0 and b['category']=='floor') or (b['arm_index']==0 and a['category']=='floor'):return True
 if (a['arm_index']==len(g['arm'])-1 and b['category']=='tool') or (b['arm_index']==len(g['arm'])-1 and a['category']=='tool'):return True
 return a['frame']==b['frame']=='world'
true=sum(not excluded(a,b) for i,a in enumerate(objects) for b in objects[i+1:]);env=sum(o['category'] in ('fixture','floor') for o in objects);cov=cover*env
assert true==120 and cov==8915 and true+cov==9035
result={'normalized_config_source_sha256':hashlib.sha256(blob).hexdigest(),'normalized_config_object_count':len(objects),'tool_cover_spheres':cover,'environment_objects':env,'true_queries_per_scene':true,'cover_queries_per_scene':cov,'total_queries_per_scene':true+cov,'probes':9,'total_scenes':1200+9*7*2,'total_primitive_queries':(1200+9*7*2)*(true+cov),'scope':'Independent primitive roster arithmetic from saved normalized configuration only, not Scene/FK query or exact raw-YAML readback.'}
assert source.read_bytes()==blob
(OUT/'ROSTER_ARITHMETIC.json').write_text(json.dumps(result,indent=2)+'\n')
