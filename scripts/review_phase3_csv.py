"""Coordinator's independent stdlib audit of all Phase 3 executed records."""
import csv
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = root/'results/phase3'
def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))
def vec(row, name, n):
    return [float(row[f'{name}_{j}']) for j in range(n)]
def close(a, b, tol=1e-9):
    assert math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tol, (a,b,tol)
summary = {'status':'PASS','scope':'independent state/guard/objective/aggregate/failure audit; FK and projector audits separate','groups':{},'samples':0}
for group, count in [('development',104),('evaluation',40)]:
    directory = base/group
    bounds = read(directory/'bounds.csv')
    n = len(bounds)
    lo = [float(x['lower']) for x in bounds]
    hi = [float(x['upper']) for x in bounds]
    vmax = [float(x['velocity']) for x in bounds]
    span = [b-a for a,b in zip(lo,hi)]
    center = [a+r/2 for a,r in zip(lo,span)]
    objective = lambda q: sum(((v-c)/r)**2 for v,c,r in zip(q,center,span))
    margin = lambda q: min(min(v-a,b-v)/r for v,a,b,r in zip(q,lo,hi,span))
    trials = read(directory/'trials.csv')
    assert len(trials) == count
    codes = {}
    for trial in trials:
        name = f"{trial['case']}_{trial['reference']}_{trial['seed']}_{trial['objective']}_{float(trial['gain']):.6f}.csv"
        rows = read(directory/name)
        assert len(rows) == int(trial['steps']) == 1500
        previous = None
        psum=rsum=ppeak=rpeak=rawpeak=acceptedpeak=executedpeak=0
        vvcount=pvcount=interventions=0
        for row in rows:
            q=vec(row,'q_before',n);actual=vec(row,'executed_q',n);speed=vec(row,'executed_dq',n)
            primary=vec(row,'primary_dq',n);secondary=vec(row,'secondary_dq',n)
            raw=vec(row,'requested_dq',n);accepted=vec(row,'accepted_dq',n);target=vec(row,'accepted_q_target',n)
            assert all(math.isfinite(v) for v in q+actual+speed+primary+secondary+raw+accepted+target)
            dt=float(row['time_after'])-float(row['time_before']);close(dt,.004,1e-12)
            for v,a,b in zip(raw,primary,secondary):close(v,a+b,1e-12)
            assert all(abs(v)<=limit+1e-9 for v,limit in zip(accepted,vmax))
            assert all(a-1e-12<=v<=b+1e-12 for v,a,b in zip(target,lo,hi))
            if previous:
                for a,b in zip(q,previous[0]):close(a,b,1e-12)
                for v,old,dq in zip(target,previous[1],accepted):close((v-old)/dt,dq,2e-9)
            previous=(actual,target)
            close(objective(q),float(row['H_joint']),1e-12)
            close(margin(q),float(row['min_normalized_margin']),1e-12)
            derivative=sum(2*(v-c)/r**2*dq for v,c,r,dq in zip(q,center,span,secondary))
            close(derivative,float(row['joint_directional_derivative']),1e-10)
            if trial['objective']=='joint':assert derivative<=1e-10
            vv=any(abs(v)>limit+1e-9 for v,limit in zip(speed,vmax))
            pv=any(v<a-1e-9 or v>b+1e-9 for v,a,b in zip(actual,lo,hi))
            assert vv==bool(int(row['measured_velocity_violation'])) and pv==bool(int(row['measured_position_violation']))
            vvcount+=vv;pvcount+=pv
            interventions+=bool(int(row['velocity_intervention']) or int(row['position_intervention']))
            xyz=vec(row,'actual_tcp_xyz',3);desired=vec(row,'desired_tcp_xyz',3)
            pe=math.sqrt(sum((a-b)**2 for a,b in zip(xyz,desired)))
            ax,ay,az,aw=vec(row,'actual_tcp_xyzw',4);bx,by,bz,bw=vec(row,'desired_tcp_xyzw',4)
            relative=[aw*bx-ax*bw-ay*bz+az*by,aw*by+ax*bz-ay*bw-az*bx,aw*bz-ax*by+ay*bx-az*bw]
            re=2*math.atan2(math.sqrt(sum(v*v for v in relative)),abs(aw*bw+ax*bx+ay*by+az*bz))
            close(pe,float(row['position_error']),1e-12);close(re,float(row['rotation_error']),1e-10)
            psum+=pe;rsum+=re;ppeak=max(ppeak,pe);rpeak=max(rpeak,re)
            rawpeak=max(rawpeak,max(map(abs,raw)));acceptedpeak=max(acceptedpeak,max(map(abs,accepted)));executedpeak=max(executedpeak,max(map(abs,speed)))
        for key,value in [('mean_position_error',psum/len(rows)),('mean_rotation_error',rsum/len(rows)),('peak_position_error',ppeak),('peak_rotation_error',rpeak),('raw_dq_max',rawpeak),('accepted_dq_max',acceptedpeak),('executed_dq_max',executedpeak),('final_H',objective(previous[0])),('final_min_margin',margin(previous[0]))]:close(value,float(trial[key]),1e-9)
        assert vvcount==int(trial['measured_velocity_violations']) and pvcount==int(trial['measured_position_violations']) and interventions==int(trial['interventions'])
        expected='EXECUTED_LIMIT_VIOLATION' if vvcount or pvcount else ('POSE_TOLERANCE_FAILURE' if pe>.01 or re>.05 or ppeak>.05 or rpeak>.2 else 'COMPLETED')
        assert trial['code']==expected
        codes[expected]=codes.get(expected,0)+1
        summary['samples']+=len(rows)
    summary['groups'][group]={'trials':count,'codes':codes}
(base/'root_csv_review.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
