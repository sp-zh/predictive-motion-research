"""Independent V7/V8 saved planning-guard parser. Never calls solver/Model."""
from pathlib import Path
import struct,math,sys,importlib.util
import numpy as np
OLD='EXPLICIT_ALPHA_PROGRESS_JERK_CURRENT_FIRST_COMMAND_AND_FIRST_PROGRESS_BAND_V7'
NEW='EXPLICIT_ORIGINAL_STRICT_FIRST_COMMAND_WITH_INWARD_SOLVER_INTERVAL_AND_AFFINE_SEED_V8'
class Wire:
 def __init__(self,raw):
  assert len(raw)<=256*1024;self.raw=raw;self.at=0
 def take(self,fmt):
  n=struct.calcsize(fmt);assert self.at+n<=len(self.raw);v=struct.unpack_from(fmt,self.raw,self.at);self.at+=n;return v
 def u(self):return self.take('<Q')[0]
 def d(self):return self.take('<d')[0]
 def text(self):
  n=self.u();assert n<=256*1024 and self.at+n<=len(self.raw);v=self.raw[self.at:self.at+n].decode();self.at+=n;return v
 def vec(self):
  n=self.u();assert n<=20000 and self.at+8*n<=len(self.raw);a=np.frombuffer(self.raw,dtype='<f8',count=n,offset=self.at).copy();self.at+=8*n;return a
 def mat(self):
  n,m=self.take('<2Q');assert n*m<=3000000 and self.at+8*n*m<=len(self.raw);a=np.frombuffer(self.raw,dtype='<f8',count=n*m,offset=self.at).copy().reshape(n,m);self.at+=8*n*m;return a

def parse_raw(raw,variable_scale=None):
 r=Wire(raw);assert r.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1';role=r.text();assert role in [OLD,NEW]
 solver_alpha,strict_alpha,solver_jerk,strict_jerk,previous_b,terminal=r.take('<6d');base=r.u();cols=r.take('<'+str(r.u())+'Q');scales=r.vec();backend=r.text();center=r.vec();limiting_row=r.u();trustrows=r.take('<'+str(r.u())+'Q');trustproof=r.mat();margin=r.d();stop=r.u();assert stop in [0,1]and r.take('<3d')==(.5,.75,1e-6);count=r.u();assert count==(7 if stop else 0);first=[]
 assert len(center)==160 and len(cols)==len(scales)==160 and trustproof.shape==(len(trustrows),4)
 for j in range(count):
  assert r.u()==j;w,nom,nw,sb,tb,lower,upper=r.take('<7d');assert nom==center[j]
  actual_sb=max(.5*abs(w),abs(w+.004*nom),.5e-6);actual_tb=math.nextafter(max(.75*abs(w),abs(w+.004*nom),.75e-6)*(1+16*sys.float_info.epsilon),math.inf)
  L=min(max(max(-1.,nom-solver_alpha),math.nextafter((-actual_sb-w)/.004,-math.inf)),nom);U=max(min(min(1.,nom+solver_alpha),math.nextafter((actual_sb-w)/.004,math.inf)),nom)
  assert(nw,sb,tb,lower,upper)==(w+.004*nom,actual_sb,actual_tb,L,U)
  first.append(dict(joint0=j,w=w,nominal=nom,strict_bound=tb,lower=lower,upper=upper))
 physical=r.u();floors=r.take('<2d');assert physical in [0,1]and floors==(1e-7,.75e-7);interior=[]
 if role==NEW:
  assert stop==physical==1 and r.u()==7 and variable_scale is not None and len(variable_scale)==144
  for j in range(7):
   assert r.u()==j;fields=r.take('<9d');oldL,oldU,lower,upper,delta,scaled_delta,blend,alpha,y=fields;a=first[j];assert(oldL,oldU)==(a['lower'],a['upper']);mult=float(scales[j]);D=float(variable_scale[j]);assert mult==1/max(1.,D)
   width=oldU-oldL;inset=min(32*1e-9/mult,width/8);expected_lower=math.nextafter(oldL+inset,math.inf);expected_upper=math.nextafter(oldU-inset,-math.inf);expected_blend=4*inset/width;expected_alpha=a['nominal']+expected_blend*(oldL+.5*width-a['nominal'])
   assert fields==(oldL,oldU,expected_lower,expected_upper,inset,mult*inset,expected_blend,expected_alpha,expected_alpha/D)
   assert oldL<lower<alpha<upper<oldU and 0<blend<=.5 and scaled_delta>4e-12
   interior.append(dict(joint0=j,old_lower=oldL,old_upper=oldU,lower=lower,upper=upper,inset=inset,blend=blend,seed_alpha=alpha,seed_y=y))
 scope_at=r.at;scope=r.text();assert r.at==len(raw)
 return dict(role=role,base=base,solver_alpha=solver_alpha,strict_alpha=strict_alpha,solver_jerk=solver_jerk,strict_jerk=strict_jerk,previous_b=previous_b,terminal=terminal,first=first,interior=interior,scope=scope,scope_offset=scope_at)

def parse(path,canonical_reader,variable_scale=None):
 spec=importlib.util.spec_from_file_location('guard_strict',canonical_reader);strict=importlib.util.module_from_spec(spec);spec.loader.exec_module(strict);raw,receipt=strict.verify_artifact(Path(path),collect=True,require_source_complete=True);out=parse_raw(raw,variable_scale);out['source_receipt']=receipt;return out
