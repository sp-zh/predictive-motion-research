#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/public-coupled-servo-v2-reference-contract';r=json.loads((base/'report.json').read_text());value=r['synthetic_reference_contracts'][0]['B_s_inv'][0];ratios=np.array([.5,1.,2.]);fig,ax=plt.subplots(figsize=(8.5,4.6),constrained_layout=True);ax.plot(ratios,np.full(3,value),'o-',color='#3f788e',label='v2 standard positive-solref B');ax.plot(ratios,ratios*value,'s--',color='#b07352',label='Retained v1 formula outside fixed ratio1 scope');ax.axvline(1,color='#666666',ls=':',label='Actual frozen FR3 ratio');ax.set_xticks(ratios);ax.set_xlabel('Synthetic solref damping-ratio metadata');ax.set_ylabel('Friction reference B (s⁻¹)');ax.legend(fontsize=9);ax.set_title('Reference coefficient correction: actual robot parameters unchanged',fontsize=12);fig.supxlabel('19 existing TRAIN windows match v1 exactly. Formula tests do not establish new physical accuracy.',fontsize=9)
image=base/'phase5_public_coupled_reference_v2.png';fig.savefig(image,dpi=170);plt.close(fig);sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();(base/'phase5_public_coupled_reference_v2.json').write_text(json.dumps({'image_sha256':sha(image),'report_sha256':sha(base/'report.json'),'source':'scripts/phase5/plot_public_coupled_reference_v2.py','units':{'ratio':'dimensionless','B':'s^-1'},'scope':'Synthetic coefficient contract and selected originalTRAIN compatibility only; retained v1 actualratio1 remains unchanged; no new plant/controller/Phase5 result'},indent=2)+'\n');print(sha(image))
