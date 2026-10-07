#!/usr/bin/env python3
import datetime,hashlib,json
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
review=p/'reviews/evidence/signed_command_cone_math_audit_20261007.json';data=json.loads(review.read_text())
authorization=p/'config/phase5_development/servo_validation_safe_reference_v3.authorization.json'
authorization.write_text(json.dumps({'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authorizing_root_chat':'01a10958-048c-7480-a04e-51544112196c','review':str(review),'review_sha256':sha(review),'authorization':'Explicit independent root approval for new prospectively frozen w_ref + signed command continuation + strict solver stopping1e-12 fixture; unchanged model/error thresholds/4000/.05/native SOLVED/physical+geom+command guards; actual candidate and accepted-history continuation checked; main MPC and causal module not integrated.','scope':'Development seed91012 curated seen inputs; no untouched holdout, future position/geometry stop certificate or Phase5 acceptance'},indent=2)+'\n')
runner=p/'scripts/phase5/run_servo_safe_reference_v3.py';s=runner.read_text();s=s.replace("e.mkdir()",'''for path in [p/'config/phase5_development/servo_validation_safe_reference_v3.authorization.json',p/'reviews/evidence/signed_command_cone_math_audit_20261007.json',p/'reviews/evidence/signed_command_cone_math_audit_20261007.md']:
    files[str(path)] = sha(path)
e.mkdir()''');runner.write_text(s)
print('root authorization included in prospective input closure; runner not yet executed')
