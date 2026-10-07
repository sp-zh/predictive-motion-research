#!/usr/bin/env python3
"""Frozen finite-output v3 audit: fresh CMake build and existing regressions only."""
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import numpy as np

BASE=Path('results/phase5-causal-soft-servo-cpp-v3-root-checkpoint/restored/project')
DATA=BASE/'results/phase5/development/causal-soft-servo-cpp-v3'
SOURCE=Path(__file__).resolve()
SOURCE_BYTES=SOURCE.read_bytes()


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def maximum(a,b):
    aa,bb=np.asarray(a),np.asarray(b)
    assert aa.shape==bb.shape and np.isfinite(aa).all() and np.isfinite(bb).all()
    return float(np.max(abs(aa-bb)))

def main():
    out=Path('results/phase5-reference/root-causal-servo-finite-v3-independent-20261007-v1');out.mkdir(exist_ok=False)
    frozen=json.loads((DATA/'frozen.json').read_text());identities={}
    for name,h in frozen['files'].items():
        relative=name.split('/predictive_motion/',1)[1];p=BASE/relative
        assert sha(p)==h,(name,h,sha(p));identities[relative]=h
    for p in (BASE/'tools/phase5_causal_servo_v3').iterdir():
        assert sha(p)==sha(Path('tools/phase5_causal_servo_v3')/p.name)
    packet_path=Path('results/phase5-reference/root-causal-servo-branch-packet-20261007/branch_packet.json')
    assert sha(packet_path)=='8f09f79a23a6be6f3785dc76612c9a1f43b90b038e1fb248d616116dcb1276f7'
    assert packet_path.read_bytes()==(DATA/'root_branch_packet.json').read_bytes()
    packet=json.loads(packet_path.read_text())
    model_path=Path('results/phase5-reference/root-augmented-soft-servo-20261007-final-v2/MODEL_SNAPSHOT.json')
    oracle_path=model_path.with_name('SOURCE_SNAPSHOT.py')
    assert sha(model_path)==packet['frozen_model_sha256'] and sha(oracle_path)==packet['oracle_sha256']
    remote='/home/codextransfer/clean-audits/causal-servo-finite-v3-independent-20261007-v1'
    files={p.name:p.read_text() for p in (BASE/'tools/phase5_causal_servo_v3').iterdir()}
    files.update({'branch_input.yaml':(DATA/'branch_input.yaml').read_text(),'nominal_input.yaml':(BASE/'results/phase5/development/causal-soft-servo-cpp-v1/input.yaml').read_text(),'horizon_control.yaml':(DATA/'horizon_control.yaml').read_text(),'horizon_initial.yaml':(DATA/'horizon_initial.yaml').read_text()})
    payload=base64.b64encode(json.dumps(files).encode()).decode()
    setup="import base64,json,pathlib,subprocess; out=pathlib.Path("+repr(remote)+"); out.mkdir(exist_ok=False); files=json.loads(base64.b64decode("+repr(payload)+")); [(out/name).write_text(text) for name,text in files.items()]; "
    remote_run=r"""
build=out/'build'
logs=[]
for command in [['cmake','-S',str(out),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'],['cmake','--build',str(build),'-j2']]:
 r=subprocess.run(command,capture_output=True,text=True);logs.append({'command':command,'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});assert r.returncode==0,logs
compile_commands=json.loads((build/'compile_commands.json').read_text())
assert len(compile_commands)==4
assert all(all(flag in entry['command'] for flag in ('-Wall','-Wextra','-Werror')) for entry in compile_commands)
def execute(args):
 r=subprocess.run([str(build/args[0]),*args[1:]],capture_output=True,text=True)
 return {'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
api=execute(['causal_soft_servo_api_probe']);edge=execute(['root_edge_probe']);overflow=execute(['causal_soft_servo_overflow_probe'])
assert api['code']==edge['code']==overflow['code']==0
for name in ['branch','nominal']:
 result=execute(['causal_soft_servo_probe',str(out/(name+'_input.yaml')),str(out/(name+'_actual.json'))]);assert result['code']==0,result
horizons=[]
for name in ['horizon_control','horizon_initial']:
 r=execute(['causal_soft_servo_probe',str(out/(name+'.yaml')),str(out/(name+'.partial.json'))]);r['case']=name;r['partial_output']=(out/(name+'.partial.json')).read_text();horizons.append(r)
import hashlib
print(json.dumps({'api':api['stdout'],'edge':json.loads(edge['stdout']),'overflow':overflow,'horizons':horizons,'branch':json.loads((out/'branch_actual.json').read_text()),'nominal':json.loads((out/'nominal_actual.json').read_text()),'build_logs':logs,'compile_commands':compile_commands,'fresh_binary_sha256':{n:hashlib.sha256((build/n).read_bytes()).hexdigest() for n in ['causal_soft_servo_api_probe','root_edge_probe','causal_soft_servo_overflow_probe','causal_soft_servo_probe']}}))
"""
    setup+=remote_run
    run=subprocess.run(['tools/dell-ssh.sh','DellTransfer','python3 -c '+shlex.quote(setup)],capture_output=True,text=True,check=True)
    actual=json.loads(run.stdout);(out/'fresh_actual.json').write_text(json.dumps(actual,indent=2)+'\n');(out/'compiler_and_api.log').write_text(run.stderr)
    branch_reports=[]
    assert len(actual['branch']['cases'])==len(packet['cases'])==8
    for a,e in zip(actual['branch']['cases'],packet['cases']):
        assert a['name']==e['name']
        errs={k:maximum(av,ev) for k,av,ev in [('state',a['states'][1],e['next_state']),('A',a['cell_A'][0],e['A']),('B',a['cell_B'][0],e['B']),('defect',a['cell_defect'][0],e['defect'])]}
        assert max(errs.values())<5e-12 and a['history'][0]['branches_2ms']==e['branches_2ms']
        assert a['clip_equalities']==int(e['exact_clip_threshold'])
        branch_reports.append({'name':a['name'],'errors':errs,'branches_2ms':a['history'][0]['branches_2ms'],'clip_equalities':a['clip_equalities']})
    expected=json.loads((BASE/'results/phase5/development/causal-soft-servo-cpp-reference-v1/oracle.json').read_text())
    original=json.loads((DATA/'actual_nominal.json').read_text());nominal=[]
    assert len(actual['nominal']['cases'])==len(expected['cases'])==2
    for a,e,o in zip(actual['nominal']['cases'],expected['cases'],original['cases']):
        assert a['name']==e['name']==o['name'] and len(a['history'])==len(e['history'])
        assert all(x['branches_2ms']==y['branches_2ms'] for x,y in zip(a['history'],e['history']))
        fields=['states','cell_A','cell_B','cell_defect','condensed_offsets','control_sensitivities','initial_sensitivities']
        errors={k:maximum(a[k],e[k]) for k in fields}
        assert max(errors.values())<5e-12
        nominal.append({'name':a['name'],'errors_vs_root_oracle':errors,'max_vs_recorded_CPP':max(maximum(a[k],o[k]) for k in fields),'history_length':len(a['history'])})
    invalid=list(csv.DictReader(io.StringIO(actual['api'])));assert len(invalid)==78 and all(r['rejected']=='1' for r in invalid)
    assert len(actual['nominal']['rejections'])==10 and all(r['rejected'] for r in actual['nominal']['rejections'])
    edge=actual['edge'];assert edge['model_validated']==1 and edge['threw']
    overflow_rows=list(csv.DictReader(io.StringIO(actual['overflow']['stdout'])))
    assert len(overflow_rows)==8 and all(r['model_validated']=='1' for r in overflow_rows)
    assert sum(r['overflow_rejected']=='1' for r in overflow_rows)==7
    assert any(r['entry']=='cycle_finite' and r['overflow_rejected']=='0' for r in overflow_rows)
    for h in actual['horizons']:
        assert h['code']==3 and h['stderr'].strip()=='nonfinite horizon '+('control sensitivity product' if h['case']=='horizon_control' else 'initial sensitivity')
    assert all(sha(BASE/name)==h for name,h in identities.items())
    result={'verdict':'PASS_ISOLATED_SCALAR_FINITE_OUTPUT_V3','audit_source_sha256':hashlib.sha256(SOURCE_BYTES).hexdigest(),'frozen_identity_checks':identities,'root_branch_packet_sha256':sha(packet_path),'frozen_model_sha256':sha(model_path),'fixed_root_oracle_sha256':sha(oracle_path),'fresh_remote':remote,'branch_tests':branch_reports,'nominal_tests':nominal,'invalid_entry_rejections':78,'domain_mesh_rejections':10,'root_v2_counterexample_now_rejected':edge,'overflow_regression_rows':overflow_rows,'horizon_overflow_rejections':[{k:v for k,v in h.items() if k!='partial_output'} for h in actual['horizons']],'compile_commands':actual['compile_commands'],'fresh_binary_sha256':actual['fresh_binary_sha256'],'fix_scope':'Reject derived nonfinite arithmetic in cycle/cell and horizon propagation/serialization; original frozen scalar-model coefficients/domain, equations and branch convention unchanged.','limits':['Scalar empirical model only, not coupled dynamics or exact MuJoCo','No model domain extension or fresh holdout','No real-time guarantee, control guards, position/geometry/stop guarantee, main MPC integration, CTRL001 closure or Phase5 acceptance','At exact clip thresholds saturated-side Jacobian is convention; unique ordinary derivative does not exist','Same original n7 branch-vector fixtures are uniform across joints; mixed branch combinations are not exhaustively tested']}
    assert SOURCE.read_bytes()==SOURCE_BYTES
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');(out/'SOURCE_SNAPSHOT.py').write_bytes(SOURCE_BYTES)
    Path('reviews/evidence/causal_servo_finite_v3_root_review_20261007.json').write_text(json.dumps(result,indent=2)+'\n')
    ready={'source_sha256':result['audit_source_sha256'],'files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in out.iterdir()}}
    assert SOURCE.read_bytes()==SOURCE_BYTES
    (out/'READY.json').write_text(json.dumps(ready,indent=2)+'\n')
    print(json.dumps({'verdict':result['verdict'],'branch_max_error':max(max(x['errors'].values()) for x in branch_reports),'nominal_max_error':max(max(x['errors_vs_root_oracle'].values()) for x in nominal),'edge':edge,'source_sha256':result['audit_source_sha256']},indent=2))

if __name__=='__main__':main()
