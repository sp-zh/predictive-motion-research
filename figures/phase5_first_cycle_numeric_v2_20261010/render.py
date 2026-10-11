from pathlib import Path
import csv, json, hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
rows=list(csv.DictReader((ROOT/'nominal_halves.csv').open()))
t=np.array([float(r['elapsed_seconds']) for r in rows])
q=np.array([[float(r[f'q{j}']) for j in range(7)] for r in rows])
C=np.array([[float(r[f'C{j}']) for j in range(7)] for r in rows])
v=np.array([[float(r[f'v{j}']) for j in range(7)] for r in rows])
w=np.array([[float(r[f'w{j}']) for j in range(7)] for r in rows])
assert len(rows)==400 and abs(t[-1]-.8)<1e-12
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
fig,axes=plt.subplots(1,3,figsize=(16,5.4),gridspec_kw={'width_ratios':[1.15,1.15,1]},layout='constrained')
colors=plt.cm.tab10(np.arange(7))
for j,c in enumerate(colors):
 axes[0].plot(t,1000*(q[:,j]-C[:,j]),color=c,lw=1.8,label=f'Joint {j+1}')
 axes[1].plot(t,v[:,j],color=c,lw=1.8)
axes[0].set(title='Model position relative to held command',xlabel='Prediction time (s)',ylabel='q − C (mrad)')
axes[0].legend(loc='upper right',fontsize=8,ncol=2,frameon=False)
axes[1].axhline(0,color='#333333',ls='--',lw=1.2,label='Command velocity w = 0')
axes[1].set(title='Physical-model velocity',xlabel='Prediction time (s)',ylabel='v (rad/s)')
axes[1].legend(loc='upper right',fontsize=8,frameon=False)
labels=['Upstream + raw retention','Inline assembly','Remaining QP path']
ms=[1535.246594,122.238013,(.918262475-.122238013)*1000]
axes[2].barh(labels,ms,color=['#5b7b92','#66835a','#b27b51'])
axes[2].invert_yaxis();axes[2].set(title='Measured offline path',xlabel='Wall time (ms)')
for i,x in enumerate(ms):axes[2].text(x+18,i,f'{x:.1f}',va='center',fontsize=10)
axes[2].set_xlim(0,1800)
axes[2].text(.02,-.31,'Native setup: 108.36 ms\nNative solve: 3.06 ms\n4 ms target missed; no usable candidate',transform=axes[2].transAxes,fontsize=10)
for a in axes[:2]:a.grid(alpha=.2);a.set_xlim(0,.8)
fig.suptitle('First genuine predictive horizon — QP TIME_LIMIT, no executed command',fontsize=17,weight='bold')
fig.text(.005,-.04,'400 model-produced 2 ms samples, N=20 / horizon=0.8 s. Frozen observed boundary; zero nominal inputs. This is a forecast, not an arm trajectory or task result.',fontsize=10)
fig.savefig(ROOT/'nominal_diagnostic.png',dpi=160,bbox_inches='tight')
fig.savefig(ROOT/'nominal_diagnostic.svg',bbox_inches='tight')
plt.close(fig)
print('Rendered genuine nominal diagnostic, no plant movement claim.')
