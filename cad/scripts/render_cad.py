"""Render actual exported SI meshes; no robot feasibility implied."""
import json
import struct
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

root = Path(__file__).resolve().parents[2]
def triangles(path):
    data = path.read_bytes()
    count = struct.unpack_from('<I', data, 80)[0]
    if len(data) != 84+50*count:
        raise ValueError('Expected binary STL')
    return np.array([struct.unpack_from('<9f', data, 84+50*i+12) for i in range(count)]).reshape(-1,3,3)

fig = plt.figure(figsize=(11,5),layout='constrained')
for idx,name in enumerate(['tool','fixture']):
    ax = fig.add_subplot(1,2,idx+1,projection='3d')
    verts = triangles(root/'cad/generated'/f'{name}_visual.stl')
    ax.add_collection3d(Poly3DCollection(verts,facecolor='#6c95b4',edgecolor='none',alpha=0.8 if name=='tool' else 0.3))
    xyz = verts.reshape(-1,3)
    lo,hi = xyz.min(axis=0),xyz.max(axis=0)
    mid = (lo+hi)/2
    width = (hi-lo).max()/2*1.1
    ax.set_xlim(mid[0]-width,mid[0]+width)
    ax.set_ylim(mid[1]-width,mid[1]+width)
    ax.set_zlim(mid[2]-width,mid[2]+width)
    ax.set_box_aspect((1,1,1))
    ax.view_init(elev=22,azim=-55)
    ax.set(xlabel='x (m)',ylabel='y (m)',zlabel='z (m)',title='Local tool geometry' if name=='tool' else 'World fixture and inspection line')
    if name=='fixture':
        path=json.loads((root/'cad/generated/inspection_path.json').read_text())
        line=np.array([path['start'],path['end']])
        ax.plot(*line.T,color='#d85c32',linewidth=3)
fig.suptitle('Parametric CAD exports — path orientation and robot feasibility pending',fontsize=12)
(root/'figures').mkdir(exist_ok=True)
fig.savefig(root/'figures/inspection_cad.png',dpi=150)
(root/'cad/generated/render_versions.json').write_text(json.dumps({'matplotlib':matplotlib.__version__,'numpy':np.__version__},indent=2)+'\n')
