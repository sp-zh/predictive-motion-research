#!/usr/bin/env python3
"""Synthetic gate regressions only: no collector or physical model execution."""
import argparse
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import numpy as np
import yaml

P=Path('/home/codextransfer/predictive_motion')
SCORER=P/'scripts/phase5/score_public_coupled_validation_91013_v2.py'
spec=importlib.util.spec_from_file_location('strict_gate',SCORER);gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
sha=gate.sha

class NoPlantStub:
    """Identity forecast for a declared synthetic constant-state trace."""
    def __init__(self,*args):self.calls=0
    def step(self,q,v,c):
        self.calls+=1
        return q.copy(),v.copy(),{'original_KKT':0.,'iterations':1,'branches':['synthetic']*7,'control_clips':0,'force_clips':0}

class WarmupFailure(NoPlantStub):
    def step(self,q,v,c):
        if self.calls==0:
            self.calls+=1
            raise ValueError('declared synthetic first warmup forecast failure')
        return super().step(q,v,c)

class NonfinitePrediction(NoPlantStub):
    def step(self,q,v,c):
        qp,vp,info=super().step(q,v,c);qp[0]=float('nan');return qp,vp,info

def write_csv(path,fields,rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def rewrite(path,change):
    with path.open() as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    fields,rows=change(fields,rows);path.unlink();write_csv(path,fields,rows)

def set_cell(path,index,column,value):
    def change(fields,rows):rows[index][column]=value;return fields,rows
    rewrite(path,change)

def boundary_fixture(case,q,ranges,corrupt=False):
    """Synthetic lawful accepted history at V; no plant/optimality claim.

    The changed tracking candidate exceeds V by 1e-13 while all recorded
    original rows retain SI <= 1e-7. A distinct valid stop supersedes it.
    """
    raw=[];cycles=[];solves=[];rows=[];c=q.copy();wprev=np.zeros(7);aprev=np.zeros(7)
    for t in range(2651):
        w=np.zeros(7)
        if 500<=t<650:w[0]=gate.V*(1-np.cos(np.pi*(t-500)/150))/2
        elif 650<=t<2500:w[0]=gate.V
        elif t>=2500:w[0]=gate.V*(1+np.cos(np.pi*(t-2500)/150))/2
        alpha=(w-wprev)/gate.DT;jerk=(alpha-aprev)/gate.DT
        newc=c+gate.DT*w
        for sub in [1,2]:
            r={'tick':t,'substep':sub,'time_s':(2*t+sub)*.002,'phase':gate.phase(t),'contacts':0,'true_clearance_m':.02}
            values=[q,np.zeros(7),newc,q,np.zeros(7),w,alpha,jerk,np.zeros(7),np.zeros(7)]
            for prefix,value in zip(gate.PREFIXES,values):
                r.update({prefix+str(j):float(value[j]) for j in range(7)})
            raw.append(r)
        cycles.append({'tick':t,'full_cycle_wall_s':.001,'command_age_s':0 if t<500 else .0005,'status':'HOLD' if t<500 else 'SOLVED','deadline_miss':0})
        if t>=500:
            base=gate.base_rows(q,c,wprev,aprev,ranges[:,0],ranges[:,1])+[(np.eye(7)[0],-1.,float('inf'))]
            for kind in (['tracking'] if t<2500 else ['tracking','stop']):
                x=w.copy()
                if corrupt and t==2500 and kind=='tracking':x[0]=gate.V+1e-13
                violations=[max(0.,lo-float(sum(A*x)),float(sum(A*x))-hi) for A,lo,hi in base];si=max(violations)
                s={k:0 for k in gate.SOLVE_FIELDS};s.update(tick=t,kind=kind,wrapper_status='SOLVED',raw_status=1,api_error=0,iterations=1,SI_violation=si,maximum_violation_row=int(np.argmax(violations)) if si else -1,candidate_size=7,state_age_s=.0001,setup_s=.0001,solve_s=.0001)
                s.update({'x'+str(j):float(x[j]) for j in range(7)});solves.append(s)
                for index,(A,lo,hi) in enumerate(base):
                    r={'tick':t,'kind':kind,'row':index,'lower':lo,'upper':hi};r.update({'A'+str(j):A[j] for j in range(7)});rows.append(r)
        c,wprev,aprev=newc,w,alpha
    for name,fields,data in [('raw.csv',gate.RAW_FIELDS,raw),('cycles.csv',gate.CYCLE_FIELDS,cycles),('all_qp_solves.csv',gate.SOLVE_FIELDS,solves),('all_qp_rows.csv',gate.ROW_FIELDS,rows)]:
        file=case/name;file.unlink();write_csv(file,fields,data)
    changed=[r for r in solves if r['tick']==2500 and r['kind']=='tracking'][0]
    (case/'boundary_provenance.json').write_text(json.dumps({'scope':'Synthetic gate history only; no plant/model/optimality claim','corrupt_superseded_tracking':corrupt,'tracking_x0':changed['x0'],'V':gate.V,'original_SI':changed['SI_violation'],'stop_x0':gate.V,'all_other_capture_values_identical_to_boundary_control':True},indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();out=a.output;out.mkdir(exist_ok=False)
    baseline=out/'complete_positive_control';baseline.mkdir();packet=baseline/'packet';packet.mkdir()
    protocol=json.loads((P/'results/phase5/development/public-coupled-validation-91013-protocol-v1/protocol.json').read_text())
    protocol.update(schema=2,project_root=str(P),model_xml=str(P/'experiments/generated/inspection/inspection_fr3.xml'),robot_urdf=str(P/'models/fr3/fr3_arm.urdf'),phase4_config=str(P/'config/phase4.yaml'),synthetic_gate_fixture=True,purpose='Synthetic full data-integrity fixture; identity model stub; never plant/model validation or approval')
    (packet/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    paths=[SCORER,Path(__file__).resolve(),packet/'protocol.json']+[Path(protocol[k]) for k in ['public_model_source','public_model_constants','robot_urdf','phase4_config','model_xml','collector_configuration','collector']]
    freeze={'seed':91013,'files':{str(f):sha(f) for f in paths},'scope':'Synthetic isolated gate inputs only; no physical evidence, no approval'}
    (packet/'frozen.json').write_text(json.dumps(freeze,indent=2)+'\n')
    constants=json.loads(Path(protocol['public_model_constants']).read_text());ranges=np.array(constants['joint_range']).reshape(7,2);q=ranges.mean(axis=1);zero=np.zeros(7)
    raw=[];cycles=[];solves=[];qp_rows=[]
    for t in range(2501):
        for sub in [1,2]:
            r={'tick':t,'substep':sub,'time_s':(2*t+sub)*.002,'phase':gate.phase(t),'contacts':0,'true_clearance_m':.02}
            for prefix in gate.PREFIXES:
                for j in range(7):r[prefix+str(j)]=q[j] if prefix in ['q_before_','q_post_','target_'] else 0.
            raw.append(r)
        cycles.append({'tick':t,'full_cycle_wall_s':.001,'command_age_s':0 if t<500 else .0005,'status':'HOLD' if t<500 else 'SOLVED','deadline_miss':0})
        if t<500:continue
        base=gate.base_rows(q,q,zero,zero,ranges[:,0],ranges[:,1])
        for kind in (['tracking'] if t<2500 else ['tracking','stop']):
            s={k:0 for k in gate.SOLVE_FIELDS};s.update(tick=t,kind=kind,wrapper_status='SOLVED',raw_status=1,api_error=0,iterations=1,SI_violation=0.,maximum_violation_row=-1,candidate_size=7,state_age_s=.0001,setup_s=.0001,solve_s=.0001)
            solves.append(s)
            for index,(A,lo,hi) in enumerate(base):
                r={'tick':t,'kind':kind,'row':index,'lower':lo,'upper':hi};r.update({'A'+str(j):A[j] for j in range(7)});qp_rows.append(r)
            r={'tick':t,'kind':kind,'row':119,'lower':-1.,'upper':float('inf')};r.update({'A'+str(j):float(j==0) for j in range(7)});qp_rows.append(r)
    for name,fields,rows in [('raw.csv',gate.RAW_FIELDS,raw),('cycles.csv',gate.CYCLE_FIELDS,cycles),('all_qp_solves.csv',gate.SOLVE_FIELDS,solves),('all_qp_rows.csv',gate.ROW_FIELDS,qp_rows)]:write_csv(baseline/name,fields,rows)
    (baseline/'summary.yaml').write_text(yaml.safe_dump({'seed':91013,'fixture':'servo_validation','completed_stop':True,'primary_failure':'','stop_failure':'','min_clearance_m':.02,'max_physical_velocity_rad_s':0.}))
    names=['complete_positive_control','truncated_42row_control','empty_trace','warmup_only','future_endpoint_NaN','warmup_failure','QP_row_NaN_after_capture_hash','API_error_nonzero','failed_attempt_missing_row_group','duplicate_attempt_overwritten','schema_field_missing','time_discontinuity','state_discontinuity','applied_candidate_mismatch','base_row_missing','base_row_wrong_coefficient','base_row_wrong_history_bound','geometry_wrong_inf','sidecar_hash_missing','cycle_missing','terminal_velocity_not_stopped','summary_false_stop','physical_jerk_forged','nonfinite_prediction','warmup_model_failure','superseding_stop_positive','boundary_history_positive','superseded_tracking_continuation_invalid']
    results=[]
    for name in names:
        case=baseline if name==names[0] else out/name
        if case!=baseline:
            case.mkdir();shutil.copytree(packet,case/'packet')
            d=json.loads((case/'packet/protocol.json').read_text());(case/'packet/protocol.json').write_text(json.dumps(d,indent=2)+'\n')
            f=json.loads((case/'packet/frozen.json').read_text());del f['files'][str(packet/'protocol.json')];f['files'][str(case/'packet/protocol.json')]=sha(case/'packet/protocol.json');(case/'packet/frozen.json').write_text(json.dumps(f,indent=2)+'\n')
            for file in gate.CONSUMED:(case/file).hardlink_to(baseline/file)
        rawfile=case/'raw.csv';factory=NoPlantStub
        if name=='truncated_42row_control':rewrite(rawfile,lambda f,r:(f,r[:42]))
        elif name=='empty_trace':rewrite(rawfile,lambda f,r:(f,[]))
        elif name=='warmup_only':
            def change(f,r):
                for row in r:row['phase']='warmup'
                return f,r
            rewrite(rawfile,change)
        elif name=='future_endpoint_NaN':set_cell(rawfile,1000,'q_post_0','nan')
        elif name=='warmup_failure':set_cell(rawfile,0,'q_before_0','nan')
        elif name=='API_error_nonzero':set_cell(case/'all_qp_solves.csv',0,'api_error',999)
        elif name=='failed_attempt_missing_row_group':
            def change(f,r):
                bad=dict(r[0],tick=2501,wrapper_status='PRIMAL_INFEASIBLE',raw_status=3,api_error=1,candidate_size=0);return f,r+[bad]
            rewrite(case/'all_qp_solves.csv',change)
        elif name=='duplicate_attempt_overwritten':rewrite(case/'all_qp_solves.csv',lambda f,r:(f,[dict(r[0],wrapper_status='PRIMAL_INFEASIBLE')]+r))
        elif name=='schema_field_missing':
            def change(f,r):
                for row in r:del row['true_clearance_m']
                return [x for x in f if x!='true_clearance_m'],r
            rewrite(rawfile,change)
        elif name=='time_discontinuity':set_cell(rawfile,1000,'time_s',3.14)
        elif name=='state_discontinuity':set_cell(rawfile,1000,'q_before_0',.001)
        elif name=='applied_candidate_mismatch':set_cell(case/'all_qp_solves.csv',0,'x0',1e-5)
        elif name=='base_row_missing':rewrite(case/'all_qp_rows.csv',lambda f,r:(f,r[1:]))
        elif name=='base_row_wrong_coefficient':set_cell(case/'all_qp_rows.csv',0,'A0',2.)
        elif name=='base_row_wrong_history_bound':set_cell(case/'all_qp_rows.csv',7,'lower',-2.)
        elif name=='geometry_wrong_inf':set_cell(case/'all_qp_rows.csv',119,'upper','-inf')
        elif name=='cycle_missing':rewrite(case/'cycles.csv',lambda f,r:(f,r[:-1]))
        elif name=='terminal_velocity_not_stopped':set_cell(rawfile,-1,'v_post_0',.001)
        elif name=='summary_false_stop':
            file=case/'summary.yaml';d=yaml.safe_load(file.read_text());d['completed_stop']=False;file.unlink();file.write_text(yaml.safe_dump(d))
        elif name=='physical_jerk_forged':set_cell(rawfile,1000,'physical_jerk_0',1.)
        elif name=='nonfinite_prediction':factory=NonfinitePrediction
        elif name=='warmup_model_failure':factory=WarmupFailure
        elif name=='superseding_stop_positive':set_cell(case/'all_qp_solves.csv',-2,'x0',1e-7)
        elif name in ['boundary_history_positive','superseded_tracking_continuation_invalid']:boundary_fixture(case,q,ranges,name=='superseded_tracking_continuation_invalid')
        execution={'argv':[protocol['collector'],protocol['project_root'],protocol['collector_configuration'],'predictive','servo_validation','91013',str(case)],'return_code':0,'source_unchanged':True,'prepared_frozen_sha256':sha(case/'packet/frozen.json'),'raw_files':{file:sha(case/file) for file in gate.CONSUMED},'scope':'Synthetic gate fixture only; no collector invocation or run approval'}
        if name=='sidecar_hash_missing':del execution['raw_files']['all_qp_rows.csv']
        (case/'execution.json').write_text(json.dumps(execution,indent=2)+'\n')
        if name=='QP_row_NaN_after_capture_hash':set_cell(case/'all_qp_rows.csv',0,'A0','nan')
        buffer=io.StringIO()
        with contextlib.redirect_stdout(buffer),contextlib.redirect_stderr(buffer):code=gate.score(case/'packet',rawfile,case/'execution.json',case/'scored',factory)
        (case/'scorer.log').write_text(buffer.getvalue());report=json.loads((case/'scored/validation_report.json').read_text())
        expected=name in ['complete_positive_control','superseding_stop_positive','boundary_history_positive'];assert (code==0)==expected,(name,report)
        if name=='superseded_tracking_continuation_invalid':assert report.get('failure',{}).get('reason')=='all-attempt candidate continuation',report
        item={'name':name,'expected_pass':expected,'exit_code':code,'gate':report['gate'],'failure':report.get('failure'),'window_failures':len(report.get('failures',[])),'windows':sum(m['windows'] for m in report.get('metrics',[])),'scope':'Synthetic NoPlant gate regression only'};results.append(item);print(json.dumps(item),flush=True)
    audit={'scope':'Synthetic CSV/identity stub gate execution; no plant, no physical model accuracy claim, no approval','scorer_sha256':sha(SCORER),'audit_source_sha256':sha(Path(__file__)),'cases':results,'all_expected_outcomes':True,'old_v1_untouched':True}
    (out/'audit.json').write_text(json.dumps(audit,indent=2,allow_nan=False)+'\n')
    files={str(f.relative_to(out)):{'sha256':sha(f),'bytes':f.stat().st_size} for f in out.rglob('*') if f.is_file()}
    (out/'READY.json').write_text(json.dumps({'scope':audit['scope'],'files':files},indent=2)+'\n')

if __name__=='__main__':main()
