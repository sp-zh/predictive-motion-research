from pathlib import Path
import json,sys,io,struct,math,numpy as np,importlib.util,time
B=Path('/private/tmp/post67_command_history_unit_v1_20261016');sp=importlib.util.spec_from_file_location('bp',B/'bounded_output.py');bp=importlib.util.module_from_spec(sp);sp.loader.exec_module(bp)
sys.path.insert(0,'/private/tmp/root_independent_controlled_stop52_review_20261012');from compressed_evidence50_v5 import EvidenceReadSet,load_math_definitions
rs=EvidenceReadSet('/Users/uot/Documents/ChatGPT/ros/tools/cold_storage_verification_v1/strict_codec_reader.py');ref=Path('/private/tmp/root_independent_controlled_stop52_review_20261012/reference_source');n=load_math_definitions(rs,ref/'audit_geometry_qp_actual.py',ref/'audit_actual39.py');vv=json.loads(Path('/Users/uot/Documents/ChatGPT/ros/reviews/evidence/phase5_joint_jerk67_prepared_v1_20261016/PREPARED_REVIEW_CAPSULE.json').read_text());gn={'__name__':'reader_v9'};exec(vv['Root_reviews_and_reproducible_V9_reader_source']['V9_reader']['code'],gn)
def pack(path,values):
 out=io.BytesIO()
 for a in values:
  a=np.asarray(a,dtype='<f8');out.write(struct.pack('<'+'Q'*a.ndim,*a.shape));out.write(a.tobytes(order='C'))
 bp.put(path,out.getvalue())
results=[]
for cycle in [32,95]:
 P=B/('context'+str(cycle))
 def raw(name):return rs.reader.verify_artifact(P/name,True,True)[0]
 d=n['reduction'](raw('qp_equality_reduction.bin'));q=n['inline_full'](raw('inline_qp.bin'));before=n['snapshot'](raw('observation_before.bin'));can=n['candidate'](raw('candidate.bin'));hint=n['parse_current_hint'](raw('current_numeric_hint.bin'));pg=gn['parse_raw'](raw('planning_guard.bin'),d['D'],solver_lower=d['ls'],solver_upper=d['us'],row_map=d['rows'],row_scale=d['R'],unscaled_lower=d['lr'],unscaled_upper=d['ur'],original_labels=q['labels']);M=len(d['ls']);w=before['x'][21:28];prev=before['alpha'];a0=-w/.004
 eligible=bool(np.max(abs(a0))<=1 and np.max(abs((a0-prev)/.004))<=19.98 and np.max(abs(a0/.004))<=19.98 and np.max(abs(before['x'][7:14]))<=1e-4 and np.max(abs(before['a']))<=1e-3)
 center=q['seed'].copy();newlo=d['ls'].copy();newhi=d['us'].copy();seed=hint['x'].copy();strict=pg['strict_alpha'];solver=pg['solver_alpha'];newL=np.array([e['lower']for e in pg['first']]);newU=np.array([e['upper']for e in pg['first']])
 if eligible:
  center=can['U'].copy();center[np.arange(160)%8!=7]=0.;center[:7]=a0
  # New center remains within the ORIGINAL saved qtrust rows. A conservative
  # long-double forward error envelope tightens the existing radius only.
  ids=[i for i,(label,unit)in enumerate(q['labels'])if label.startswith('trust/q/half/')];AA=q['A'][ids].astype(np.longdouble);cc=center.astype(np.longdouble);value=AA@cc;products=np.abs(AA)*np.abs(cc);err=1024*np.finfo(np.longdouble).eps*np.sum(products,axis=1)+np.longdouble(1e-18);margin=np.minimum(value-q['l'][ids],q['u'][ids]-value)-err;l1=np.sum(np.abs(AA),axis=1)*(1+1024*np.finfo(np.longdouble).eps);assert np.min(margin)>0
  strict=min(strict,float(np.min(np.longdouble(.125)*margin[l1>0]/l1[l1>0])));strict=math.nextafter(strict,0.);solver=math.nextafter(strict*.999,0.)
  base=pg['base'];seed=center[:144]/d['D'];newL=[];newU=[]
  for k in range(20):
   for j in range(7):
    col=k*8+j;row=base+k*7+j;mult=float(d['R'][row]);L=max(-1.,float(center[col])-solver)-float(d['p'][col]);U=min(1.,float(center[col])+solver)-float(d['p'][col])
    if k==0:
     sb=max(.5*abs(float(w[j])),abs(float(w[j])+.004*float(center[col])),.5e-6);L=min(max(L,math.nextafter((-sb-float(w[j]))/.004,-math.inf)),float(center[col]));U=max(min(U,math.nextafter((sb-float(w[j]))/.004,math.inf)),float(center[col]));newL.append(L);newU.append(U);delta=min(32e-9/mult,(U-L)/8);blend=4*delta/(U-L);seed[j]=(center[col]+blend*(L+.5*(U-L)-center[col]))/d['D'][j];L=math.nextafter(L+delta,math.inf);U=math.nextafter(U-delta,-math.inf)
    newlo[row]=mult*L;newhi[row]=mult*U
  newL=np.array(newL);newU=np.array(newU)
 recon=d['p']+d['Z']@(d['D']*seed);av=d['As']@seed;violation=max(0.,float(np.max(newlo-av)),float(np.max(av-newhi)));orig=q['A']@recon;origv=max(0.,float(np.max(q['l']-orig)),float(np.max(orig-q['u'])));hist=n['rounded_history'](before['x'],prev,before['b'],recon,[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40],q['labels'],q['l'],q['u'])
 jointrows=np.array([i for i,r in enumerate(d['rows'])if r>=0 and q['labels'][r][0].startswith('feedback_jerk/')and q['labels'][r][1]=='rad/s^3'],dtype=float);assert len(jointrows)==140
 fields=[d['Hs'],d['gs'],d['As'],d['ls'],d['us'],d['Fs'],d['D'],seed,d['rawx'],d['rawy'],d['p'],d['Z'],before['x'],prev,np.array([before['b']]),q['seed'],np.array([e['lower']for e in pg['first']]),np.array([e['upper']for e in pg['first']]),jointrows,can['U']];pack(B/('fixture'+str(cycle)+'.bin'),fields);pack(B/('hint'+str(cycle)+'.bin'),[hint['x'],hint['y']]);pack(B/('candidate'+str(cycle)+'.bin'),[newlo,newhi,seed,center,np.array([strict]),newL,newU,before['a'],np.array([int(eligible)])]);results.append({'cycle':cycle,'M':M,'eligible':eligible,'prefix_first_jerk_max':float(np.max(abs((a0-prev)/.004))),'prefix_second_jerk_max':float(np.max(abs(a0/.004))),'strict_radius':strict,'solver_radius':solver,'new_seed_scaled_violation':violation,'original_SI_seed_violation':origv,'history_failures':hist['failures'],'original_H_g_A_F_E_unchanged':True,'Model_calls':0})
bp.put(B/'PRECHECK_AND_FIXTURE_IDENTITIES.json',(json.dumps({'contexts':results,'scope':'Fixed ORIGINAL saved affine model; proposal source does not certify new genuine Model/B/C. Early retains old nominal, no uniform twozero.'},indent=2)+'\n').encode());print(json.dumps(results))
