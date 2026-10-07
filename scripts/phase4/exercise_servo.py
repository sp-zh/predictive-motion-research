from pathlib import Path
import csv,json,subprocess,time,os,sys
import yaml
root=Path(sys.argv[sys.argv.index('--root')+1]).resolve() if '--root' in sys.argv else Path(__file__).resolve().parents[2]
path=list(csv.DictReader((root/'results/cad/path_screening_aabb/feasible_path.csv').open()))
q=[float(path[0][f'q{i}']) for i in range(1,8)]
regular='--regular' in sys.argv
if regular:q=yaml.safe_load((root/'results/phase4/servo-sanity-state.yaml').read_text())['q']
prefix='servo-regular-api' if regular else 'servo-api'
cmds=[]
magnitude=.01 if regular else .001
for seq,twist in enumerate([[0]*6,[magnitude,0,0,0,0,0],[0,magnitude,0,0,0,0],[0,0,magnitude,0,0,0],[0,0,0,magnitude,0,0],[0,0,0,0,magnitude,0],[0,0,0,0,0,magnitude]]):
    cmds.append(' '.join(map(str,[seq]+q+[0]*7+twist)))
env=dict(os.environ,ROS_LOCALHOST_ONLY='1',ROS_DOMAIN_ID='71')
result=subprocess.run([str(root/'build-phase4-servo/servo_sidecar'),str(root/'experiments/generated/phase4')],input='\n'.join(cmds)+'\n',text=True,capture_output=True,env=env,timeout=60)
(root/f'results/phase4/{prefix}.stdout').write_text(result.stdout)
(root/f'results/phase4/{prefix}.stderr').write_text(result.stderr)
rows=[line for line in result.stdout.splitlines() if line.startswith('RESULT ')]
parsed=[]
for row in rows:
    p=row.split(); parsed.append({'seq':int(p[1]),'pid':int(p[2]),'status':int(p[3]),'csm_matches_measured':bool(int(p[4])),
                                  'api_seconds':float(p[5]),'synchronization_plus_api_seconds':float(p[6]),
                                  'positions':list(map(float,p[7:14])),'velocities':list(map(float,p[14:21]))})
report={'exit_code':result.returncode,'requests':len(cmds),'results':parsed,
        'actual_api':'moveit_servo::Servo::getNextJointState','collision_enabled':True,'smoothing_enabled':True,
        'collision_freshness':'real asynchronous thread enabled; CSM match is not collision-cycle freshness proof; independent common supervisor required',
        'transport':'measured JointState ROS to CSM; Cartesian requests via stdin C++ API; no ROS Cartesian transport cost claim'}
(root/f'results/phase4/{prefix}.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if result.returncode or len(parsed)!=7 or not all(r['csm_matches_measured'] for r in parsed) or any(r['status']==-1 for r in parsed):raise SystemExit(1)
if max(abs(a-b) for a,b in zip(parsed[0]['positions'],q))>1e-10 or max(abs(v) for v in parsed[0]['velocities'])>1e-10:raise SystemExit('Zero request changed initial target')
if regular and not any(sum(v*v for v in r['velocities'])>1e-12 for r in parsed[1:]):raise SystemExit('Regular-state Servo motion not exercised')
