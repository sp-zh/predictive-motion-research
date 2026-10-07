#!/usr/bin/env python3
"""Read-only frozen module audit; separate compile/replay and API counterexample."""
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import numpy as np

BASE=Path('results/phase5-causal-soft-servo-cpp-v2-root-checkpoint/restored/project')
DATA=BASE/'results/phase5/development/causal-soft-servo-cpp-v2'
SOURCE=Path(__file__).resolve()
SOURCE_BYTES=SOURCE.read_bytes()
EDGE=r'''#include "causal_soft_servo.hpp"
#include <iostream>
using namespace phase5_local_model;
int main(){Model m;m.mass=Vector::Constant(1,1e-300);m.bias=Vector::Zero(1);m.kp=Vector::Constant(1,1e308);m.damping=Vector::Zero(1);m.friction=Vector::Zero(1);m.impedance=Vector::Constant(1,.9);m.decay=Vector::Constant(1,100);m.q_min=Vector::Constant(1,-.01);m.q_max=Vector::Constant(1,.01);m.error_min=Vector::Constant(1,-.001);m.error_max=Vector::Constant(1,.001);m.velocity_abs_max=.05;Vector z=Vector::Zero(6),u=Vector::Zero(2);z(4)=.2;
bool validated=false;try{m.validate();validated=true;auto t=cycle(z,u,m);std::cout<<"{\"model_validated\":"<<validated<<",\"threw\":false,\"state_finite\":"<<t.state.allFinite()<<",\"A_finite\":"<<t.A.allFinite()<<",\"B_finite\":"<<t.B.allFinite()<<",\"defect_finite\":"<<t.defect.allFinite()<<"}\n";}catch(const std::exception&){std::cout<<"{\"model_validated\":"<<validated<<",\"threw\":true}\n";}}
'''

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def maximum(a,b):
    aa,bb=np.asarray(a),np.asarray(b)
    assert aa.shape==bb.shape and np.isfinite(aa).all() and np.isfinite(bb).all()
    return float(np.max(abs(aa-bb)))

