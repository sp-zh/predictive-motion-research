#!/usr/bin/env python3
"""Replay only the integrity audit on already recorded 91012 data.

An isolated synthetic packet/summary seed mapping adapts the 91013 gate.
Original raw data and its summary stay immutable. No model or plant runs.
"""
import argparse,hashlib,importlib.util,json,pathlib,shutil,traceback,yaml
p=pathlib.Path('/home/codextransfer/predictive_motion')
source=p/'scripts/phase5/score_public_coupled_validation_91013_v2.py'
spec=importlib.util.spec_from_file_location('strict_gate',source);gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
parser=argparse.ArgumentParser();parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args();out=args.output;out.mkdir(exist_ok=False);packet=out/'synthetic_packet';packet.mkdir()
original=pathlib.Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-safe-reference-v3-validation')
protocol=json.loads((p/'results/phase5/development/public-coupled-validation-91013-protocol-v1/protocol.json').read_text())
protocol.update(schema=2,project_root=str(p),model_xml=str(p/'experiments/generated/inspection/inspection_fr3.xml'),robot_urdf=str(p/'models/fr3/fr3_arm.urdf'),phase4_config=str(p/'config/phase4.yaml'),synthetic_gate_fixture=True,purpose='Integrity replay of old physical seed91012 only, isolated synthetic metadata seed mapping; no91013/model/plant run')
(packet/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
files=[source,pathlib.Path(__file__),packet/'protocol.json']+[pathlib.Path(protocol[k]) for k in ['public_model_source','public_model_constants','robot_urdf','phase4_config','model_xml','collector_configuration','collector']]
(packet/'frozen.json').write_text(json.dumps({'seed':91013,'files':{str(f):gate.sha(f) for f in files},'scope':protocol['purpose']},indent=2)+'\n')
hashes={}
for name in gate.CONSUMED:
 f=original/name;hashes[name]=gate.sha(f);shutil.copyfile(f,out/name)
summary=yaml.safe_load((out/'summary.yaml').read_text());assert summary['seed']==91012;summary['seed']=91013;summary['scope']=protocol['purpose'];(out/'summary.yaml').write_text(yaml.safe_dump(summary))
execution={'argv':[protocol['collector'],str(p),protocol['collector_configuration'],'predictive','servo_validation','91013',str(out)],'return_code':0,'source_unchanged':True,'prepared_frozen_sha256':gate.sha(packet/'frozen.json'),'raw_files':{name:gate.sha(out/name) for name in gate.CONSUMED},'scope':protocol['purpose']}
(out/'synthetic_execution.json').write_text(json.dumps(execution,indent=2)+'\n')
report={'scope':protocol['purpose'],'original_seed':91012,'synthetic_schema_seed':91013,'no_model_step_or_collector_executed':True,'original_capture_sha256':hashes,'scorer_sha256':gate.sha(source),'audit_source_sha256':gate.sha(pathlib.Path(__file__))}
try:
 _,_,_,_,_,_,audit=gate.inspect_capture(packet,out/'raw.csv',out/'synthetic_execution.json');report.update(gate='PASS_RECORDED_91012_CAPTURE_INTEGRITY_REPLAY_ONLY',audit=audit)
except Exception as exc:
 report.update(gate='FAIL_RECORDED_CAPTURE_INTEGRITY_REPLAY',failure={'type':type(exc).__name__,'reason':str(exc)});(out/'traceback.txt').write_text(traceback.format_exc())
assert all(gate.sha(original/name)==digest for name,digest in hashes.items())
(out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');print(json.dumps(report,indent=2))
(out/'SCORER_SNAPSHOT.py').write_bytes(source.read_bytes());(out/'AUDIT_SNAPSHOT.py').write_bytes(pathlib.Path(__file__).read_bytes())
manifest={str(f.relative_to(out)):{'sha256':gate.sha(f),'bytes':f.stat().st_size} for f in out.rglob('*') if f.is_file()};(out/'READY.json').write_text(json.dumps({'scope':protocol['purpose'],'files':manifest},indent=2)+'\n')
raise SystemExit(0 if report['gate'].startswith('PASS') else 1)
