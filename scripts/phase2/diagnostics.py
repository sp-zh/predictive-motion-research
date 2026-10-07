"""Offline runner-contract probes. These are not development/evaluation trials."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import yaml

root=Path(__file__).resolve().parents[2]
out=root/'results/phase2/diagnostics'
out.mkdir(parents=True,exist_ok=True)
design=yaml.safe_load((root/'config/phase2.yaml').read_text())
selected=yaml.safe_load((root/'results/phase2/selection.yaml').read_text())
runner=root/'install/predictive_motion_control/lib/predictive_motion_control/phase2_benchmark'
robot=root/'src/predictive_motion_kinematics/config/fr3.yaml'
scene=root/'.vendor/menagerie/franka_fr3/scene.xml'
checks=[]
def execute(name,cfg,should_reject=False):
    path=out/(name+'.yaml')
    path.write_text(yaml.safe_dump(cfg,sort_keys=False))
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    selection=out/(name+'_selection.yaml')
    chosen=dict(selected,config_sha256=sha)
    selection.write_text(yaml.safe_dump(chosen))
    result=subprocess.run([str(runner),str(robot),str(scene),str(path),str(out/name),'evaluation',str(selection),sha],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/(name+'.log')).write_text(result.stdout)
    if should_reject:
        assert result.returncode!=0,(name,result.stdout)
    else:
        assert result.returncode==0,(name,result.stdout)
    checks.append(dict(name=name,returncode=result.returncode,expected_reject=should_reject))
    return out/name

for name,changes in [('invalid_margin',{'search_margin':.5}),('invalid_quantile',{'near_quantile':.9,'nominal_quantile':.5}),('invalid_count',{'search_samples':0}),('invalid_duration',{'path_seconds':-1}),('invalid_scale',{'rotation_length_scale':0}),('overlapping_seeds',{'evaluation_seeds':[1101]})]:
    cfg=copy.deepcopy(design);cfg.update(changes);execute(name,cfg,True)
probe=copy.deepcopy(design)
probe.update(search_samples=200,development_seeds=[3101],evaluation_seeds=[4101],sweep_points=3)
limited=copy.deepcopy(probe);limited['velocity_limits']=[1e-6]*7
folder=execute('executed_limit_violation',limited)
import csv
rows=list(csv.DictReader((folder/'trials.csv').open()))
assert len(rows)==6 and all(row['code']=='EXECUTED_LIMIT_VIOLATION' for row in rows)
huge=copy.deepcopy(probe);huge['feedback_gain']=1e308
folder=execute('solver_exception',huge)
rows=list(csv.DictReader((folder/'trials.csv').open()))
assert len(rows)==6
assert any('EXCEPTION' in row['code'] for row in rows),rows
assert list(folder.glob('*.error.txt'))
(out/'summary.json').write_text(json.dumps(dict(status='PASS',checks=checks,limit_failure_trials=6,exception_codes=[row['code'] for row in rows]),indent=2)+'\n')
print('RUNNER_CONFIG_LIMIT_AND_EXCEPTION_CONTRACTS_PASS')
