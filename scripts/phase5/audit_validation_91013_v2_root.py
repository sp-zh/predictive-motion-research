#!/usr/bin/env python3
"""Independent capture-integrity corruptions of a disclosed synthetic fixture.

No collector, plant, public predictor or run approval is executed. Fixture
metadata is rebuilt for each isolated case; supplied captured bytes stay intact.
"""
import argparse, csv, hashlib, importlib.util, json, shutil
from pathlib import Path

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d): p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def alter(path,index,column,value):
    with path.open() as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    rows[index][column]=value
    path.unlink()
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for arg in ('scorer','fixture','output'): ap.add_argument('--'+arg,type=Path,required=True)
    a=ap.parse_args(); src=Path(__file__).resolve(); source_hash=sha(src); scorer_hash=sha(a.scorer)
    spec=importlib.util.spec_from_file_location('reviewed_gate',a.scorer);gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
    out=a.output;out.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(src,out/'SOURCE_SNAPSHOT.py');shutil.copyfile(a.scorer,out/'SCORER_SNAPSHOT.py')
    supplied=json.loads((a.fixture/'packet/protocol.json').read_text())
    report={'scope':'Root independent synthetic capture-integrity execution only. No forecast/model/plant/approval; no Phase5 acceptance. Metadata rebuilt and hashes re-signed after disclosed corruptions so structural checks, rather than hash mismatch alone, are exercised.','source_sha256':source_hash,'scorer_sha256':scorer_hash,'input_fixture':str(a.fixture),'cases':[]}
    cases=[('complete_positive_control',None),('base_bound_relaxed',( 'all_qp_rows.csv',0,'lower',-1.)),('base_coefficient_erased',('all_qp_rows.csv',0,'A0',0.)),('interior_clock_shift',('raw.csv',1501,'time_s',3.0045)),('unapplied_API_error',('all_qp_solves.csv',-2,'api_error',7)),('geometry_lower_positive_infinity',('all_qp_rows.csv',119,'lower','inf')),('summary_velocity_disagrees',None),('deadline_flag_disagrees',('cycles.csv',1000,'deadline_miss',1))]
    for name,mutation in cases:
        case=out/name;case.mkdir();packet=case/'packet';packet.mkdir()
        for f in gate.CONSUMED:(case/f).hardlink_to(a.fixture/f)
        if mutation:alter(case/mutation[0],*mutation[1:])
        if name=='summary_velocity_disagrees':
            p=case/'summary.yaml';d=gate.yaml.safe_load(p.read_text());d['max_physical_velocity_rad_s']=.01;p.unlink();p.write_text(gate.yaml.safe_dump(d))
        protocol=dict(supplied,purpose=report['scope'],synthetic_gate_fixture=True)
        dump(packet/'protocol.json',protocol)
        inputs=[a.scorer.resolve(),src,packet/'protocol.json']+[Path(protocol[k]) for k in ['public_model_source','public_model_constants','robot_urdf','phase4_config','model_xml','collector_configuration','collector']]
        freeze={'seed':91013,'files':{str(p):sha(p) for p in inputs},'scope':report['scope']};dump(packet/'frozen.json',freeze)
        execution={'argv':[protocol['collector'],protocol['project_root'],protocol['collector_configuration'],'predictive','servo_validation','91013',str(case)],'return_code':0,'source_unchanged':True,'prepared_frozen_sha256':sha(packet/'frozen.json'),'raw_files':{f:sha(case/f) for f in gate.CONSUMED},'scope':report['scope']};dump(case/'execution.json',execution)
        try:
            _,_,_,_,rows,_,audit=gate.inspect_capture(packet,case/'raw.csv',case/'execution.json')
            result={'name':name,'accepted':True,'audit':audit,'rows':len(rows)}
        except Exception as exc:result={'name':name,'accepted':False,'failure_type':type(exc).__name__,'reason':str(exc)}
        assert result['accepted']==(name=='complete_positive_control'),result
        report['cases'].append(result);print(json.dumps(result),flush=True)
    assert sha(a.scorer)==scorer_hash and sha(src)==source_hash
    report['all_expected_outcomes']=True;dump(out/'audit.json',report)
    files={str(p.relative_to(out)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in out.rglob('*') if p.is_file()}
    dump(out/'READY.json',{'scope':report['scope'],'files':files})
if __name__=='__main__':main()
