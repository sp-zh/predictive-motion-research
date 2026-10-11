from pathlib import Path
import struct,json,math,sys
class R:
 def __init__(self,p):self.b=p.read_bytes();self.i=0
 def raw(self,n):b=self.b[self.i:self.i+n];assert len(b)==n;self.i+=n;return b
 def u(self):return struct.unpack('<Q',self.raw(8))[0]
 def d(self):return struct.unpack('<d',self.raw(8))[0]
 def text(self):return self.raw(self.u()).decode()
 def head(self):assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1';return self.text()
 def end(self):assert self.i==len(self.b),(self.i,len(self.b))
def record(q):
 out={'boundary':[q.u(),q.u()],'commit_success':q.u(),'commit_error':q.text(),'points':[]}
 for _ in range(q.u()):
  t={'half':q.u(),'actual_simulation_time':q.d(),'raw_pose_available':q.u(),'actual_elapsed':q.d(),'logical_elapsed':q.d(),'logical_s':q.d(),'logical_r':q.d()}
  if t['raw_pose_available']:
   for kind in ['actual','desired']:t[kind]={'world_position':[q.d() for _ in range(3)],'world_rotation_rowmajor':[q.d() for _ in range(9)]}
  t['measured']=q.u()
  if t['measured']:t.update(translation_error_m=q.d(),rotation_angle_rad=q.d(),within_10mm_005rad=q.u())
  t.update(commit_point_passed=q.u(),stage=q.text(),error=q.text());out['points'].append(t)
 out['scope']=q.text();return out
root=Path(sys.argv[1]);dest=Path(sys.argv[2]);dest.mkdir(exist_ok=False);rows=[]
for k in range(3):
 q=R(root/f'cycle-{k}/actual_task_errors.bin');assert q.head()=='ACTUAL_WORLD_TCP_TASK_ERROR_TWO_PHYSICAL_HALVES_V1';t=record(q);q.end();before=json.loads((root.parent.parent.parent.parent.parent/'none').read_text()) if False else None
 assert t['boundary']==[k,k] and t['commit_success']==1 and not t['commit_error'] and len(t['points'])==2
 for n,p in enumerate(t['points'],1):
  assert p['half']==n and p['logical_elapsed']==.002*n and p['raw_pose_available'] and p['measured'] and p['commit_point_passed'] and not p['error']
  A,B=p['actual'],p['desired'];pa,pb=A['world_position'],B['world_position'];Ra,Rb=A['world_rotation_rowmajor'],B['world_rotation_rowmajor'];translation=math.hypot(*[b-a for a,b in zip(pa,pb)]);rel=[sum(Ra[3*h+i]*Rb[3*h+j] for h in range(3)) for i in range(3) for j in range(3)];cosine=min(1.,max(-1.,(rel[0]+rel[4]+rel[8]-1)*.5));sine=.5*math.hypot(rel[7]-rel[5],rel[2]-rel[6],rel[3]-rel[1]);angle=math.atan2(sine,cosine);assert abs(translation-p['translation_error_m'])<=1e-12 and abs(angle-p['rotation_angle_rad'])<=1e-12
  assert translation<=.01 and angle<=.05 and p['within_10mm_005rad']==1 and p['logical_s']>0 and p['logical_r']>0;rows.append({'cycle':k,**p})
 (dest/f'cycle-{k}.json').write_text(json.dumps(t,indent=2)+'\n')
summary={'actual_points':len(rows),'maximum_translation_error_m':max(p['translation_error_m'] for p in rows),'maximum_rotation_angle_rad':max(p['rotation_angle_rad'] for p in rows),'final_s':rows[-1]['logical_s'],'final_r':rows[-1]['logical_r'],'scope':'6actual2ms native scratch worldTCP poses vsprivatepinnedTd atlogical controllerprogress; Euclideanworldposition/SO3angle, notSE3logtranslation; nofulltask/stop/phaseacceptance'};(dest/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');(dest/'ALL_ACTUAL_TASK_POINTS.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(summary))
