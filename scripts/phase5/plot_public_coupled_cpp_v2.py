#!/usr/bin/env python3
"""Plot executed fixed-input parity; presentation diagnostic, no phase acceptance."""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path('/home/codextransfer/predictive_motion')
REPORT=ROOT/'results/phase5/development/public-coupled-cpp-v2/parity-attempt2/report.json'
OUT=ROOT/'figures/phase5';OUT.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
d=json.loads(REPORT.read_text());assert d['status']=='PASS_FIXED_RECORDED_CPP_PROTOTYPE_ONLY'
r=[x for x in d['records'] if 'max_physical_q' in x]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,2,figsize=(13.5,9.4),constrained_layout=True)
fig.get_layout_engine().set(rect=(0,.09,1,.91))
for ax,key,gate,label in [(axes[0,0],'max_parity_q',1e-12,'C++ vs Python position (rad)'),(axes[0,1],'max_parity_v',1e-11,'C++ vs Python velocity (rad/s)'),(axes[1,0],'max_physical_q',None,'C++ vs recorded position (rad)'),(axes[1,1],'max_physical_v',None,'C++ vs recorded velocity (rad/s)')]:
 for prefix,color,marker,offset in [('train91011','#007c91','o',-.04),('seen91013','#d57918','s',.04)]:
  data=[x for x in r if x['name'].startswith(prefix)]
  for h in [1,2,20,400]:
   group=[x for x in data if x['steps']==h]
   if not group:continue
   ys=[max(x[key],1e-18) for x in group]
   ax.scatter([np.log10(h*.002*1000)+offset]*len(ys),ys,color=color,marker=marker,alpha=.65,label=prefix if h==1 else None)
 ax.set_yscale('log');ax.set_ylim(5e-19,3e-3);ax.set_xticks(np.log10([2,4,40,800]),['2','4','40','800']);ax.set_xlabel('Complete conditional window (ms)');ax.set_ylabel(label);ax.grid(axis='y',alpha=.2)
 if gate:ax.axhline(gate,color='#ad3948',linestyle='--',label='Declared parity tolerance')
 else:
  gates=[1e-6,1e-6,1e-4,1e-4] if key.endswith('_q') else [1e-4,1e-4,1e-3,1e-3]
  ax.plot(np.log10([2,4,40,800]),gates,'--',color='#ad3948',label='Original error gate')
 ax.legend(loc='upper left',fontsize=9)
fig.suptitle('C++ v2 public transition: regression after exact-bound label repair\nPreviously seen TRAIN 91011 / development 91013 · selected complete windows',fontsize=17)
fig.text(.5,.025,'3,437 forecast substeps · clamps and friction branches checked · four incomplete EOF windows retained · zero differences shown at 10⁻¹⁸ floor\nDevelopment diagnostic only: no new plant run, controller integration, timing certificate or Phase 5 acceptance.',ha='center',fontsize=10)
file=OUT/'phase5_public_coupled_cpp_v2_parity.png';fig.savefig(file,dpi=160,bbox_inches='tight');plt.close(fig)
provenance={'status':'DEVELOPMENT_DIAGNOSTIC_ONLY','phase5':'NOT_ACCEPTED','report':str(REPORT),'report_sha256':sha(REPORT),'source':str(Path(__file__)),'source_sha256':sha(__file__),'figure_sha256':sha(file),'units':'q rad; v rad/s; window ms','zero_display_floor':1e-18,'selection':'Fixed predeclared tick windows, no selection by performance; four incomplete EOF windows retained in report.','forecast_substeps':d['forecast_substeps'],'frozen_source_sha256':d['source_freeze_sha256'],'data_acceptance':'Selected fixed recorded conditional windows only; does not establish task or controller performance.'}
(OUT/'phase5_public_coupled_cpp_v2_parity.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(str(file),sha(file))
