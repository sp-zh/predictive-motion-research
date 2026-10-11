from pathlib import Path
import os,json,hashlib
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/phase5-foundation-figure-mpl-cache-v2')
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).parent;A=json.loads((p/'assessment.json').read_text())['points'];F=json.loads((p/'friction.json').read_text())['joint1_force_series'];last=A[-1];attempt=40
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.grid':True,'grid.alpha':.2,'axes.spines.right':False,'axes.spines.top':False})
fig,ax=plt.subplots(1,2,figsize=(14,6));fig.subplots_adjust(left=.09,right=.985,top=.80,bottom=.21,wspace=.31)
fig.suptitle(f'Attempt {attempt}: candidate B rejected | '+('1' if attempt==40 else '5')+' prior physical commits',fontsize=17,y=.96)
a=ax[0];a.plot([1000*z['elapsed'] for z in A],[z['affine_error'] for z in A],lw=2,color='#2374ab');a.axhline(1e-6,color='#a92222',ls='--',label='Original 1e-6 gate');a.scatter(1000*last['elapsed'],last['affine_error'],color='#a92222');a.set_yscale('log');a.set(xlabel='Candidate forecast elapsed (ms)',ylabel='Maximum component error\n(original per-component units)',title=f"First refusal: sample {last['sample']}, {1000*last['elapsed']:.0f} ms");a.legend(loc='upper left',fontsize=9);a.text(.45,.12,f"Rejected: {last['affine_error']:.3g}",transform=a.transAxes,color='#a92222')
a=ax[1];t=[1000*z['elapsed'] for z in F];a.plot(t,[z['nominal_force'] for z in F],lw=2,color='#2374ab',label='Nominal model force');a.plot(t,[z['candidate_force'] for z in F],lw=2,color='#d67d00',label='Nonlinear candidate force');a.axhline(1.137,color='#a92222',ls='--',label='+1.137 Nm limit');a.axvline(1000*last['elapsed'],color='#777777',ls=':');a.set(xlabel='Candidate forecast elapsed (ms)',ylabel='Joint 2 friction force (Nm; index 1)',title='First branch difference at the same sample');a.legend(loc='lower left',bbox_to_anchor=(.44,.02),fontsize=9)
fig.text(.5,.09,'Predictions only: the rejected proposal was not executed. Matching branch-change timing does not establish causality.',ha='center',fontsize=10)
fig.text(.5,.045,'State units: q/C rad; v/w rad/s; s dimensionless; r 1/s. Original component gate unchanged. No full-task, stop or phase acceptance.',ha='center',fontsize=9)
q=p/f'candidate_branch_affine_refusal{attempt}.png';fig.savefig(q,dpi=160);plt.close(fig)
(p/'ROOT_RENDER_RECEIPT.json').write_text(json.dumps({'files':[{'name':q.name,'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()}],'scope':'unchanged recorded forecast data; labels/layout adjusted; no new model/native calculation','matplotlib_version':matplotlib.__version__},indent=2)+'\n')
