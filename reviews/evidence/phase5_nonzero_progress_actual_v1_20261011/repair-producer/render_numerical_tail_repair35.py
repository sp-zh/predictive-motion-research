from pathlib import Path
import json,subprocess,shlex,hashlib,tarfile,io
P=Path('/private/tmp/phase5_numerical_progress_tail_repair_checkpoint_v1_20261011');raw=P/'actual-dell/full144-planning-margin-pure-v1-20261011-attempt35/pure-margin-cases-v1';remote='/home/codextransfer/predictive_motion/results/phase5/numerical-progress-tail-pure-repair-plot-v1-20261011';inputs={n:(raw/n).read_text() for n in ['zero.stdout','reduced.stdout','planning.stdout','FINITE_CLOCK_CERTIFICATES.json','planning.REFERENCE_ERROR_BOUNDS.json']}
script='''from pathlib import Path
import json,hashlib,os,resource,signal
resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));signal.alarm(40);p=Path(__file__).parent;os.environ['MPLCONFIGDIR']=str(p/'mpl-local-cache');os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt;import numpy as np
names=['zero.stdout','reduced.stdout','planning.stdout','FINITE_CLOCK_CERTIFICATES.json','planning.REFERENCE_ERROR_BOUNDS.json'];before={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names};cert=json.loads((p/names[3]).read_text())['cases'];bounds=json.loads((p/names[4]).read_text());assert len(cert)==3 and len(bounds)==400;rows=[];violations=[]
for name in ['zero','reduced','planning']:
 lines=(p/(name+'.stdout')).read_text().splitlines();violations.append(float(next(s for s in lines if s.startswith('original14756SI_max,')).split(',')[1]))
 if name=='planning':rows=[[float(v) for v in s.split(',')[1:]] for s in lines if s.startswith('reference_point,')]
assert len(rows)==400 and cert[2]['valid_reference_domains']==400;times=[];elapsed=0;lattice=[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40]
for k,n in enumerate(lattice):
 for cycle in range(n):
  for half in [1,2]:times.append(elapsed+.004*cycle+.002*half)
 elapsed+=.004*n
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2});fig,ax=plt.subplots(2,2,figsize=(13,8.5));fig.suptitle('Phase 5 pure planning repair: finite terminal progress margin',x=.075,ha='left',fontsize=18)
x=np.arange(3);observed=[c['terminal_r'] for c in cert];targets=[c['target'] for c in cert];ax[0,0].scatter(x,observed,s=70,color=['#b23a38','#b23a38','#006f89'],label='Literal C++ terminal r',zorder=3);ax[0,0].scatter(x,targets,marker='x',color='#777777',s=45,label='Prospective planning target');ax[0,0].axhline(0,color='#777777',ls=':');ax[0,0].set_yscale('symlog',linthresh=1e-17);ax[0,0].set_xticks(x,['0','1e-18','1e-13']);ax[0,0].set(title='Zero / reduced controls retain strict failures',xlabel='Planning terminal r target (1/s)',ylabel='Pure terminal r (1/s)',ylim=(-4e-17,3e-13));ax[0,0].legend(loc='upper left',fontsize=8)
for i,c in enumerate(cert):ax[0,0].annotate('Refused' if i<2 else '400 / 400 references pass',(i,observed[i]),xytext=(0,-18 if i<2 else 12),textcoords='offset points',ha='center',fontsize=8)
ax[0,1].semilogy(times,[max(b['R_bound'],1e-22) for b in bounds],color='#006f89',label='Exact-rational operation bound');ax[0,1].semilogy(times,[max(b['R_error'],1e-22) for b in bounds],color='#d47623',label='Observed clock rounding error');ax[0,1].axhline(1e-13,color='#777777',ls=':',label='Planning margin');ax[0,1].set(title='Input-specific finite IEEE certificate',xlabel='Command reference horizon (s)',ylabel='Cell-reference r error / bound (1/s)');ax[0,1].legend(loc='lower right',fontsize=8)
ax[1,0].plot(times,[r[-1] for r in rows],color='#006f89');ax[1,0].axhline(0,color='#777777',ls=':');ax[1,0].set(title='All 400 logical speed references',xlabel='Predicted command horizon (s)',ylabel='Logical r (1/s)');ax[1,0].text(.05,.15,'Certified terminal r lower: 9.985e-14 1/s',transform=ax[1,0].transAxes,fontsize=9)
ax[1,1].semilogy(x,violations,'o',color='#006f89',markersize=7);ax[1,1].axhline(1e-7,color='#b23a38',ls=':',label='Original SI acceptance 1e-7');ax[1,1].set_xticks(x,['0','1e-18','1e-13']);ax[1,1].set(title='All 14,756 original SI rows checked',xlabel='Planning terminal r target (1/s)',ylabel='Maximum original SI violation',ylim=(1e-20,1e-6));ax[1,1].legend(loc='upper left',fontsize=8)
fig.text(.075,.058,'Saved attempt 30 input | 144 dimensions | 200 literal cycles + 400 cell references | original SI / strict limits unchanged',fontsize=10)
fig.text(.075,.027,'Biased numerical planning space, not equivalent to original E0 or a stop certificate. No new Model, physics, controller or phase acceptance.',fontsize=9)
fig.subplots_adjust(top=.88,bottom=.17,left=.075,right=.97,hspace=.43,wspace=.31)
for ext in ['png','svg']:fig.savefig(p/('numerical_progress_tail_repair.'+ext),dpi=160)
plt.close(fig);assert before=={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names};outputs={n:{'bytes':(p/n).stat().st_size,'sha256':hashlib.sha256((p/n).read_bytes()).hexdigest()} for n in ['numerical_progress_tail_repair.png','numerical_progress_tail_repair.svg']};(p/'PLOT_PROVENANCE.json').write_text(json.dumps({'schema':'NUMERICAL_TAIL_PURE_REPAIR_PLOT_V1','inputs':before,'outputs':outputs,'matplotlib_version':matplotlib.__version__,'scope':'all3prospectivemargins, all400pureclockerrors/bounds/planningspeeds/fullSI, savedoneinputcase; noactualmotion/globalguarantee','new_Model_or_MuJoCo':0},indent=2)+'\\n');print(json.dumps(outputs))
''';inputs['render.py']=script;ssh=['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer'];stage='''from pathlib import Path
import sys,json
p=Path(%r);p.mkdir(exist_ok=False)
for n,b in json.load(sys.stdin).items():(p/n).write_text(b)
'''%remote;x=subprocess.run(ssh+['python3 -I -S -B -c '+shlex.quote(stage)],input=json.dumps(inputs).encode(),capture_output=True,timeout=25);assert x.returncode==0,x.stderr;x=subprocess.run(ssh+['env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 '+remote+'/render.py'],capture_output=True,timeout=45);print(x.stdout.decode());assert x.returncode==0,x.stderr
code='''from pathlib import Path
import io,sys,tarfile
p=Path(%r);b=io.BytesIO()
with tarfile.open(fileobj=b,mode='w:gz') as t:
 for q in sorted(p.iterdir()):
  if q.is_file():t.add(q,arcname=q.name)
assert len(b.getvalue())<16777216;sys.stdout.buffer.write(b.getvalue())
'''%remote;x=subprocess.run(ssh+['python3 -I -S -B -c '+shlex.quote(code)],capture_output=True,timeout=25);assert x.returncode==0,x.stderr;out=P/'figures';out.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(x.stdout)) as t:assert all(m.isfile() and '..' not in Path(m.name).parts and not m.name.startswith('/') for m in t.getmembers());t.extractall(out,filter='data')
for n,row in json.loads((out/'PLOT_PROVENANCE.json').read_text())['outputs'].items():assert (out/n).stat().st_size==row['bytes'] and hashlib.sha256((out/n).read_bytes()).hexdigest()==row['sha256']
print('pure repair plot readbackPASS')
