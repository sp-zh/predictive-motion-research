from pathlib import Path
import sys,os,json,hashlib,ast,struct,math
import numpy as np
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write
import root61_parser_and_formal_review_v1 as m61
m60=m61.m60;strict=m61.strict;parse=m61.parse;check_receipt=m61.check_receipt
ROOT=Path('/Users/uot/Documents/ChatGPT/ros');BASE=Path('/private/tmp/phase5_current_braking_nominal62_source_v3_20261016');O=Path('/private/tmp/root62_stop_cause_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
t=ast.parse(Path('/private/tmp/root61_parser_and_formal_review_v1.py').read_text());main=next(n for n in t.body if isinstance(n,ast.FunctionDef)and n.name=='main');start=next(i for i,n in enumerate(main.body)if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='tree'for x in n.targets));body=[n for n in main.body[start:]if not(isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='print')];exec(compile(ast.Module(body=body,type_ignores=[]),'<retained formal-only audit>','exec'))
old=Path('/private/tmp/phase5_exact_cycle_endpoint61_source_v1_20261016/production_math_pure_v1/readback');current=BASE/'production_math_pure_v1/readback';rows=[]
for case in['actual56_48_1','old52_40_0','old53_40_1','old54_43_0','old55_40_2','actual58_54_0','actual58_74_0','actual60_43_0']:
 for ext in['finalxy.bin','states.bin','boundary48.bin','retained64.bin','refinement120.bin']:
  p='stop_'+case+'.'+ext;assert(current/p).read_bytes()==(old/p).read_bytes()
 rows.append(case)
for case in['old52_40_0','old53_40_1','old54_43_0','ACTIVE_constrained','ACTIVE_interior','ACTIVE_zero']:
 p='active_'+case+'.core.bin';assert(current/p).read_bytes()==(old/p).read_bytes()
bounded_write(O/'FORMAL62_ALL8_FIVECORES6ACTIVE_BITEXACT61.json',json.dumps(dict(schema='ROOT62V3_ALL_OLD_NUMERIC_CORES_BYTEEXACT61_V1',root_reader_qualification='Initial retained formal-only audit omitted m60 module alias in globals; NameError before any report write. Corrected reader alias only, no helper/Model/native/capture repeated.',eight_stop_cases=rows,all_five_core_files_equal=True,six_active_entire_core_equal=True,original_saved_row_primal_1e12_and_stationarity_1e10_gates_verified=True,scope='Old fixed QP regression and original merged diagnostics only. Current-history nominal changes future matrices; this does not prove new Model/B/C/physical stopping.'),indent=2)+'\n');print(json.dumps({'formal_payloads':number,'stop':8,'active':6,'all_core_bytes_exact61':True}))
