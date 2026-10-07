#!/usr/bin/env python3
import json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/causal-soft-servo-cpp-v1';ref=p/'results/phase5/development/causal-soft-servo-cpp-reference-v1';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
actual=json.loads((base/'actual.json').read_text())['cases'][1];expected=json.loads((ref/'oracle.json').read_text())['cases'][1];h=actual['history'];t=np.array([x['time_s'] for x in h]);z=np.array([x['state'] for x in h]);e=np.array([x['state'] for x in expected['history']]);q0=expected['initial'][0];edges=np.cumsum(expected['mesh_s']);n=7
fig,axes=plt.subplots(1,2,figsize=(11,4.6),constrained_layout=True)
axes[0].plot(t,(z[:,0]-q0)*1e6,label='C++ predicted q, joint 0');axes[0].plot(t,(z[:,2*n]-q0)*1e6,label='C++ accepted target c, joint 0');axes[0].plot(t,(e[:,0]-q0)*1e6,'k--',lw=.8,label='Frozen root q reference');axes[0].set_ylabel('Position relative to initial q (microrad)');axes[0].legend(fontsize=8)
axes[1].plot(t,z[:,-2],label='C++ progress s');axes[1].plot(t,e[:,-2],'k--',lw=.8,label='Frozen root s reference');axes[1].set_ylabel('Progress s (dimensionless)');axes[1].legend(fontsize=8)
for ax in axes:
 for edge in edges:ax.axvline(edge,color='#888888',alpha=.16,lw=.6)
 ax.set_xlabel('Model forecast time (s)')
fig.suptitle('Causal local soft-servo model: 200 command cycles / 400 physical model steps',fontsize=12);axes[0].set_title('Frozen coefficients and original local domain',fontsize=10);axes[1].set_title('20 nonuniform cells; integer 4 ms periods',fontsize=10)
image=base/'phase5_causal_soft_servo_cpp_parity.png';fig.savefig(image,dpi=170);plt.close(fig)
(base/'phase5_causal_soft_servo_cpp_parity.json').write_text(json.dumps({'image_sha256':sha(image),'actual_sha256':sha(base/'actual.json'),'root_oracle_sha256':sha(ref/'oracle.json'),'model_sha256':sha(ref/'MODEL_SNAPSHOT.json'),'source':'scripts/phase5/plot_causal_soft_servo_parity.py','units':{'q_c':'microradians relative to initial physical q','s':'dimensionless','time':'seconds'},'scope':'Model algebra only, not actual plant or controller performance; no geometry change'},indent=2)+'\n');print(sha(image))
