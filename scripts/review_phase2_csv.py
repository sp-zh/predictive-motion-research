"""Coordinator's independent standard-library audit of delivered executed samples."""
import csv
import argparse
import json
import math
from pathlib import Path

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--input',type=Path,default=root/'results/phase2')
args=parser.parse_args()
base=args.input
def read(path):
    with path.open() as f:return list(csv.DictReader(f))
def vec(row,name,n):return [float(row[f'{name}_{j}']) for j in range(n)]
def close(a,b,tol=2e-9):
    if abs(a-b)>tol:raise ValueError(f'Mismatch {a} versus {b}')

summary={'scope':'independent artifact audit; not statistical superiority','groups':{},'samples':0}
for group,count in [('development',44),('evaluation',12),('weak_direction',6)]:
    directory=base/group
    bounds=read(directory/'bounds.csv');n=len(bounds)
    vmax=[float(b['velocity']) for b in bounds]
    low=[float(b['lower']) for b in bounds];high=[float(b['upper']) for b in bounds]
    trials=read(directory/'trials.csv');assert len(trials)==count
    codes={}
    for trial in trials:
        filename=f"{trial['kind']}_{trial['seed']}_{trial['method']}_{float(trial['damping']):.6f}.csv"
        rows=read(directory/filename);assert len(rows)==int(trial['steps'])==1500
        peak_position=peak_rotation=peak_raw=peak_accepted=peak_executed=0
        position_sum=rotation_sum=0;violations=0;interventions=0;previous=None
        for row in rows:
            q=vec(row,'executed_q',n);dq=vec(row,'executed_dq',n);raw=vec(row,'requested_dq',n);accepted=vec(row,'accepted_dq',n);target=vec(row,'accepted_q_target',n)
            assert all(math.isfinite(v) for v in q+dq+raw+accepted+target)
            dt=float(row['time_after'])-float(row['time_before']);close(dt,.004,1e-12)
            assert all(abs(v)<=limit+1e-10 for v,limit in zip(accepted,vmax))
            assert all(lo-1e-12<=v<=hi+1e-12 for v,lo,hi in zip(target,low,high))
            speed_violation=any(abs(v)>limit+1e-9 for v,limit in zip(dq,vmax))
            position_violation=any(v<lo-1e-9 or v>hi+1e-9 for v,lo,hi in zip(q,low,high))
            assert int(row['measured_velocity_violation'])==speed_violation
            assert int(row['measured_position_violation'])==position_violation
            violations+=speed_violation or position_violation
            interventions+=bool(int(row['velocity_intervention']) or int(row['position_intervention']))
            if previous:
                for v,old in zip(vec(row,'q_before',n),previous[0]):close(v,old,1e-12)
                for v,old,velocity in zip(target,previous[1],accepted):close((v-old)/dt,velocity,2e-9)
            previous=(q,target)
            xyz=vec(row,'actual_tcp_xyz',3);desired=vec(row,'desired_tcp_xyz',3)
            perror=math.sqrt(sum((a-b)**2 for a,b in zip(xyz,desired)))
            actual_quat=vec(row,'actual_tcp_xyzw',4);desired_quat=vec(row,'desired_tcp_xyzw',4)
            # atan2 quaternion relative-vector angle is stable near zero.
            ax,ay,az,aw=actual_quat;bx,by,bz,bw=desired_quat
            relative=[aw*bx-ax*bw-ay*bz+az*by,aw*by+ax*bz-ay*bw-az*bx,aw*bz-ax*by+ay*bx-az*bw]
            rw=aw*bw+ax*bx+ay*by+az*bz
            rerror=2*math.atan2(math.sqrt(sum(v*v for v in relative)),abs(rw))
            close(perror,float(row['position_error']),1e-12);close(rerror,float(row['rotation_error']),2e-9)
            position_sum+=perror;rotation_sum+=rerror
            peak_position=max(peak_position,perror);peak_rotation=max(peak_rotation,rerror)
            peak_raw=max(peak_raw,max(map(abs,raw)));peak_accepted=max(peak_accepted,max(map(abs,accepted)));peak_executed=max(peak_executed,max(map(abs,dq)))
        for key,value in [('mean_position_error',position_sum/len(rows)),('mean_rotation_error',rotation_sum/len(rows)),('peak_position_error',peak_position),('peak_rotation_error',peak_rotation),('raw_dq_max',peak_raw),('accepted_dq_max',peak_accepted),('executed_dq_max',peak_executed)]:close(value,float(trial[key]))
        assert interventions==int(trial['interventions'])
        if violations:assert trial['code']=='EXECUTED_LIMIT_VIOLATION'
        codes[trial['code']]=codes.get(trial['code'],0)+1
        summary['samples']+=len(rows)
    summary['groups'][group]={'trials':count,'codes':codes}
summary['status']='PASS'
(base/'root_csv_review.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
