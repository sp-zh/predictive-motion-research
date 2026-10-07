#!/usr/bin/env python3
"""Only score a frozen soft-friction candidate on its new prospectively frozen trace."""
import argparse,json
from pathlib import Path
from servo_model_soft_friction_v2 import evaluate
from servo_model_v1 import trace,sha,write_new
p=argparse.ArgumentParser(description=__doc__)
for name in ['raw','execution','frozen','model','output']:
    p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args()
model=json.loads(a.model.read_text());execution=json.loads(a.execution.read_text());frozen=json.loads(a.frozen.read_text())
if execution['return_code']!=0 or execution['argv'][-2]!='91012':raise ValueError('new completed 91012 fixture required')
if frozen['files'].get(str(a.model))!=sha(a.model):raise ValueError('candidate not frozen/changed')
if execution['raw_files']['raw.csv']!=sha(a.raw):raise ValueError('trace identity changed')
if sha(Path(__file__).with_name('servo_model_soft_friction_v2.py'))!=model['script_sha256']:raise ValueError('prediction source changed')
rows,data=trace(a.raw);report=evaluate(model,rows,data)
report.update({'seed':91012,'model_sha256':sha(a.model),'raw_sha256':sha(a.raw),'frozen_sha256':sha(a.frozen),
               'script_sha256':sha(__file__),'validation_execution_sha256':sha(a.execution),
               'new_waveform_run_id':'servo-soft-friction-v2-validation','model_coefficients_unchanged':True})
a.output.mkdir(exist_ok=False);write_new(a.output/'validation_report.json',report)
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['gate']=='PASS_LOCAL_EMPIRICAL' else 1)
