from pathlib import Path
import sys,os,json,hashlib,struct,ast,math,resource
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,768*1024**2))
P=Path('/private/tmp/phase5_physical_stop_nominal_design_v1_20261016');P.mkdir();os.environ['P5_DERIVED53_ROOT']=str(P);root=Path('/private/tmp/phase5_controlled_stop_roundoff_command_terminal64_v1_20261016');A=next((root/'actual-dell').iterdir())/'run-attempt1/artifacts';reader=Path('/Users/uot/Documents/ChatGPT/ros/tools/cold_storage_verification_v1/strict_codec_reader.py');import importlib.util
spec=importlib.util.spec_from_file_location('strict',reader);codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
class R:
 def __init__(self,p,role):self.b,self.facts=codec.verify_artifact(p,True,True);self.i=0;assert self.t()=='P5_ACTIVE_SESSION_LOSSLESS_V1'and self.t()==role
 def u(self):v=struct.unpack_from('<Q',self.b,self.i)[0];self.i+=8;return v
 def d(self):v=struct.unpack_from('<d',self.b,self.i)[0];self.i+=8;return v
 def t(self):n=self.u();v=self.b[self.i:self.i+n].decode();self.i+=n;return v
 def arr(self,n):return[self.d()for _ in range(n)]
 def vec(self):return self.arr(self.u())
 def end(self):assert self.i==len(self.b)
def snapshot(p):
 r=R(p,'ACTUAL_NATIVE_SESSION_SNAPSHOT');o={'path':str(p),'codec':r.facts,'observation_id':r.t(),'transaction_id':r.t(),'tick':r.u(),'sequence':r.u(),'completed':r.u(),'stage':r.t(),'error':r.t()};[r.u()for _ in range(3)];o['time']=r.d();r.d();o['contact_free']=r.u()
 for k in ['q','v','C','w']:o[k]=r.arr(7)
 o['s']=r.d();o['r']=r.d();o['previous_alpha']=r.arr(7);o['previous_b']=r.d();o['acc_available']=r.u();r.arr(7);o['a']=r.arr(7);o['halves']=r.u();r.t();r.vec();r.vec();r.end();return o
