import sys,json,os,resource,signal,io,base64,hashlib,pathlib
resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));signal.alarm(40)
p=pathlib.Path('/home/codextransfer/predictive_motion/results/phase5/stop50-actual-visuals-v2-20261012');p.mkdir(exist_ok=False);os.environ['MPLCONFIGDIR']=str(p/'mpl-cache')
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
d=json.load(sys.stdin);t=d['task'];stop=d['stop'];times=[1000*(.004*z['cycle']+z['logical_elapsed']) for z in t]
commits=d['whole']['entry']['commits'];halves=len(t);elapsed=commits*4;state='PASSED' if stop['passed'] else 'NOT ENTERED';dwell=stop['consecutive'];brake=max(0,commits-32)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.grid':True,'grid.alpha':.22,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(2,2,figsize=(14,9),constrained_layout=True);fig.suptitle(f'Attempt 50: {min(32,commits)} active + {brake} braking commands; stop {state}',fontsize=17)
a=ax[0,0];a.plot(times,[100*z['logical_s'] for z in t],lw=2,color='#2374ab');a.set(xlabel='Recorded controller time (ms)',ylabel='Path progress (%)',title=f'{elapsed} ms completed prefix; full task incomplete');a.text(.03,.8,'Compression writer failed before braking',transform=a.transAxes,fontsize=9)
a=ax[0,1];a.plot(times,[1000*z['translation_error_m'] for z in t],lw=2,color='#007f5f',label='Actual TCP translation');a.axhline(10,color='#007f5f',ls='--',label='10 mm limit');a.set(xlabel='Recorded controller time (ms)',ylabel='Translation error (mm)',title=f'{halves} actual native poses vs pinned reference',ylim=(0,11));a.legend(fontsize=9)
a=ax[1,0];a.axis('off');a.text(.5,.65,'Braking and stop monitoring not entered',ha='center',transform=a.transAxes,fontsize=14);a.text(.5,.43,'0 recorded stop halves\n0 / 50 consecutive dwell samples\nNo stop-speed measurement available',ha='center',transform=a.transAxes,fontsize=12)
a=ax[1,1];w=d['whole']['whole'];a.plot([x['cycle']+1 for x in w],[x['wall'] for x in w],marker='o',markersize=3,color='#d67d00');a.axhline(.004,color='#b22222',ls='--');a.set_yscale('log');a.set(xlabel='Current boundary / cycle',ylabel='Whole offline wall time (s)',title='Includes all entered trials; offline development timing');a.text(.03,.07,'4 ms deadline',transform=a.transAxes,color='#b22222')
fig.text(.5,-.015,'Stopped by gzip evidence writer; last scaled reduction incomplete. Original native/SI/strict/B/C gates retained. Development evidence; no full-task/online/Phase5 acceptance.',ha='center',fontsize=10)
images=[];total=0
def emit(fig,name):
 global total
 buf=io.BytesIO();fig.savefig(buf,format='png',dpi=150,bbox_inches='tight');b=buf.getvalue();assert len(b)<=8*1024**2-total;total+=len(b);(p/name).write_bytes(b);images.append({'name':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()});plt.close(fig)
emit(fig,'stop50_actual_diagnostic.png')
fig=plt.figure(figsize=(10,7));a=fig.add_subplot(111,projection='3d');origin=t[0]['actual']['world_position']
for kind,color,label in [('actual','#2374ab','Actual TCP'),('desired','#007f5f','Pinned desired TCP')]:
 vals=[z[kind]['world_position'] for z in t];a.plot(*[[1000*(v[j]-origin[j]) for v in vals] for j in range(3)],lw=2,color=color,label=label)
a.set(xlabel='World X offset (mm)',ylabel='World Y offset (mm)',zlabel='World Z offset (mm)',title=f'Actual recorded {elapsed} ms prefix; full task incomplete');a.legend();fig.text(.5,.03,'Coordinates from actual native poses. Origin = first actual TCP. Seed 91011; offline development diagnostic.',ha='center',fontsize=9);emit(fig,'stop50_actual_tcp_prefix.png')
print(json.dumps({'matplotlib_version':matplotlib.__version__,'files':images,'seed':91011,'scope':'Recorded partial native motion only; stop/fulltask/online/phase unaccepted'}))
