#!/usr/bin/env python3
"""Strict recorded-data gate, then frozen public-model conditional forecasts.

The test-only Python model_factory isolates gate logic; the CLI always uses
the frozen public model. Neither path authorizes or executes a plant run.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import argparse
import csv
import hashlib
import json
import math
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import yaml

PREFIXES = ['q_before_', 'v_before_', 'target_', 'q_post_', 'v_post_',
            'command_velocity_', 'command_acceleration_', 'command_jerk_',
            'physical_acceleration_', 'physical_jerk_']
RAW_FIELDS = ['tick', 'substep', 'time_s', 'phase', 'contacts', 'true_clearance_m'] + [p+str(j) for p in PREFIXES for j in range(7)]
CYCLE_FIELDS = ['tick', 'full_cycle_wall_s', 'command_age_s', 'status', 'deadline_miss']
SOLVE_FIELDS = ['tick', 'kind', 'wrapper_status', 'raw_status', 'api_error', 'iterations', 'SI_violation', 'maximum_violation_row', 'candidate_size', 'state_age_s', 'setup_s', 'solve_s'] + ['x'+str(j) for j in range(7)]
ROW_FIELDS = ['tick', 'kind', 'row', 'lower', 'upper'] + ['A'+str(j) for j in range(7)]
CONSUMED = ['raw.csv', 'summary.yaml', 'cycles.csv', 'all_qp_solves.csv', 'all_qp_rows.csv']
DT, SUBDT, V, ACC, JERK, SI = .004, .002, .0625, 1., 20., 1e-7
HORIZONS = [(1, 1e-6, 1e-4), (2, 1e-6, 1e-4), (20, 1e-4, 1e-3), (400, 1e-4, 1e-3)]
LIMITATIONS = ['Exact geometry tail-row count and per-solve solver options are not exported; continuous recorded indices and source-defined base rows cannot detect a missing final geometry row.', 'H/g are frozen source/reference-defined, not captured per accepted solve.', 'Hashes bind the supplied capture to its execution record; they do not authenticate a dishonest producer or certify unlogged forces/nonlinear guard evaluations.']

class IntegrityError(ValueError):
    pass

def need(condition, message):
    if not condition:
        raise IntegrityError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_json(path):
    return json.loads(Path(path).read_text(), parse_constant=lambda value: (_ for _ in ()).throw(IntegrityError('nonfinite JSON: '+value)))

def integer(value, label):
    try:
        n = int(value)
        need(str(n) == str(value), 'noncanonical integer '+label)
        return n
    except (ValueError, TypeError) as exc:
        raise IntegrityError('invalid integer '+label) from exc

def number(value, label, finite=True):
    try:
        x = float(value)
    except (ValueError, TypeError) as exc:
        raise IntegrityError('invalid number '+label) from exc
    need(math.isfinite(x) if finite else not math.isnan(x), 'nonfinite/NaN '+label)
    return x

def table(path, fields):
    with Path(path).open(newline='') as file:
        reader = csv.DictReader(file)
        need(reader.fieldnames == fields, 'CSV schema '+Path(path).name)
        rows = list(reader)
    need(all(None not in r and all(v is not None and v != '' for v in r.values()) for r in rows), 'missing/extra CSV cells '+Path(path).name)
    return rows

def near(a, b, label, atol=2e-12):
    need(np.isfinite(a).all() and np.isfinite(b).all() and np.allclose(a, b, atol=atol, rtol=0), label)

def phase(tick):
    return 'warmup' if tick < 500 else 'reference_motion' if tick < 695 else 'reference_recorded_stop' if tick < 928 else 'hold' if tick < 2500 else 'new_shared_stop'

def base_rows(q, c, w, alpha, lower, upper):
    """Same order/arithmetic contract as frozen C++ constrainers; no geometry."""
    eye = np.eye(7); rows = []
    for j in range(7):
        lo = max(-V, (lower[j]+.005-q[j])/DT, (lower[j]+.005-c[j])/DT, w[j]-ACC*DT, w[j]+DT*alpha[j]-JERK*DT*DT)
        hi = min(V, (upper[j]-.005-q[j])/DT, (upper[j]-.005-c[j])/DT, w[j]+ACC*DT, w[j]+DT*alpha[j]+JERK*DT*DT)
        rows.append((eye[j], lo, hi))
    inv = 1/DT; inv2 = inv*inv
    for j in range(7):
        ac = w[j]*inv; jc = w[j]*inv2+alpha[j]*inv
        rows += [(eye[j]*inv, ac-ACC, ac+ACC), (eye[j]*inv2, jc-JERK, jc+JERK)]
    for j in range(7):
        for k in range(1, 15):
            recovery = np.longdouble(.5)*np.longdouble(JERK)*np.longdouble(DT)**2*k*(k-1)
            offset = (k-1)*np.longdouble(w[j])
            rows.append((eye[j]*k, float(offset-np.longdouble(V)-recovery), float(offset+np.longdouble(V)+recovery)))
    need(len(rows) == 119, 'base row construction')
    return rows

def continuable(w, alpha):
    for velocity, acceleration in zip(w, alpha):
        if abs(velocity) > V or abs(acceleration) > ACC:
            return False
        def recovery(distance):
            if distance < 0:
                return float('nan')
            n = max(0., math.sqrt(2*distance/JERK)/DT-1)
            f = lambda k: distance/(DT*(k+1))+.5*JERK*DT*k
            exact = min(f(math.floor(n)), f(math.ceil(n)))
            return 0. if distance == 0 else max(0., exact-64*np.finfo(float).eps*max(abs(exact), JERK*DT))
        lo = max(-ACC, acceleration-JERK*DT, -recovery(velocity+V))
        hi = min(ACC, acceleration+JERK*DT, recovery(V-velocity))
        if not math.isfinite(lo+hi) or lo > hi:
            return False
    return True

def inspect_capture(packet, raw, execution_path):
    freeze = load_json(packet/'frozen.json'); protocol = load_json(packet/'protocol.json'); execution = load_json(execution_path)
    need(freeze['seed'] == 91013 and protocol['seed'] == 91013 and protocol['schema'] == 2, 'protocol seed/schema')
    need(execution['prepared_frozen_sha256'] == sha(packet/'frozen.json'), 'execution frozen identity')
    need(execution['return_code'] == 0 and execution['source_unchanged'] is True, 'collector failure/source mutation')
    expected_argv = [protocol['collector'], protocol['project_root'], protocol['collector_configuration'], 'predictive', 'servo_validation', '91013', str(raw.parent)]
    need(execution['argv'] == expected_argv, 'collector argv contract')
    for path, digest in freeze['files'].items():
        need(sha(path) == digest, 'frozen input SHA '+path)
    need(freeze['files'].get(str(packet/'protocol.json')) == sha(packet/'protocol.json'), 'protocol absent from frozen inputs')
    for key in ['public_model_source', 'public_model_constants', 'robot_urdf', 'phase4_config', 'model_xml', 'collector_configuration', 'collector']:
        need(protocol[key] in freeze['files'], 'consumed input not frozen '+key)
    need(protocol['horizons'] == [{'substeps':n,'q_limit_rad':q,'v_limit_rad_s':v} for n,q,v in HORIZONS], 'original accuracy limits')
    cfg = yaml.safe_load(Path(protocol['collector_configuration']).read_text())
    for key, value in {'control_dt_s':DT,'physics_substep_s':SUBDT,'collision_safe_m':.005,'identification_duration_s':8.,'command_velocity_rad_s':V,'command_acceleration_rad_s2':ACC,'command_jerk_rad_s3':JERK,'position_margin_rad':.005,'qp_stopping_tolerance':1e-12}.items():
        need(cfg[key] == value, 'collector configuration '+key)
    captured = {}
    for name in CONSUMED:
        need(execution['raw_files'].get(name) == sha(raw.with_name(name)), 'capture SHA '+name)
        captured[name] = sha(raw.with_name(name))
    summary = yaml.safe_load(raw.with_name('summary.yaml').read_text())
    need(isinstance(summary, dict) and summary['completed_stop'] is True and summary['seed'] == 91013 and summary['fixture'] == 'servo_validation' and summary['primary_failure'] == '' and summary['stop_failure'] == '', 'summary incomplete/failure/seed')
    rows = table(raw, RAW_FIELDS); cycles = table(raw.with_name('cycles.csv'), CYCLE_FIELDS)
    solves = table(raw.with_name('all_qp_solves.csv'), SOLVE_FIELDS); qprows = table(raw.with_name('all_qp_rows.csv'), ROW_FIELDS)
    n = len(cycles)
    need(2501 <= n <= 3750 and len(rows) == 2*n, 'complete phase/cycle/raw roster')
    for i,r in enumerate(rows):
        need(integer(r['tick'],'tick') == i//2 and integer(r['substep'],'substep') == i%2+1 and r['phase'] == phase(i//2), 'raw clock/phase roster')
        need(abs(number(r['time_s'],'time')-(i+1)*SUBDT) <= 1e-10, 'raw time continuity')
        need(integer(r['contacts'],'contacts') == 0 and number(r['true_clearance_m'],'clearance') >= .005, 'contact/clearance regime')
    data = {prefix:np.array([[number(r[prefix+str(j)],prefix+str(j)) for j in range(7)] for r in rows]) for prefix in PREFIXES}
    q,v,c,qp,vp,w,alpha,jcmd,ap,jp = [data[p] for p in PREFIXES]
    near(q[1:], qp[:-1], 'q state continuity', 0); near(v[1:], vp[:-1], 'v state continuity', 0)
    for x in [c,w,alpha,jcmd]:
        near(x[::2], x[1::2], 'held two-substep command', 0)
    near(c[:1000], np.broadcast_to(q[0],(1000,7)), 'warmup target', 0)
    for x in [w,alpha,jcmd]:
        near(x[:1000], np.zeros((1000,7)), 'warmup command history', 0)
    near((vp-v)/SUBDT, ap, 'physical acceleration consistency', 2e-10)
    near((ap-np.vstack([np.zeros(7),ap[:-1]]))/SUBDT, jp, 'physical jerk consistency', 2e-8)
    constants = load_json(protocol['public_model_constants']); urdf = ET.parse(protocol['robot_urdf']).getroot()
    joints = {j.attrib['name']:j for j in urdf.findall('joint')}; mjrange = np.array(constants['joint_range']).reshape(7,2)
    lower = np.array([max(float(joints[name].find('limit').attrib['lower']), mjrange[j,0]) for j,name in enumerate(constants['joint_names'])])
    upper = np.array([min(float(joints[name].find('limit').attrib['upper']), mjrange[j,1]) for j,name in enumerate(constants['joint_names'])])
    phase4 = yaml.safe_load(Path(protocol['phase4_config']).read_text()); physical_v = np.array(phase4['velocity_rad_s'])
    need(physical_v.shape == (7,) and np.isfinite(physical_v).all(), 'physical velocity contract')
    need(np.all(qp >= lower) and np.all(qp <= upper) and np.all(abs(vp) <= physical_v), 'executed physical q/v guards')
    need(np.all(abs(ap[1000:]) <= 5.) and np.all(abs(jp[1000:]) <= 500.), 'executed physical acceleration/jerk guards')
    near(c[1000::2], c[998:-2:2]+DT*w[1000::2], 'accepted position integration', 1e-13)
    near(alpha[1000::2], (w[1000::2]-w[998:-2:2])/DT, 'accepted acceleration history', 1e-13)
    near(jcmd[1000::2], (alpha[1000::2]-alpha[998:-2:2])/DT, 'accepted jerk history', 1e-11)
    need(np.all(abs(w) <= V) and np.all(abs(alpha) <= ACC) and np.all(abs(jcmd) <= JERK+SI+1e-11), 'accepted derivative limits')
    need(all(continuable(ww,aa) for ww,aa in zip(w[1000::2],alpha[1000::2])), 'accepted history continuation')
    need(abs(w[-1]).max() < 1e-6 and abs(vp[-1]).max() < 1e-4, 'terminal shared stop')
    need(not any(abs(w[2*t]).max() < 1e-6 and abs(vp[2*t+1]).max() < 1e-4 for t in range(2500,n-1)), 'trace after first completed stop')
    near(number(summary['min_clearance_m'],'summary clearance'), min(number(r['true_clearance_m'],'clearance') for r in rows), 'summary clearance consistency')
    near(number(summary['max_physical_velocity_rad_s'],'summary velocity'), abs(vp).max(), 'summary velocity consistency')
    maxage = 0.; missed = 0
    for t,r in enumerate(cycles):
        need(integer(r['tick'],'cycle tick') == t and r['status'] == ('HOLD' if t < 500 else 'SOLVED'), 'cycle roster/status')
        wall = number(r['full_cycle_wall_s'],'wall'); age = number(r['command_age_s'],'command age'); miss = integer(r['deadline_miss'],'deadline flag')
        need(wall >= 0 and 0 <= age <= .05 and age <= wall+1e-12 and miss == int(wall > DT), 'cycle wall/age/deadline')
        need(t >= 500 or age == 0, 'warmup command age')
        maxage = max(maxage,age); missed += miss
    expected_keys = {(t,'tracking') for t in range(500,n)} | {(t,'stop') for t in range(2500,n)}
    points = {}; ordered = [(t,k) for t in range(500,n) for k in (['tracking'] if t < 2500 else ['tracking','stop'])]
    need(len(solves) == len(ordered), 'attempt roster length')
    for r,key in zip(solves,ordered):
        current = (integer(r['tick'],'attempt tick'),r['kind'])
        need(current == key and current not in points, 'attempt uniqueness/order/coverage')
        need(r['wrapper_status'] == 'SOLVED' and integer(r['raw_status'],'native status') == 1 and integer(r['api_error'],'API status') == 0 and integer(r['candidate_size'],'candidate size') == 7, 'native/API/candidate rejection')
        x = np.array([number(r['x'+str(j)],'candidate') for j in range(7)])
        need(continuable(x,(x-w[2*key[0]-2])/DT), 'all-attempt candidate continuation')
        need(0 <= integer(r['iterations'],'iterations') <= 4000 and 0 <= number(r['SI_violation'],'reported SI') <= SI, 'iteration/reported SI')
        age,setup,solve = [number(r[k],k) for k in ['state_age_s','setup_s','solve_s']]
        need(0 <= age <= .05 and min(setup,solve) >= 0 and setup+solve <= .05, 'solver captured timing policy')
        points[key] = (r,x)
        if key[1] == ('tracking' if key[0] < 2500 else 'stop'):
            near(x, w[2*key[0]], 'applied candidate vs accepted raw', 0)
    need(set(points) == expected_keys, 'attempt coverage')
    groups = defaultdict(list); key_order = []
    for r in qprows:
        key = (integer(r['tick'],'QP row tick'),r['kind'])
        need(key in points, 'orphan QP row')
        if not key_order or key != key_order[-1]:key_order.append(key)
        need(integer(r['row'],'row index') == len(groups[key]), 'row duplicate/gap/order')
        groups[key].append(r)
    need(key_order == ordered and set(groups) == expected_keys, 'QP row group coverage/order')
    maxsi = 0.; counts = Counter()
    for key, group in groups.items():
        tick,kind = key; r,x = points[key]
        need(len(group) >= 119, 'missing source-defined base rows')
        base = base_rows(q[2*tick],c[2*tick-2],w[2*tick-2],alpha[2*tick-2],lower,upper)
        actualsi = 0.
        for index,row in enumerate(group):
            A = np.array([number(row['A'+str(j)],'A') for j in range(7)])
            lo = number(row['lower'],'lower',False); hi = number(row['upper'],'upper',False)
            need(math.isfinite(lo) and (math.isfinite(hi) if index < 119 else hi == math.inf) and lo <= hi, 'illegal QP bound infinity/order')
            if index < 119:
                expected_A,l,u = base[index];near(A,expected_A,'base row coefficient',0);near([lo,hi],[l,u],'base row history bounds')
            product = A*x;need(np.isfinite(product).all(), 'nonfinite A*x products');value = float(sum(product));need(math.isfinite(value),'nonfinite Ax sum')
            actualsi = max(actualsi,0.,lo-value,value-hi)
        need(actualsi <= SI, 'original row SI violation')
        near(actualsi,number(r['SI_violation'],'reported SI'),'computed/reported SI',1e-12)
        need(-1 <= integer(r['maximum_violation_row'],'maximum row') < len(group), 'reported maximum row index')
        maxsi = max(maxsi,actualsi);counts[len(group)] += 1
    need(all(sha(raw.with_name(name)) == digest for name,digest in captured.items()), 'capture changed during audit')
    return protocol,freeze,execution,summary,rows,data,{'consumed_sidecars_sha256':captured,'cycles':n,'attempts':len(solves),'source_defined_base_rows':119,'row_counts':dict(counts),'max_command_age_s':maxage,'full4ms_deadline_misses':missed,'actual_original_row_max_SI_violation':maxsi,'superseded_tracking_attempts_not_applied':n-2500,'phase_rows':dict(Counter(r['phase'] for r in rows))}

def score(packet, raw, execution, output, model_factory=None):
    packet,raw,execution,output = map(Path,(packet,raw,execution,output));output.mkdir(exist_ok=False)
    synthetic = model_factory is not None
    report = {'seed':91013,'gate':'FAIL_CAPTURE_INTEGRITY','scope':'Synthetic gate control only; no plant/model validation' if synthetic else 'Fresh known curated conditional development trace only; no task, controller, uniform-domain, 250Hz or Phase5 acceptance','acceptance_limitations':LIMITATIONS,'synthetic_gate_model':synthetic,'no_calibration':True}
    try:
        protocol,freeze,_,summary,rows,data,audit = inspect_capture(packet,raw,execution)
        report.update(protocol_sha256=sha(packet/'protocol.json'),frozen_sha256=sha(packet/'frozen.json'),summary=summary,capture_integrity=audit)
        if model_factory is None:
            from public_coupled_servo_v2 import PublicServo
            model_factory = PublicServo
        model = model_factory(Path(protocol['model_xml']),load_json(protocol['public_model_constants']))
        q,v,c,qp,vp = [data[k] for k in PREFIXES[:5]];metrics=[];failures=[];maxkkt=0.;maxiters=0;branches=Counter();clamps=Counter();last=time.monotonic()
        for count,qlim,vlim in HORIZONS:
            starts = list(range(0,len(rows)-count+1,2));need(bool(starts),'no complete windows')
            group = {kind:{'windows':0,'complete':0,'failed':0,'maxq':0.,'maxv':0.,'sumq':0.,'sumv':0.,'worstq':None,'worstv':None} for kind in ['active','warmup']}
            for i in starts:
                kind='warmup' if rows[i]['phase']=='warmup' else 'active';s=group[kind];s['windows']+=1;predq,predv=q[i].copy(),v[i].copy()
                try:
                    for k in range(count):
                        predq,predv,info=model.step(predq,predv,c[i+k])
                        need(np.shape(predq)==(7,) and np.shape(predv)==(7,) and np.isfinite(predq).all() and np.isfinite(predv).all(),'nonfinite/malformed prediction')
                        kkt=number(info['original_KKT'],'force KKT');need(0<=kkt<=1e-10,'force QP KKT');maxkkt=max(maxkkt,kkt)
                        it=integer(info['iterations'],'force iterations');need(it>=0,'force iterations');maxiters=max(maxiters,it)
                        branches.update(info['branches']);clamps['controls']+=integer(info['control_clips'],'control clips');clamps['forces']+=integer(info['force_clips'],'force clips')
                    eq,ev=abs(predq-qp[i+count-1]),abs(predv-vp[i+count-1]);need(np.isfinite(eq).all() and np.isfinite(ev).all(),'nonfinite endpoint error')
                    s['complete']+=1;s['sumq']+=float(np.sum(eq**2));s['sumv']+=float(np.sum(ev**2))
                    for label,error in [('q',eq),('v',ev)]:
                        if error.max()>s['max'+label]:s['max'+label]=float(error.max());s['worst'+label]={'start_tick':i//2,'joint_index':int(error.argmax()),'phase':rows[i]['phase']}
                except Exception as exc:
                    s['failed']+=1;failures.append({'duration_s':count*SUBDT,'start_tick':i//2,'phase':rows[i]['phase'],'type':type(exc).__name__,'reason':str(exc)})
                if time.monotonic()-last>20:print(json.dumps({'substeps':count,'processed_start':i//2,'failures':len(failures)}),flush=True);last=time.monotonic()
            for kind,s in group.items():
                need(s['windows']>0,'missing '+kind+' windows');den=s['complete']*7;selected=[i for i in starts if ('warmup' if rows[i]['phase']=='warmup' else 'active')==kind]
                rmseq=math.sqrt(s['sumq']/den) if den else None;rmsev=math.sqrt(s['sumv']/den) if den else None
                okay=s['complete']==s['windows'] and s['failed']==0 and all(x is not None and math.isfinite(x) for x in [rmseq,rmsev,s['maxq'],s['maxv']])
                passed=okay and (kind=='warmup' or s['maxq']<=qlim and s['maxv']<=vlim)
                metrics.append({'scope':kind,'duration_s':count*SUBDT,'windows':s['windows'],'completed_windows':s['complete'],'failed_windows':s['failed'],'max_q_error_rad':s['maxq'],'max_v_error_rad_s':s['maxv'],'rmse_q_rad':rmseq,'rmse_v_rad_s':rmsev,'q_worst':s['worstq'],'v_worst':s['worstv'],'q_limit_rad':qlim,'v_limit_rad_s':vlim,'accuracy_gate_applies':kind=='active','start_phase_counts':dict(Counter(rows[i]['phase'] for i in selected)),'windows_intersecting_phase':{ph:sum(any(rows[j]['phase']==ph for j in range(i,i+count)) for i in selected) for ph in ['reference_motion','reference_recorded_stop','hold','new_shared_stop']},'hold_only_windows':sum(all(rows[j]['phase']=='hold' for j in range(i,i+count)) for i in selected),'passed':passed})
            (output/'metrics.partial.json').write_text(json.dumps(metrics,indent=2,allow_nan=False)+'\n');(output/'failures.partial.json').write_text(json.dumps(failures,indent=2,allow_nan=False)+'\n')
        for path,digest in freeze['files'].items():need(sha(path)==digest,'frozen input changed while scoring')
        for name,digest in audit['consumed_sidecars_sha256'].items():need(sha(raw.with_name(name))==digest,'sidecar changed while scoring')
        success = not failures and all(m['passed'] for m in metrics)
        report.update(gate=('PASS_SYNTHETIC_GATE_CONTROL_ONLY' if synthetic else 'PASS_FRESH_CURATED_CONDITIONAL_TRACE_ONLY') if success else 'FAIL_FRESH_CURATED_CONDITIONAL_TRACE',metrics=metrics,failures=failures,max_force_QP_KKT=maxkkt,max_force_QP_iterations=maxiters,repeated_prediction_branches=dict(branches),prediction_clamps=dict(clamps),all_full_windows_including_hold_stop_retained=True,overlapping_windows_not_independent_trials=True,uniform_accuracy_box_claim=False,main_MPC_integrated=False)
    except Exception as exc:
        report.update(gate='FAIL_CAPTURE_INTEGRITY',failure={'type':type(exc).__name__,'reason':str(exc)},all_input_files_retained=True)
    (output/'validation_report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'gate':report['gate'],'failure':report.get('failure'),'windows':sum(m['windows'] for m in report.get('metrics',[]))},allow_nan=False),flush=True)
    return 0 if report['gate'].startswith('PASS') else 1

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ['packet','raw','execution','output']:parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(score(args.packet,args.raw,args.execution,args.output))
