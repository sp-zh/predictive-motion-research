"""Independent final-v2 structural gate tests; no native/plant execution."""
from pathlib import Path
import argparse
import json,hashlib,tarfile,importlib.util,copy
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--gate',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
source=args.gate;b=source.read_bytes();assert hashlib.sha256(b).hexdigest()=='70b79c6c4d2d9a78a47e8f4e1c02c6587bf4df94f6303350fd4128db87cd6437';(args.output/'GATE_SNAPSHOT.py').write_bytes(b);(args.output/'SOURCE_SNAPSHOT.py').write_bytes(Path(__file__).read_bytes());spec=importlib.util.spec_from_file_location('root_gate_snapshot',source);gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
a=Path('transfer/incoming/root-public-coupled-cpp-v1-20261007/evidence.tar.gz')
with tarfile.open(a) as t:
 native=json.loads(t.extractfile('native_output.json').read());inputs=json.loads(t.extractfile('cases.json').read())
for item in inputs['cases']+inputs['box_cases']:item['expect_success']=item['expected_success']
mutations=[('valid_control',lambda x:None,True),('empty_state',lambda x:x.update(cases=[]),False),('drop_state_tail',lambda x:x['cases'].pop(),False),('drop_box_tail',lambda x:x['box_cases'].pop(),False),('duplicate_state',lambda x:x['cases'][1].update(name=x['cases'][0]['name']),False),('string_success',lambda x:x['cases'][0].update(success='true'),False),('short_trace',lambda x:x['cases'][0]['trace'].pop(),False),('NaN_state',lambda x:x['cases'][0]['trace'][0]['q'].__setitem__(0,float('nan')),False),('bool_q',lambda x:x['cases'][0]['trace'][0]['q'].__setitem__(0,True),False),('float_iterations',lambda x:x['cases'][0]['trace'][0]['friction'].update(iterations=1.0),False),('huge_integer_q',lambda x:x['cases'][0]['trace'][0]['q'].__setitem__(0,10**1000),False)]
reports=[]
for name,change,expected in mutations:
 data=copy.deepcopy(native);change(data)
 try:gate.validate_output(data,inputs);passed=True;reason=None
 except Exception as e:passed=False;reason=type(e).__name__+': '+str(e)
 assert passed==expected,(name,reason)
 reports.append({'name':name,'accepted':passed,'reason':reason})
assert source.read_bytes()==b
report={'scope':'Final structural gate isolation on copied old native output; deterministic in-memory corruptions, no v2 native/physics/model execution. Actual source implementation and captured data remain unchanged.','gate_source_sha256':hashlib.sha256(b).hexdigest(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'control_archive_sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'cases':reports,'all_expected_outcomes':True};(args.output/'audit.json').write_text(json.dumps(report,indent=2)+'\n');files={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in args.output.iterdir() if p.is_file()};(args.output/'READY.json').write_text(json.dumps({'scope':report['scope'],'files':files},indent=2)+'\n');print(json.dumps(report,indent=2))
