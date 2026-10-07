#!/usr/bin/env python3
"""Independently audit recorded servo identification; never fit or simulate a plant."""
import argparse,csv,hashlib,json,math,re
from pathlib import Path
import xml.etree.ElementTree as ET

def audit(case,urdf):
    execution=json.loads((case/'execution.json').read_text())
    frozen=json.loads((case/'frozen.json').read_text())['files']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for name,h in execution['raw_files'].items():
        if sha(case/'raw'/name)!=h:raise ValueError('raw identity changed')
    for p,suffix in [(urdf,'/models/fr3/fr3_arm.urdf'),(case/'servo_identification.yaml','/config/phase5_development/servo_identification.yaml')]:
        matches=[h for n,h in frozen.items() if n.endswith(suffix)]
        if len(matches)!=1 or sha(p)!=matches[0]:raise ValueError('protocol/URDF identity mismatch')
    text=(case/'servo_identification.yaml').read_text()
    def scalar(key):
        matches=re.findall(r'^'+re.escape(key)+r':\s*([^\n]+)$',text,re.M)
        if len(matches)!=1:raise ValueError('missing scalar '+key)
        return float(matches[0])
    dt,subdt=scalar('control_dt_s'),scalar('physics_substep_s')
    warmup=round(scalar('warmup_s')/dt);tol=scalar('solver_acceptance_tolerance')+1e-8
    joints={j.attrib['name']:j.find('limit').attrib for j in ET.parse(urdf).getroot().findall('joint') if j.attrib.get('type')=='revolute'}
    limits=[joints['fr3_joint'+str(j+1)] for j in range(7)]
    rows=list(csv.DictReader((case/'raw/raw.csv').open()));cycles=list(csv.DictReader((case/'raw/cycles.csv').open()))
    errors={k:0. for k in ['time','state_chain','physical_acceleration','physical_jerk','target_integrator','command_acceleration','command_jerk','same_cycle_command']}
    violations={k:0 for k in ['nonfinite','URDF_position','URDF_velocity','command_target_URDF_margin','command_velocity','command_acceleration','command_jerk','physical_acceleration','physical_jerk','contact','clearance','command_age','solver_status']}
    peaks={k:0. for k in ['command_velocity','command_acceleration','command_jerk','physical_velocity','physical_acceleration','physical_jerk']}
    vector=lambda r,p:[float(r[p+str(j)]) for j in range(7)]
    maxerr=lambda a,b:max(abs(x-y) for x,y in zip(a,b))
    previous=None;previous_a=[0.]*7;previous_w=[0.]*7;previous_ca=[0.]*7;previous_target=vector(rows[0],'target_')
    for i,r in enumerate(rows):
        tick,sub=int(r['tick']),int(r['substep'])
        if tick!=i//2 or sub!=i%2+1:raise ValueError('noncontiguous substeps')
        numeric=[float(v) for v in r.values() if v!=r['phase']]
        violations['nonfinite']+=not all(math.isfinite(v) for v in numeric)
        errors['time']=max(errors['time'],abs(float(r['time_s'])-(i+1)*subdt))
        qb,vb=vector(r,'q_before_'),vector(r,'v_before_');q,v=vector(r,'q_post_'),vector(r,'v_post_')
        w,ca,cj=vector(r,'command_velocity_'),vector(r,'command_acceleration_'),vector(r,'command_jerk_')
        pa,pj=vector(r,'physical_acceleration_'),vector(r,'physical_jerk_');target=vector(r,'target_')
        if previous:errors['state_chain']=max(errors['state_chain'],maxerr(qb,vector(previous,'q_post_')),maxerr(vb,vector(previous,'v_post_')))
        errors['physical_acceleration']=max(errors['physical_acceleration'],maxerr(pa,[(x-y)/subdt for x,y in zip(v,vb)]))
        errors['physical_jerk']=max(errors['physical_jerk'],maxerr(pj,[(x-y)/subdt for x,y in zip(pa,previous_a)]))
        if sub==1:
            errors['target_integrator']=max(errors['target_integrator'],maxerr(target,[x+dt*y for x,y in zip(previous_target,w)]))
            errors['command_acceleration']=max(errors['command_acceleration'],maxerr(ca,[(x-y)/dt for x,y in zip(w,previous_w)]))
            errors['command_jerk']=max(errors['command_jerk'],maxerr(cj,[(x-y)/dt for x,y in zip(ca,previous_ca)]))
            previous_target,previous_w,previous_ca=target,w,ca
        else:
            for prefix in ['target_','command_velocity_','command_acceleration_','command_jerk_']:
                errors['same_cycle_command']=max(errors['same_cycle_command'],maxerr(vector(r,prefix),vector(previous,prefix)))
        violations['contact']+=int(r['contacts'])!=0;violations['clearance']+=float(r['true_clearance_m'])<scalar('collision_safe_m')-1e-8
        for j,l in enumerate(limits):
            violations['URDF_position']+=q[j]<float(l['lower'])-1e-8 or q[j]>float(l['upper'])+1e-8
            violations['URDF_velocity']+=abs(v[j])>float(l['velocity'])+1e-8
            if tick>=warmup:
                margin=scalar('position_margin_rad')
                violations['command_target_URDF_margin']+=target[j]<float(l['lower'])+margin-tol or target[j]>float(l['upper'])-margin+tol
        if tick>=warmup:
            for name,values,key in [('command_velocity',w,'command_velocity_rad_s'),('command_acceleration',ca,'command_acceleration_rad_s2'),('command_jerk',cj,'command_jerk_rad_s3'),('physical_acceleration',pa,'executed_acceleration_rad_s2'),('physical_jerk',pj,'executed_jerk_rad_s3')]:
                peak=max(abs(x) for x in values);peaks[name]=max(peaks[name],peak);violations[name]+=peak>scalar(key)+tol
            peaks['physical_velocity']=max(peaks['physical_velocity'],max(abs(x) for x in v))
        previous,previous_a=r,pa
    for c in cycles:
        if int(c['tick'])>=warmup:
            violations['command_age']+=not 0<=float(c['command_age_s'])<=.05
            violations['solver_status']+=c['status']!='SOLVED'
    if len(cycles)*2!=len(rows):raise ValueError('cycle/substep mismatch')
    result={'scope':'Independent recorded identification fixture checks only. No model fit, holdout accuracy, task/retiming, full MJCF limit intersection, hardware or real-time claim. URDF bounds and frozen protocol only.','status':'PASS' if not any(violations.values()) and max(errors.values())<1e-8 else 'FAIL','rows':len(rows),'active_substeps':sum(int(r['tick'])>=warmup for r in rows),'raw_sha256':sha(case/'raw/raw.csv'),'protocol_sha256':sha(case/'servo_identification.yaml'),'urdf_sha256':sha(urdf),'violations':violations,'recomputed_history_errors':errors,'active_peaks':peaks,'final':{'physical_velocity_max':max(abs(x) for x in vector(rows[-1],'v_post_')),'command_velocity_max':max(abs(x) for x in vector(rows[-1],'command_velocity_')),'command_acceleration_max':max(abs(x) for x in vector(rows[-1],'command_acceleration_'))},'min_recorded_clearance_m':min(float(r['true_clearance_m']) for r in rows),'active_full_cycle_4ms_misses':sum(float(c['full_cycle_wall_s'])>dt for c in cycles if int(c['tick'])>=warmup),'active_full_cycle_max_s':max(float(c['full_cycle_wall_s']) for c in cycles if int(c['tick'])>=warmup),'script_sha256':sha(Path(__file__))}
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--urdf',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('Refuse overwrite')
    result=audit(a.case,a.urdf);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
