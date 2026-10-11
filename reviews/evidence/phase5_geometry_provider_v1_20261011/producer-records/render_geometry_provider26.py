from pathlib import Path
import json,subprocess,shlex,hashlib,tarfile,io
P=Path('/private/tmp/phase5_geometry_provider_checkpoint_v1_20261011');D=P/'actual-dell/nominal-geometry-provider-recorded-v4-20261011-attempt26/run-attempt1/artifacts';remote='/home/codextransfer/predictive_motion/results/phase5/recorded-geometry-provider-plot-v1-20261011'
script='''import pathlib,json,csv,hashlib,os,resource,signal
resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));signal.alarm(40);p=pathlib.Path(__file__).parent;os.environ['MPLCONFIGDIR']=str(p/'mpl-local-cache')
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt;import numpy as np
names=['nominal_geometry_minima.csv','gradient_regression_summary.csv','selected_witness_regression.csv'];before={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names};mins,reg,wit=[list(csv.DictReader((p/n).open())) for n in names];assert len(mins)==1200 and len(reg)==9 and len(wit)==252
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
for ext in ['png','svg']:fig.savefig(p/('recorded_nominal_geometry.'+ext),dpi=160)
plt.close(fig);after={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names};assert before==after;outputs={n:{'bytes':(p/n).stat().st_size,'sha256':hashlib.sha256((p/n).read_bytes()).hexdigest()} for n in ['recorded_nominal_geometry.png','recorded_nominal_geometry.svg']};(p/'PLOT_PROVENANCE.json').write_text(json.dumps({'schema':'RECORDED_NOMINAL_GEOMETRY_PROVIDER_PLOT_V1','inputs':before,'outputs':outputs,'matplotlib_version':matplotlib.__version__,'scope':'all1200recordednominalposes andall9fixedgradientprobes; noactualcontroller/motion/geometryQPsolve/candidateperformance','new_geometry_engine_or_ModelF1_or_MuJoCo_entries':0},indent=2)+'\\n');print(json.dumps(outputs))
'''
files={n:(D/n).read_text() for n in ['nominal_geometry_minima.csv','gradient_regression_summary.csv','selected_witness_regression.csv']};files['render.py']=script;ssh=['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer'];code='''import pathlib,json,sys
p=pathlib.Path(%r);p.mkdir(exist_ok=False)
for n,b in json.load(sys.stdin).items():(p/n).write_text(b)
'''%remote;r=subprocess.run(ssh+['python3 -I -S -B -c '+shlex.quote(code)],input=json.dumps(files).encode(),capture_output=True,timeout=20);assert r.returncode==0,r.stderr
r=subprocess.run(ssh+['env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /usr/bin/python3 '+remote+'/render.py'],capture_output=True,timeout=45);assert r.returncode==0,r.stderr;print(r.stdout.decode());code='''import pathlib,tarfile,io,sys
p=pathlib.Path(%r);b=io.BytesIO()
with tarfile.open(fileobj=b,mode='w:gz') as t:
 for q in p.iterdir():
  if q.is_file():t.add(q,arcname=q.name)
assert len(b.getvalue())<16777216;sys.stdout.buffer.write(b.getvalue())
'''%remote;r=subprocess.run(ssh+['python3 -I -S -B -c '+shlex.quote(code)],capture_output=True,timeout=20);assert r.returncode==0,r.stderr;O=P/'figures';O.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(r.stdout)) as t:assert all(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in t.getmembers());t.extractall(O,filter='data')
for n,row in json.loads((O/'PLOT_PROVENANCE.json').read_text())['outputs'].items():assert (O/n).stat().st_size==row['bytes'] and hashlib.sha256((O/n).read_bytes()).hexdigest()==row['sha256']
print('allplotoutputs/standaloneinput/sourcefullreadback PASS')
