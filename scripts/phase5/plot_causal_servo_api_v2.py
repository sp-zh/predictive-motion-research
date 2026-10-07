#!/usr/bin/env python3
import json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/causal-soft-servo-cpp-v2';report=base/'report.json';r=json.loads(report.read_text());cases=r['branch_cases'];labels=['n1 interior','n1 positive saturation','n1 negative saturation','n7 interior','n7 positive saturation','n7 negative saturation','n1 exact positive threshold','n1 exact negative threshold'];values=np.array([[c['branches_2ms'][s][0] for s in (0,1)] for c in cases]);fig,ax=plt.subplots(figsize=(9,5.8),constrained_layout=True);ax.imshow(values,cmap=ListedColormap(['#467cac','#f0f0e9','#bb705c']),norm=BoundaryNorm([-1.5,-.5,.5,1.5],3),aspect='auto');ax.set_yticks(range(8),labels);ax.set_xticks([0,1],['First physical step (2 ms)','Second physical step (4 ms)'])
for i in range(8):
 for j in (0,1):ax.text(j,i,{-1:'−1: negative saturation',0:'0: interior',1:'+1: positive saturation'}[values[i,j]],ha='center',va='center',fontsize=10,color='white' if values[i,j] else '#303030')
ax.set_title('Frozen-root branches matched by isolated C++ v2\n78 invalid-entry checks rejected; original nominal trajectories unchanged',fontsize=12);fig.supxlabel('Exact thresholds use the declared saturation-side convention; ordinary derivative is not unique.',fontsize=9)
image=base/'phase5_causal_servo_api_v2_branches.png';fig.savefig(image,dpi=170);plt.close(fig);sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();(base/'phase5_causal_servo_api_v2_branches.json').write_text(json.dumps({'image_sha256':sha(image),'report_sha256':sha(report),'branch_packet_sha256':r['root_branch_packet_sha256'],'source':'scripts/phase5/plot_causal_servo_api_v2.py','units':'Discrete branch codes −1/0/+1, time milliseconds','scope':'Algebraic branch fixtures only; n7 vectors have uniform branch across7joints here; synthetic threshold boxes do not alter FR3 model domain; no plant/geometry/controller acceptance'},indent=2)+'\n');print(sha(image))
