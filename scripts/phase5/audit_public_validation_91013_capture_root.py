#!/usr/bin/env python3
"""Independent complete recorded-state/QP/history and window-roster audit.

No producer scorer or predictor import, plant call, refit or numerical forecast.
Every exported row is recomputed with math.fsum; geometry tail completeness and
per-solve H/g remain unverified logging limitations.
"""
import argparse,csv,hashlib,json,math,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import yaml

SHA=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
DT=.004;SUBDT=.002

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 root=Path('/home/codextransfer/predictive_motion');packet=root/'results/phase5/development/public-coupled-validation-91013-protocol-v2';run=root/'results/phase5/development/public-coupled-v2-development-validation-91013';raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013')
 source=Path(__file__);source_bytes=source.read_bytes();out=a.output;out.mkdir(parents=True,exist_ok=False)
 assert SHA(packet/'frozen.json')=='190b05049892a27923778475e8287a7814854455d1fa55d722d14094245b814d'
 freeze=json.loads((packet/'frozen.json').read_text());protocol=json.loads((packet/'protocol.json').read_text());execution=json.loads((run/'execution.json').read_text());assert execution['return_code']==0 and execution['source_unchanged'] is True and execution['prepared_frozen_sha256']==SHA(packet/'frozen.json')
 hashes={name:SHA(raw/name) for name in ['raw.csv','cycles.csv','summary.yaml','all_qp_solves.csv','all_qp_rows.csv']};assert hashes=={name:execution['raw_files'][name] for name in hashes};assert hashes['raw.csv']=='ea70d9e8b01bc6e44387e2f4701779243bb1b202020a61aef18312fac1c054e8'
 for key in ['public_model_constants','robot_urdf','phase4_config']:
  assert SHA(protocol[key])==freeze['files'][protocol[key]]
 constants=json.loads(Path(protocol['public_model_constants']).read_text());joints={j.attrib['name']:j for j in ET.parse(protocol['robot_urdf']).getroot().findall('joint')};flat_ranges=constants['joint_range'];assert len(flat_ranges)==14;ranges=[flat_ranges[2*j:2*j+2] for j in range(7)];lower=[max(ranges[j][0],float(joints[name].find('limit').attrib['lower'])) for j,name in enumerate(constants['joint_names'])];upper=[min(ranges[j][1],float(joints[name].find('limit').attrib['upper'])) for j,name in enumerate(constants['joint_names'])];physical_v=yaml.safe_load(Path(protocol['phase4_config']).read_text())['velocity_rad_s']
 with (raw/'raw.csv').open() as f:rows=list(csv.DictReader(f))
 assert len(rows)%2==0;cycles_count=len(rows)//2;assert 2501<=cycles_count<=3750
 phases=lambda t:'warmup' if t<500 else 'reference_motion' if t<695 else 'reference_recorded_stop' if t<928 else 'hold' if t<2500 else 'new_shared_stop'
 def vector(r,p):
  values=[float(r[p+str(j)]) for j in range(7)];assert all(math.isfinite(x) for x in values);return values
 cprev=vector(rows[0],'q_before_');wprev=[0.]*7;aprev=[0.]*7;phys_aprev=[0.]*7;prev_q=prev_v=None;minclear=math.inf;maxv=maxa=maxj=0.;minrecovery=math.inf
 for i,r in enumerate(rows):
  t=i//2;assert int(r['tick'])==t and int(r['substep'])==i%2+1 and r['phase']==phases(t) and abs(float(r['time_s'])-(i+1)*SUBDT)<=1e-10 and int(r['contacts'])==0
  clear=float(r['true_clearance_m']);assert math.isfinite(clear) and clear>=.005;minclear=min(minclear,clear)
  q,v,c,qp,vp,w,alpha,jerk,pa,pj=[vector(r,p) for p in ['q_before_','v_before_','target_','q_post_','v_post_','command_velocity_','command_acceleration_','command_jerk_','physical_acceleration_','physical_jerk_']]
  if i:assert q==prev_q and v==prev_v
  assert all(lower[j]<=qp[j]<=upper[j] and abs(vp[j])<=physical_v[j] for j in range(7));maxv=max(maxv,*map(abs,vp))
  assert max(abs((vp[j]-v[j])/SUBDT-pa[j]) for j in range(7))<2e-10
  assert max(abs((pa[j]-phys_aprev[j])/SUBDT-pj[j]) for j in range(7))<2e-8
  if t>=500:
   assert max(map(abs,pa))<=5 and max(map(abs,pj))<=500;maxa=max(maxa,*map(abs,pa));maxj=max(maxj,*map(abs,pj))
  if i%2==0:
   if t<500:assert c==cprev and w==wprev==[0.]*7 and alpha==aprev==[0.]*7 and jerk==[0.]*7
   else:
    assert max(abs(c[j]-cprev[j]-DT*w[j]) for j in range(7))<1e-13
    assert max(abs(alpha[j]-(w[j]-wprev[j])/DT) for j in range(7))<1e-13
    assert max(abs(jerk[j]-(alpha[j]-aprev[j])/DT) for j in range(7))<1e-11
    assert max(map(abs,w))<=.0625 and max(map(abs,alpha))<=1 and max(map(abs,jerk))<=20+1e-7+1e-11
    for speed,acc in zip(w,alpha):
     recovery=DT*math.fsum(max(abs(acc)-DT*20*k,0) for k in range(1,15));margin=.0625-math.copysign(1,acc)*speed-recovery;assert margin>=-1e-12;minrecovery=min(minrecovery,margin)
   cprev,wprev,aprev=c,w,alpha
  else:
   for prefix,values in [('target_',c),('command_velocity_',w),('command_acceleration_',alpha),('command_jerk_',jerk)]:assert values==vector(rows[i-1],prefix)
  prev_q,prev_v,phys_aprev=qp,vp,pa
 assert max(map(abs,wprev))<1e-6 and max(map(abs,prev_v))<1e-4
 summary=yaml.safe_load((raw/'summary.yaml').read_text());assert summary['seed']==91013 and summary['completed_stop'] is True and summary['primary_failure']==summary['stop_failure']=='' and abs(summary['min_clearance_m']-minclear)<2e-12 and abs(summary['max_physical_velocity_rad_s']-maxv)<2e-12
 expected=[(t,k) for t in range(500,cycles_count) for k in (['tracking'] if t<2500 else ['tracking','stop'])];points={};si={};indices={};reported={}
 with (raw/'all_qp_solves.csv').open() as f:solves=list(csv.DictReader(f))
 assert len(solves)==len(expected)
 for r,key in zip(solves,expected):
  actual=(int(r['tick']),r['kind']);assert actual==key and key not in points;assert r['wrapper_status']=='SOLVED' and int(r['raw_status'])==1 and int(r['api_error'])==0 and int(r['candidate_size'])==7
  points[key]=vector(r,'x');si[key]=0.;indices[key]=0;reported[key]=float(r['SI_violation']);assert math.isfinite(reported[key]) and 0<=reported[key]<=1e-7
 for t in range(500,cycles_count):assert vector(rows[2*t],'command_velocity_')==points[(t,'tracking' if t<2500 else 'stop')]
 row_order=[]
 with (raw/'all_qp_rows.csv').open() as f:
  for r in csv.DictReader(f):
   key=(int(r['tick']),r['kind']);assert key in points and int(r['row'])==indices[key]
   if not row_order or key!=row_order[-1]:row_order.append(key)
   A=vector(r,'A');products=[x*y for x,y in zip(A,points[key])];assert all(math.isfinite(x) for x in products);value=math.fsum(products);assert math.isfinite(value)
   lo,hi=float(r['lower']),float(r['upper']);assert math.isfinite(lo) and not math.isnan(hi) and hi!=-math.inf and lo<=hi
   assert indices[key]>=119 or math.isfinite(hi)
   si[key]=max(si[key],lo-value,value-hi);indices[key]+=1
 assert row_order==expected and min(indices.values())>=119 and max(si.values())<=1e-7
 assert max(abs(si[k]-reported[k]) for k in expected)<1e-12
 with (raw/'cycles.csv').open() as f:cycles=list(csv.DictReader(f))
 assert len(cycles)==cycles_count
 for t,r in enumerate(cycles):
  wall,age=float(r['full_cycle_wall_s']),float(r['command_age_s']);assert int(r['tick'])==t and r['status']==('HOLD' if t<500 else 'SOLVED') and math.isfinite(wall) and math.isfinite(age) and 0<=age<=.05 and age<=wall+1e-12 and int(r['deadline_miss'])==int(wall>DT)
 roster=[]
 for count in [1,2,20,400]:
  starts=list(range(0,len(rows)-count+1,2))
  for scope in ['active','warmup']:
   selected=[i for i in starts if (i>=1000)==(scope=='active')]
   roster.append({'scope':scope,'duration_s':count*SUBDT,'windows':len(selected),'start_phase_counts':dict(Counter(rows[i]['phase'] for i in selected)),'windows_intersecting_phase':{p:sum(any(rows[k]['phase']==p for k in range(i,i+count)) for i in selected) for p in ['reference_motion','reference_recorded_stop','hold','new_shared_stop']},'hold_only_windows':sum(all(rows[k]['phase']=='hold' for k in range(i,i+count)) for i in selected)})
 assert hashes=={name:SHA(raw/name) for name in hashes} and source.read_bytes()==source_bytes
 result={'decision':'PASS_INDEPENDENT_RECORDED_CAPTURE_QP_HISTORY_AND_ROSTER','scope':'Complete recorded audit and window roster, not numerical full-window forecasts; no new plant or Phase5 acceptance. Exact geometry tail count/options and per-solve H/g remain unverified.','source_sha256':hashlib.sha256(source_bytes).hexdigest(),'capture_sha256':hashes,'rows':len(rows),'cycles':cycles_count,'actual_qp_attempts':len(solves),'actual_qp_rows':sum(indices.values()),'phase_rows':dict(Counter(r['phase'] for r in rows)),'actual_original_SI_max':max(si.values()),'minimum_signed_recovery_margin':minrecovery,'minimum_clearance_m':minclear,'max_physical_velocity_rad_s':maxv,'max_active_physical_acceleration_rad_s2':maxa,'max_active_physical_jerk_rad_s3':maxj,'terminal_physical_speed_rad_s':max(map(abs,prev_v)),'terminal_command_speed_rad_s':max(map(abs,wprev)),'max_cycle_wall_s':max(float(r['full_cycle_wall_s']) for r in cycles),'full4ms_deadline_misses':sum(int(r['deadline_miss']) for r in cycles),'window_roster':roster}
 (out/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');(out/'SOURCE_SNAPSHOT.py').write_bytes(source_bytes)
 files={p.name:{'sha256':SHA(p),'bytes':p.stat().st_size} for p in out.iterdir() if p.is_file()};(out/'READY.json').write_text(json.dumps({'files':files,'scope':result['scope']},indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