mesh=[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40];Ls=[1,2,3,4,5,6,7,8,10,12,16,19];Ms=[2,3,4,5,6,7,8,10,12,16,19];Js=[4.99,4.5,4.,3.5,3.,2.5,2.,1.5,1.,.75,.5,.25,.1,.05,.02,.01];constants=Path('/private/tmp/phase5_current_braking_nominal62_source_v3_20261016/PINNED_CONSTANTS62.json');assert hashlib.sha256(constants.read_bytes()).hexdigest()=='d37c9a12539345fd1dbb6718cd273584140359ca2bd9834442bf2228e50f6bdd';c=json.loads(constants.read_text());bounds=list(zip(c['control_range'][::2],c['control_range'][1::2]));tree=ast.parse(Path('/private/tmp/check_nominal62_all_records_v3.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'<original-scalar-and-progress-families>','exec'));node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='check');s=ast.unparse(node);s=s.replace('def check(','def check_original(').replace('cap * 0.999','cap').replace('jerk * 0.999','jerk');exec(compile(s,'<original-only-warm-check>','exec'))
def shifted_previous(cycle):
 commits=list((A/('cycle-'+str(cycle-1))).glob('trial-*/actual_commit.bin'));assert len(commits)==1;q=commits[0].parent/'candidate.bin';r=R(q,'SOLVER_RESULT_AND_DATA_ONLY_PREVIEW');r.t();flags=[r.u()for _ in range(8)];u=r.vec();assert len(u)==160 and flags[1]==flags[2]==1 and flags[4]==1;out=[[0.]*8 for _ in mesh];start=1
 for k in range(20):
  end=start+mesh[k];old=0
  for j in range(20):
   last=old+mesh[j];left=max(start,old);right=min(end,last)
   if right>left:
    for d in range(8):out[k][d]+=(float(right-left)/mesh[k])*u[j*8+d]
   old=last
  start=end
 return out,{'path':str(q),'codec':r.facts,'flags':flags,'scope':'Existing previous final accepted candidate controls only, no inherited owner/permission.'}
def integrate(u,w,C):
 for k in range(20):
  for _ in range(mesh[k]):w=w+.004*u[k];C=C+.004*w
 return w,C
def doublehat(w,prior,C,target,L,M):
 peak=(M-1)//2;base=[prior*max(0.,1.-(k+1)/L)for k in range(20)];a=[min((k+1)/(peak+1),(M-k)/(M-peak))if k<M else 0. for k in range(20)];b=[a[18-k]if k<=18 else 0. for k in range(20)];bw,bC=integrate(base,w,C);wa,ca=integrate(a,0.,0.);wb,cb=integrate(b,0.,0.);det=wa*cb-wb*ca;scale=abs(wa*cb)+abs(wb*ca)
 if not math.isfinite(det)or not scale>0 or abs(det)<=1e-10*scale:return [],0.,0.,{'reason':11,'cell':0,'step':0,'last_rate':w,'last_position':C,'max_jerk':0.,'observed':det,'bound':1e-10*scale}
 p1=((-bw)*cb-(target-bC)*wb)/det;p2=(wa*(target-bC)-ca*(-bw))/det;return [base[k]+p1*a[k]+p2*b[k]for k in range(20)],p1,p2,None
baseline=snapshot(A/'cycle-0/trial-0/observation_before.bin');assert baseline['tick']==baseline['sequence']==0 and baseline['completed']and max(map(abs,baseline['v']))<=1e-4;offset=[C-q for C,q in zip(baseline['C'],baseline['q'])];cases=[]
for cycle in [32,87]:
 x=snapshot(A/('cycle-'+str(cycle))/'trial-0/observation_before.bin');warm,warmfacts=shifted_previous(cycle);target=[q+off-.02*v for q,off,v in zip(x['q'],offset,x['v'])];channels=[];selected_controls=[[0.]*8 for _ in mesh];allok=True
 for ch in range(7):
  records=[];best=None;fid=0
  for L in Ls:
   for M in Ms:
    u,p1,p2,early=doublehat(x['w'][ch],x['previous_alpha'][ch],x['C'][ch],target[ch],L,M);pr=check(u,x['w'][ch],x['previous_alpha'][ch],x['C'][ch],False,*bounds[ch],0.)if early is None else early
    if pr['reason']==0 and abs(pr['last_position']-target[ch])>1e-12:pr.update(reason=13,observed=abs(pr['last_position']-target[ch]),bound=1e-12)
    score=abs(x['C'][ch]+.004*(x['w'][ch]+.004*u[0])-target[ch])if pr['reason']==0 else 0.;record={'family':fid,'L':L,'M':M,'pulse1':p1,'pulse2':p2,'score':score,**pr};records.append(record)
    if pr['reason']==0 and(best is None or score<best['record']['score']):best={'record':record,'controls':u}
    fid+=1
  if best is None:
   u=[row[ch]for row in warm];pr=check_original(u,x['w'][ch],x['previous_alpha'][ch],x['C'][ch],False,*bounds[ch],0.);score=abs(x['C'][ch]+.004*(x['w'][ch]+.004*u[0])-target[ch])if pr['reason']==0 else 0.;record={'family':132,'pulse1':0.,'pulse2':0.,'score':score,'warm_position_target_not_required':True,**pr};records.append(record)
   if not pr['reason']:best={'record':record,'controls':u}
  channels.append({'channel':ch,'target_C':target[ch],'target_delta':target[ch]-x['C'][ch],'records':records,'selected':best})
  if best:
   for k in range(20):selected_controls[k][ch]=best['controls'][k]
  else:allok=False
 progress_records=[];pbest=None
 for fid in range(148):
  u,parameter,early=family(x['r'],x['previous_b'],2e-7,fid);pr=check(u,x['r'],x['previous_b'],x['s'],True,0,0,2e-7)if early is None else dict(last_rate=x['r'],last_position=x['s'],max_jerk=0.,**early)
  if not pr['reason']and x['r']+.004*u[0]<1e-7:pr.update(reason=12,observed=x['r']+.004*u[0],bound=1e-7,cell=0,step=0)
  record={'family':fid,'parameter':parameter,**pr};progress_records.append(record)
  if not pr['reason']:pbest={'record':record,'controls':u};break
 if pbest is None:
  u=[r[7]for r in warm];pr=check_original(u,x['r'],x['previous_b'],x['s'],True,0,0,0.)
  if not pr['reason']and x['r']+.004*u[0]<1e-7:pr.update(reason=12,observed=x['r']+.004*u[0],bound=1e-7,cell=0,step=0)
  record={'family':148,'parameter':0.,'warm_terminal_rate_nearzero_not_2e7':True,**pr};progress_records.append(record)
  if not pr['reason']:pbest={'record':record,'controls':u}
 if pbest:
  for k in range(20):selected_controls[k][7]=pbest['controls'][k]
 else:allok=False
 cases.append({'cycle':cycle,'snapshot':x,'warm':warmfacts,'physical_T_seconds':.02,'channels':channels,'progress':{'records':progress_records,'selected':pbest,'target_nominal_terminal_r':2e-7,'first4ms_lower':1e-7},'all8_scalar_channels_success':allok,'selected_controls':selected_controls if allok else None})
report={'schema':'SAVED64_PHYSICAL_CURRENT_STATE_DOUBLE_HAT_PROGRESS_BAND_PURE_DESIGN_V1','baseline':baseline,'baseline_offset_C_minus_q':offset,'baseline_extra_retained_scalar_count':10,'coefficient_record_bytes_proposed':112,'maximum_nominal_payload':1080*112+1280+4096,'finite_family_caps_unchanged':{'joint_analytic':132,'joint_warm':1,'progress':149,'total':1080},'cases':cases,'scope':'Pure saved-data fixed132 analytic families, no Model/OSQP/SI/B/C/new65 source or simulation. Ctarget approximation from same-session measured warmup/actual q/v; no actual/history/accepted controls changed, no exact gravity or stop proof. All failures retained, no clipping, original scalar domains/jerk/200macro400half preserved; first progress lower is a proposed stricter planning subset only.'};bounded_write(P/'SAVED64_DOUBLEHAT_PHYSICAL_AND_PROGRESS_DESIGN.json',json.dumps(report,indent=2)+'\n');print(json.dumps({'baseline_v_inf':max(map(abs,baseline['v'])),'offset':offset,'cases':[{'cycle':e['cycle'],'all8':e['all8_scalar_channels_success'],'selected_joint_families':[c['selected']['record']['family']if c['selected']else None for c in e['channels']],'joint_success_count':[sum(r['reason']==0 for r in c['records'])for c in e['channels']],'progress_selected':e['progress']['selected']['record']if e['progress']['selected']else None,'total_records':sum(len(c['records'])for c in e['channels'])+len(e['progress']['records'])}for e in cases]}))
