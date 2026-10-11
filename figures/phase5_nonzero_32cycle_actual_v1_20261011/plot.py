import os,resource,signal,json,pathlib,hashlib
resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));signal.alarm(40)
p=pathlib.Path(__file__).parent;os.environ['MPLCONFIGDIR']=str(p/'mpl-local-cache')
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
s=json.loads((p/'functional.json').read_text());t=json.loads((p/'task_points.json').read_text());n=json.loads((p/'native.json').read_text())['cycles'];fine=json.loads((p/'fine.json').read_text());time=[1000*(.004*z['cycle']+z['logical_elapsed']) for z in t];cycles=list(range(1,33))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.grid':True,'grid.alpha':.22,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(2,2,figsize=(14,9),constrained_layout=True)
fig.suptitle('32 genuine nonzero closed-loop cycles | seed 91011 | offline development',fontsize=17)
a=ax[0,0];a.plot(time,[100*z['logical_s'] for z in t],color='#2374ab',lw=2);a.set(xlabel='Actual controller elapsed (ms)',ylabel='Path progress (%)',title='128 ms recorded prefix — full task incomplete');a.annotate('Final progress 0.1267%',(time[-1],100*t[-1]['logical_s']),xytext=(-115,-22),textcoords='offset points')
a=ax[0,1];a.plot(time,[1000*z['translation_error_m'] for z in t],label='TCP translation (mm)',color='#007f5f',lw=2);a.axhline(10,color='#007f5f',ls='--',label='10 mm limit');a.set(xlabel='Actual controller elapsed (ms)',ylabel='Translation error (mm)',title='64 actual 2 ms poses vs pinned task reference');b=a.twinx();b.plot(time,[z['rotation_angle_rad'] for z in t],color='#a13d63',lw=2,label='SO(3) angle (rad)');b.axhline(.05,color='#a13d63',ls=':',label='0.05 rad limit');b.set_ylabel('Orientation error (rad)');b.set_ylim(0,.055);a.set_ylim(0,11);lines=a.get_lines()+b.get_lines();a.legend(lines,[x.get_label() for x in lines],fontsize=8,loc='center right')
a=ax[1,0];a.plot(cycles,[z['timing']['complete_cycle_seconds'] for z in n],color='#d67d00',marker='o',markersize=3);a.axhline(.004,color='#b22222',ls='--');a.set_yscale('log');a.set(xlabel='Cycle',ylabel='Measured offline wall time (s)',title='4 ms deadline missed in 32 / 32 cycles');a.text(.03,.08,'4 ms deadline',transform=a.transAxes,color='#b22222');a.set_ylim(.002,10)
a=ax[1,1];names=['evidence_codec_write_sha','geometry_query','current_numeric_hint','evidence_fsync','assembly','native_osqp_wrapper'];labels=['Evidence codec + write + SHA','Nominal geometry query','Fresh current numeric hint','Evidence fsync','Affine + QP assembly','Native solver wrapper'];vals=[next(z['total_seconds']/32 for z in fine['segments'] if z['name']==name) for name in names];a.barh(labels[::-1],vals[::-1],color='#596d8c');a.set(xlabel='Mean measured seconds per cycle',title='Nested measurements overlap; do not add');a.tick_params(axis='y',labelsize=9)
fig.text(.5,-.015,'32 commits / 64 physical substeps / 12,800 candidate checks. No full-task, physical-stop, online 4 ms or Phase 5 acceptance claim.',ha='center',fontsize=10)
fig.savefig(p/'actual32_diagnostic.png',dpi=160,bbox_inches='tight');plt.close(fig)
fig=plt.figure(figsize=(10,7));a=fig.add_subplot(111,projection='3d');pa=[z['actual']['world_position'] for z in t];pd=[z['desired']['world_position'] for z in t];origin=pa[0]
for vals,color,label in [(pa,'#2374ab','Actual TCP'),(pd,'#007f5f','Pinned desired TCP')]:
 a.plot(*[[1000*(v[j]-origin[j]) for v in vals] for j in range(3)],color=color,lw=2,label=label)
a.set(xlabel='World X offset (mm)',ylabel='World Y offset (mm)',zlabel='World Z offset (mm)',title='Actual recorded TCP prefix: 128 ms, path progress 0.1267%');a.legend();fig.text(.5,.025,'Replay coordinates from 64 recorded native poses; origin = first actual TCP. Offline diagnostic; task completion and stop unverified.',ha='center',fontsize=9);fig.savefig(p/'actual32_tcp_prefix.png',dpi=160,bbox_inches='tight');plt.close(fig)
files=[]
for q in p.glob('*.png'):files.append({'name':q.name,'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
(p/'RENDER_RECEIPT.json').write_text(json.dumps({'files':files,'matplotlib_version':matplotlib.__version__,'scope':'actual recorded offline prefix; not complete task/stop/Phase5 acceptance','seed':91011},indent=2)+'\n')
