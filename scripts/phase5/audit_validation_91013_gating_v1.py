#!/usr/bin/env python3
"""Execute frozen scorer on explicitly synthetic CSVs with a no-plant stub.

These fixtures exercise data-integrity/gate logic only. They are neither
simulation data, model-validation data, approval files nor a physical run.
"""
import contextlib
import csv
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import types
import numpy as np
import yaml

SOURCE=Path(__file__).resolve();SOURCE_BYTES=SOURCE.read_bytes()
SCORER=Path('scripts/phase5/score_public_coupled_validation_91013.py')
RUNNER=Path('scripts/phase5/run_public_coupled_validation_91013.py')
PACKET=Path('results/phase5-public-validation-protocol-91013-root-checkpoint/restored/project/results/phase5/development/public-coupled-validation-91013-protocol-v1')
OUT=Path('results/phase5-reference/root-validation-91013-gating-v1-20261007')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class NoPlantStub:
    """Pure identity transform, rejects nonfinite input as real model does."""
    def __init__(self,*args):pass
    def step(self,q,v,target):
        if not all(np.isfinite(x).all() for x in (q,v,target)):raise ValueError('synthetic input nonfinite')
        return q.copy(),v.copy(),{'original_KKT':0.,'iterations':1,'branches':[0]*7,'control_clips':0,'force_clips':0}