def main():
    out=Path('results/phase5-reference/root-causal-servo-cpp-v2-independent-20261007-v1');out.mkdir(exist_ok=False)
    frozen=json.loads((DATA/'frozen.json').read_text());identities={}
    for name,h in frozen['files'].items():
        relative=name.split('/predictive_motion/',1)[1];p=BASE/relative
        assert sha(p)==h,(name,h,sha(p));identities[relative]=h
    for p in (BASE/'tools/phase5_causal_servo_v2').iterdir():
        assert sha(p)==sha(Path('tools/phase5_causal_servo_v2')/p.name)
    packet_path=Path('results/phase5-reference/root-causal-servo-branch-packet-20261007/branch_packet.json')
    assert sha(packet_path)=='8f09f79a23a6be6f3785dc76612c9a1f43b90b038e1fb248d616116dcb1276f7'
    assert packet_path.read_bytes()==(DATA/'root_branch_packet.json').read_bytes()
    packet=json.loads(packet_path.read_text())
    model_path=Path('results/phase5-reference/root-augmented-soft-servo-20261007-final-v2/MODEL_SNAPSHOT.json')
    oracle_path=model_path.with_name('SOURCE_SNAPSHOT.py')
    assert sha(model_path)==packet['frozen_model_sha256'] and sha(oracle_path)==packet['oracle_sha256']
    remote='/home/codextransfer/clean-audits/causal-servo-cpp-v2-independent-20261007-v1'
    files={p.name:p.read_text() for p in (BASE/'tools/phase5_causal_servo_v2').iterdir() if p.suffix in ('.hpp','.cpp')}
    files.update({'edge_probe.cpp':EDGE,'branch_input.yaml':(DATA/'branch_input.yaml').read_text(),'nominal_input.yaml':(BASE/'results/phase5/development/causal-soft-servo-cpp-v1/input.yaml').read_text()})
    payload=base64.b64encode(json.dumps(files).encode()).decode()
    setup="import base64,json,pathlib,subprocess; out=pathlib.Path("+repr(remote)+"); out.mkdir(exist_ok=False); files=json.loads(base64.b64decode("+repr(payload)+")); [(out/name).write_text(text) for name,text in files.items()]; "
    setup+="[(subprocess.run(['c++','-O2','-std=c++17','-Wall','-Wextra','-Werror','-I/usr/include/eigen3',str(out/(name+'.cpp')),'-lyaml-cpp','-o',str(out/name)],check=True)) for name in ['causal_soft_servo_probe','causal_soft_servo_api_probe','edge_probe']]; "
    setup+="api=subprocess.check_output([str(out/'causal_soft_servo_api_probe')],text=True); edge=json.loads(subprocess.check_output([str(out/'edge_probe')],text=True)); [(subprocess.run([str(out/'causal_soft_servo_probe'),str(out/(name+'_input.yaml')),str(out/(name+'_actual.json'))],check=True)) for name in ['branch','nominal']]; print(json.dumps({'api':api,'edge':edge,'branch':json.loads((out/'branch_actual.json').read_text()),'nominal':json.loads((out/'nominal_actual.json').read_text())}))"
    run=subprocess.run(['tools/dell-ssh.sh','DellTransfer','python3 -c '+shlex.quote(setup)],capture_output=True,text=True,check=True)
    actual=json.loads(run.stdout);(out/'fresh_actual.json').write_text(json.dumps(actual,indent=2)+'\n');(out/'compiler_and_api.log').write_text(run.stderr);(out/'edge_probe.cpp').write_text(EDGE)
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
    edge=actual['edge'];assert edge['model_validated']==1 and not edge['threw'] and edge['state_finite']==1 and edge['A_finite']==edge['B_finite']==edge['defect_finite']==0
    result={'verdict':'PASS_FROZEN_SCALAR_MODEL_COMPONENT_WITH_GENERIC_API_HARDENING_DEFECT','audit_source_sha256':hashlib.sha256(SOURCE_BYTES).hexdigest(),'frozen_identity_checks':identities,'root_branch_packet_sha256':sha(packet_path),'frozen_model_sha256':sha(model_path),'fixed_root_oracle_sha256':sha(oracle_path),'fresh_remote':remote,'branch_tests':branch_reports,'nominal_tests':nominal,'invalid_entry_rejections':78,'domain_mesh_rejections':10,'derived_nonfinite_counterexample':edge,'defect_scope':'Generic finite-positive parameter API accepts mass=1e-300,kp=1e308,D=0,eta=0; physical zero state remains finite but transition A/B/defect contain nonfinite values and no exception. Outside the frozen FR3 coefficients; does not invalidate fixed-model parity. Check derived outputs before returning or document enforceable arithmetic envelope.','limits':['Scalar empirical model only, not coupled dynamics or exact MuJoCo','No model domain extension or fresh holdout','No real-time guarantee, control guards, position/geometry/stop guarantee, main MPC integration, CTRL001 closure or Phase5 acceptance','At exact clip thresholds saturated-side Jacobian is convention; unique ordinary derivative does not exist','Same original n7 branch-vector fixtures are uniform across joints; mixed branch combinations are not exhaustively tested']}
    assert SOURCE.read_bytes()==SOURCE_BYTES
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');(out/'SOURCE_SNAPSHOT.py').write_bytes(SOURCE_BYTES)
    Path('reviews/evidence/causal_servo_cpp_v2_root_review_20261007.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'verdict':result['verdict'],'branch_max_error':max(max(x['errors'].values()) for x in branch_reports),'nominal_max_error':max(max(x['errors_vs_root_oracle'].values()) for x in nominal),'edge':edge,'source_sha256':result['audit_source_sha256']},indent=2))

if __name__=='__main__':main()
