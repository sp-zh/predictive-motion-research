from pathlib import Path
import csv,json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
p=Path(__file__).resolve().parent
data=p.parents[1]/'reviews/evidence/phase5_geometry_provider_v1_20261011/plot-inputs'
names=['nominal_geometry_minima.csv','gradient_regression_summary.csv','selected_witness_regression.csv']
expected={'nominal_geometry_minima.csv': '6fbe880d4341e87d9457c0e2b34ed16c6b71fe1fa184d2a76447391117d05a94', 'gradient_regression_summary.csv': '5e2c9ad784b33ba2858e75e3cb8a12cc580259e3dd608dcf38827e4bc47b41d5', 'selected_witness_regression.csv': 'd7cd643dc8e2b93d6dd36145040d53d45c97b72657bfac61e8b303fc3370978d'}
before={n:hashlib.sha256((data/n).read_bytes()).hexdigest() for n in names}
assert before==expected
mins,reg,wit=[list(csv.DictReader((data/n).open())) for n in names]
assert len(mins)==1200 and len(reg)==9 and len(wit)==252
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2});fig,ax=plt.subplots(1,2,figsize=(13,6.5));fig.suptitle('Phase 5 development: geometry at recorded nominal poses',fontsize=18,x=.07,ha='left');colors=['#006f89','#d47623','#684e91']
for k,c in enumerate(colors):
 r=[r for r in mins if int(r['cycle'])==k];t=[float(x['elapsed_s']) for x in r];ax[0].plot(t,[float(x['min_true_m'])*1000 for x in r],color=c,label=f'Cycle {k+1}: true');ax[0].plot(t,[float(x['min_cover_m'])*1000 for x in r],color=c,ls='--',label=f'Cycle {k+1}: cover')
ax[0].axhline(5,color='#b23a38',ls=':',label='Original 5 mm floor');ax[0].set_ylim(4,25);ax[0].set_xlim(0,.8);ax[0].set_xlabel('Recorded nominal prediction time (s)');ax[0].set_ylabel('Full-query clearance (mm)');ax[0].set_title('1200 poses, 9035 queries at each pose',loc='left');ax[0].legend(loc='lower right',fontsize=8,ncol=2)
x=np.arange(9);labels=[f"C{int(r['cycle'])+1}/S{int(r['sample'])}" for r in reg];series=[('point_max_error',1e-7,'Point Jacobian','#006f89','o'),('cover_max_error',1e-5,'Cover centered FD','#568d39','s'),('true_smooth_max_error',1e-4,'True smooth FD','#d47623','^')]
for name,limit,label,color,marker in series:ax[1].semilogy(x,[max(float(r[name]),1e-13) for r in reg],marker=marker,color=color,label=label);ax[1].axhline(limit,color=color,ls=':',lw=1.3,label=f'{label} original gate {limit:g}')
ax[1].set_ylim(1e-12,1e-3);ax[1].set_xticks(x,labels,rotation=40,ha='right',fontsize=9);ax[1].set_ylabel('Derivative error (m/rad)');ax[1].set_title('Nine fixed gradient probe poses',loc='left');ax[1].legend(loc='center right',fontsize=8);ax[1].text(.035,.97,'epsilon = 1e-6 rad; all original gates pass',transform=ax[1].transAxes,va='top',fontsize=10)
fig.text(.07,.11,'Selected QP assistance: 2 true + 2 cover supports per pose = 4800 rows. Full nonlinear candidate checks remain mandatory.',fontsize=10)
fig.text(.07,.065,'63 point components | 33,012 cover components | 7,549 smooth / 11 non-smooth true components | 0 interval failures',fontsize=10)
fig.text(.07,.025,'Recorded Model nominal poses only; no new ModelF1, MuJoCo or controller steps. No full-task, real-time or Phase5 acceptance claim.',fontsize=9)
fig.subplots_adjust(top=.84,bottom=.24,left=.075,right=.975,wspace=.3)
for ext in ['png','svg']:fig.savefig(p/('recorded_nominal_geometry_root.'+ext),dpi=160)
plt.close(fig);after={n:hashlib.sha256((data/n).read_bytes()).hexdigest() for n in names};assert before==after;outputs={n:{'bytes':(p/n).stat().st_size,'sha256':hashlib.sha256((data/n).read_bytes()).hexdigest()} for n in ['recorded_nominal_geometry_root.png','recorded_nominal_geometry_root.svg']}
(p/'ROOT_REPRODUCTION_PROVENANCE.json').write_text(json.dumps({'schema':'ROOT_RECORDED_NOMINAL_GEOMETRY_REPRODUCTION_V1','inputs':before,'outputs':outputs,'matplotlib_version':matplotlib.__version__,'scope':'Pure plot of pinned saved geometry/minimum/FD summaries; no new FK/Scene/Model/native/controller entry; full FD aggregate not independently replayed.'},indent=2)+'\n')
print(json.dumps(outputs))