def csv_write(path,fields,rows):
    with path.open('w') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def main():
    OUT.mkdir(exist_ok=False)
    freeze=json.loads((PACKET/'frozen.json').read_text());protocol=json.loads((PACKET/'protocol.json').read_text())
    assert sha(SCORER)==freeze['files']['/home/codextransfer/predictive_motion/scripts/phase5/score_public_coupled_validation_91013.py']
    assert sha(RUNNER)==freeze['files']['/home/codextransfer/predictive_motion/scripts/phase5/run_public_coupled_validation_91013.py']
    assert sha(PACKET/'protocol.json')=='66e3ea6665f573ef729c0d1504499f0773e2f8d6de6157c3d5f6132bb075eb40'
    scorer_bytes=SCORER.read_bytes();runner_bytes=RUNNER.read_bytes()
    (OUT/'SCORER_SNAPSHOT.py').write_bytes(scorer_bytes);(OUT/'RUNNER_SNAPSHOT.py').write_bytes(runner_bytes)
    module=types.ModuleType('public_coupled_servo_v2');module.PublicServo=NoPlantStub
    previous_module=sys.modules.get('public_coupled_servo_v2');sys.modules['public_coupled_servo_v2']=module
    raw_fields=['tick','substep','phase','contacts']+[prefix+str(j) for prefix in ['q_before_','v_before_','target_','q_post_','v_post_'] for j in range(7)]
    cycle_fields=['tick','full_cycle_wall_s','command_age_s','status','deadline_miss']
    attempt_fields=['tick','kind','wrapper_status','raw_status','api_error','candidate_size']+['x'+str(j) for j in range(7)]
    row_fields=['tick','kind','row','lower','upper']+['A'+str(j) for j in range(7)]
    names=['synthetic_control','empty_trace','warmup_only','future_endpoint_NaN','warmup_failure','QP_row_NaN_after_capture_hash','API_error_nonzero','failed_attempt_missing_row_group','duplicate_attempt_overwritten']
    reports=[]
    for name in names:
        case=OUT/name;case.mkdir();prepared=case/'synthetic_packet';prepared.mkdir()
        constants=case/'synthetic_constants.json';constants.write_text('{}\n')
        synthetic_protocol=dict(protocol,public_model_constants=str(constants.resolve()),purpose='Synthetic scorer gating fixture only; no plant/model trial')
        (prepared/'protocol.json').write_text(json.dumps(synthetic_protocol,indent=2)+'\n')
        synthetic_freeze={'seed':91013,'files':{str(SCORER.resolve()):sha(SCORER),str(constants.resolve()):sha(constants),str((prepared/'protocol.json').resolve()):sha(prepared/'protocol.json')},'scope':'Synthetic metadata for isolated gate reproduction; no approval'}
        (prepared/'frozen.json').write_text(json.dumps(synthetic_freeze,indent=2)+'\n')
        rows=[]
        for i in range(42):
            r={field:0 for field in raw_fields};r.update(tick=i//2,substep=i%2+1,phase='reference_motion')
            rows.append(r)
        if name=='empty_trace':rows=[]
        if name=='warmup_only':
            for r in rows:r['phase']='warmup'
        if name=='future_endpoint_NaN':
            for r in rows:r['q_post_0']='nan';r['v_post_0']='nan'
        if name=='warmup_failure':
            for r in rows[:2]:r['phase']='warmup';r['q_before_0']='nan'
        raw=case/'raw.csv';csv_write(raw,raw_fields,rows)
        cycles=[{'tick':0,'full_cycle_wall_s':.001,'command_age_s':.001,'status':'SOLVED','deadline_miss':0}]
        csv_write(case/'cycles.csv',cycle_fields,cycles)
        attempt={field:0 for field in attempt_fields};attempt.update(tick=0,kind='tracking',wrapper_status='SOLVED',raw_status=1,api_error=0,candidate_size=7)
        attempts=[attempt.copy()]
        if name=='API_error_nonzero':attempts[0]['api_error']=999
        if name=='failed_attempt_missing_row_group':
            failed=attempt.copy();failed.update(tick=1,kind='tracking',wrapper_status='PRIMAL_INFEASIBLE',raw_status=3,api_error=1,candidate_size=0);attempts.append(failed)
        if name=='duplicate_attempt_overwritten':
            failed=attempt.copy();failed.update(wrapper_status='PRIMAL_INFEASIBLE',raw_status=3,api_error=1,candidate_size=0);attempts.insert(0,failed)
        csv_write(case/'all_qp_solves.csv',attempt_fields,attempts)
        row={field:0 for field in row_fields};row.update(tick=0,kind='tracking',row=0,lower=0,upper=0,A0=1)
        csv_write(case/'all_qp_rows.csv',row_fields,[row])
        (case/'summary.yaml').write_text(yaml.safe_dump({'completed_stop':True,'primary_failure':'','stop_failure':''}))
        raw_hashes={f.name:sha(f) for f in case.iterdir() if f.is_file()}
        execution={'argv':['synthetic-gate-no-collector','91013',str(raw.resolve())],'return_code':0,'prepared_frozen_sha256':sha(prepared/'frozen.json'),'raw_files':raw_hashes,'scope':'Entirely synthetic; no execution/approval/plant'}
        execution_path=case/'synthetic_execution.json';execution_path.write_text(json.dumps(execution,indent=2)+'\n')
        if name=='QP_row_NaN_after_capture_hash':row['A0']='nan';csv_write(case/'all_qp_rows.csv',row_fields,[row])
        old_argv=sys.argv;sys.argv=[str(SCORER),'--packet',str(prepared),'--raw',str(raw),'--execution',str(execution_path),'--output',str(case/'scored')]
        buffer=io.StringIO();code=0
        try:
            with contextlib.redirect_stdout(buffer),contextlib.redirect_stderr(buffer):runpy.run_path(str(SCORER),run_name='__main__')
        except SystemExit as e:code=e.code
        finally:sys.argv=old_argv
        (case/'scorer.log').write_text(buffer.getvalue())
        result=json.loads((case/'scored/validation_report.json').read_text())
        metrics=result.get('metrics',[])
        reports.append({'name':name,'exit_code':code,'gate':result['gate'],'phase_rows':result.get('phase_rows'),'active_windows':[m['windows'] for m in metrics if m['scope']=='active'],'warmup_failed_windows':sum(m['failed_windows'] for m in metrics if m['scope']=='warmup'),'reported_failures':len(result.get('failures',[])),'max_SI':result.get('actual_original_row_max_SI_violation'),'nonfinite_RMSE':any(m['rmse_q_rad'] is not None and not np.isfinite(m['rmse_q_rad']) or m['rmse_v_rad_s'] is not None and not np.isfinite(m['rmse_v_rad_s']) for m in metrics),'sidecar_hash_mismatches':[f for f,h in raw_hashes.items() if sha(case/f)!=h]})
        assert code==0 and result['gate']=='PASS_FRESH_CURATED_CONDITIONAL_TRACE_ONLY'
    if previous_module is None:del sys.modules['public_coupled_servo_v2']
    else:sys.modules['public_coupled_servo_v2']=previous_module
    assert SOURCE.read_bytes()==SOURCE_BYTES and SCORER.read_bytes()==scorer_bytes and RUNNER.read_bytes()==runner_bytes
    report={'decision':'DO_NOT_APPROVE_PREPARED_PROTOCOL_V1','scope':'Execution of unchanged scorer on synthetic gate CSVs with a declared no-plant identity stub; not actual collector output or predictor accuracy evidence','source_sha256':hashlib.sha256(SOURCE_BYTES).hexdigest(),'scorer_sha256':sha(SCORER),'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PACKET/'protocol.json'),'original_prepared_frozen_sha256':sha(PACKET/'frozen.json'),'original_prelisted_inputs':len(freeze['files']),'cases':reports,'no_root_approval_file_created':True,'no_collector_executed':True,'unchanged_scorer_source_executed':True,'frozen_scorer_model_was_stubbed_for_gate_isolation':True}
    text=json.dumps(report,indent=2,allow_nan=False)+'\n';(OUT/'audit.json').write_text(text);(OUT/'SOURCE_SNAPSHOT.py').write_bytes(SOURCE_BYTES)
    Path('reviews/evidence/public_validation_91013_protocol_v1_root_review_20261007.json').write_text(text)
    files={str(p.relative_to(OUT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in OUT.rglob('*') if p.is_file()}
    assert SOURCE.read_bytes()==SOURCE_BYTES
    (OUT/'READY.json').write_text(json.dumps({'source_sha256':report['source_sha256'],'files':files},indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
