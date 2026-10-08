"""Strict structural gate before any native numerical parity score."""
import json,math
class NativeOutputError(ValueError):pass
def need(condition,message):
 if not condition:raise NativeOutputError(message)
def load_native(path):
 def invalid(value):raise NativeOutputError('nonfinite JSON '+value)
 with open(path) as f:return json.load(f,parse_constant=invalid)
def number(x,label):
 need(type(x) in (int,float),'numeric type '+label)
 try:finite=math.isfinite(x)
 except (OverflowError,ValueError,TypeError):raise NativeOutputError('outside finite double range '+label)
 need(finite,'finite numeric '+label)
def vector(x,n,label):
 need(type(x) is list and len(x)==n,'vector length '+label)
 for item in x:number(item,label)
def integer(x,low,high,label):need(type(x) is int and low<=x<=high,'integer '+label)
def error_record(x):need(type(x.get('error')) is str and bool(x['error']),'explicit error string')
def roster(actual,expected,label):
 need(type(actual) is list and len(actual)==len(expected),'exact roster length '+label)
 names=[]
 for entry in actual:
  need(type(entry) is dict and type(entry.get('name')) is str,'named object '+label);names.append(entry['name'])
 need(len(names)==len(set(names)),'unique roster names '+label)
 need(names==[x['name'] for x in expected],'ordered roster names '+label)
def friction(x,n):
 need(type(x) is dict,'friction object');vector(x.get('force'),n,'friction force')
 labels=x.get('branches');need(type(labels) is list and len(labels)==n,'friction branch length')
 for label in labels:need(type(label) is int and label in (-1,0,1,2),'friction branch type/value')
 integer(x.get('iterations'),1,100,'friction iterations');number(x.get('original_KKT'),'original KKT')
 need(0<=x['original_KKT']<=1e-10,'native original KKT gate')
def state(x):
 need(type(x) is dict,'state object');vector(x.get('q'),7,'state q');vector(x.get('v'),7,'state v')
 integer(x.get('control_clips'),0,7,'control clips');integer(x.get('force_clips'),0,7,'force clips');friction(x.get('friction'),7)
def validate_output(native,inputs):
 def finite_tree(value):
  if type(value) in (int,float):number(value,'all native numeric values')
  elif type(value) is dict:
   for child in value.values():finite_tree(child)
  elif type(value) is list:
   for child in value:finite_tree(child)
 finite_tree(native)
 need(type(native) is dict and type(native.get('model_success')) is bool and native['model_success'],'typed successful model')
 m=native.get('metadata');need(type(m) is dict,'metadata object')
 for key in ('nq','nv'):need(type(m.get(key)) is int and m[key]==7,'metadata '+key)
 for key in ('idx_q','idx_v'):need(type(m.get(key)) is list and all(type(x) is int for x in m[key]) and m[key]==list(range(7)),'metadata indices')
 for key in ('joint_nq','joint_nv'):need(type(m.get(key)) is list and all(type(x) is int for x in m[key]) and m[key]==[1]*7,'metadata joint dimensions')
 for key,n in [('masses',8),('armature',7),('gravity',3),('R',7),('B',7),('D',7)]:vector(m.get(key),n,'metadata '+key)
 for key in ('units','pinocchio_version'):need(type(m.get(key)) is str and bool(m[key]),'metadata string')
 for key in ('joint_names','frame_names'):
  need(type(m.get(key)) is list and bool(m[key]) and all(type(x) is str and x for x in m[key]),'metadata names')
 need(len(m['joint_names'])==len(set(m['joint_names']))==7 and m['pinocchio_version']=='4.1.0','metadata fixed mapping/version')
 roster(native.get('cases'),inputs['cases'],'state');roster(native.get('box_cases'),inputs['box_cases'],'box')
 for inp,out in zip(inputs['cases'],native['cases']):
  need(type(out.get('success')) is bool,'typed state success');need(out['success']==inp['expect_success'],'expected state outcome')
  trace=out.get('trace');need(type(trace) is list,'state trace array')
  for point in trace:state(point)
  if not out['success']:
   error_record(out);need(len(trace)==inp.get('expected_partial_steps',0),'negative retained trace length');continue
  need(len(trace)==len(inp['targets']),'complete trace length')
  need(bool(trace),'nonempty successful trace');last=out.get('last');state(last)
  for key in ('q','v','friction','control_clips','force_clips'):need(last[key]==trace[-1][key],'last/trace consistency')
  for key in ('M','W','H'):
   value=last.get(key);need(type(value) is list and len(value)==7,'matrix rows '+key)
   for row in value:vector(row,7,'matrix '+key)
  for key in ('ell','bias','smooth','actuator','controls'):vector(last.get(key),7,'last '+key)
 serialization_rejections=[]
 for inp,out in zip(inputs['box_cases'],native['box_cases']):
  need(type(out.get('success')) is bool,'typed box success')
  if not out['success']:
   error_record(out)
   if inp['expect_success']:
    need(inp.get('serialization_may_reject') is True and 'bad conversion' in out['error'],'unsupported serialization only')
    serialization_rejections.append({'name':inp['name'],'error':out['error'],'scope':'Input serialization rejection; not solver arithmetic acceptance.'})
   need('result' not in out,'failed box has no success result');continue
  need(inp['expect_success'],'expected box outcome');friction(out.get('result'),len(inp['ell']))
 return serialization_rejections
