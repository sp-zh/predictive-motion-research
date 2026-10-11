from pathlib import Path
import struct,json,math,sys,hashlib
class R:
 def __init__(self,p):self.b=p.read_bytes();self.i=0
 def raw(self,n):b=self.b[self.i:self.i+n];assert len(b)==n;self.i+=n;return b
 def u(self):return struct.unpack('<Q',self.raw(8))[0]
 def signed(self):n=self.u();return n if n<(1<<63) else n-(1<<64)
 def f(self):return struct.unpack('<d',self.raw(8))[0]
 def text(self):return self.raw(self.u()).decode()
 def vec(self):n=self.u();assert n<=1000000;return [self.f() for _ in range(n)]
 def head(self):assert self.text()=='P5_ACTIVE_SESSION_LOSSLESS_V1';return self.text()
 def end(self):assert self.i==len(self.b),(self.i,len(self.b))
def parse(path):
 q=R(path);d={'role':q.head(),'attempted':q.u(),'complete':q.u(),'error':q.text(),'nominal_digest':q.text(),'geometry_config_sha256':q.text(),'observation_id':q.text(),'transaction_id':q.text(),'boundary':[q.u(),q.u()],'simulation_time':q.f(),'scope':q.text(),'row_count':q.u(),'samples':[]}
 for _ in range(q.u()):
  s={k:q.u() for k in ['sample','cell','cycle','half']};s.update(elapsed=q.f(),nominal_q=q.vec(),minimum_true=q.f(),minimum_cover=q.f(),full_query_count=q.u(),selected=[])
  for _ in range(q.u()):
   r={'sample':q.u(),'id':q.text(),'units':q.text(),'Jq':q.vec(),'nominal_value':q.f(),'lower':q.f(),'upper':q.f(),'a':q.text(),'b':q.text(),'type':q.text(),'cover_index':q.signed(),'covered_tool_environment':q.u(),'distance':q.f(),'normal':q.vec(),'witness_a':q.vec(),'witness_b':q.vec(),'gradient':q.vec()};s['selected'].append(r)
  d['samples'].append(s)
 d['provider_cumulative']={k:q.u() for k in ['scene_attempts','scene_returns','primitive_attempts','true_attempts','true_returns','cover_attempts','cover_returns','fk_attempts','fk_returns','jac_attempts','jac_returns']};d.update(separate_logical_reservation=q.u(),reservation_scope=q.text());q.end()
 if d['complete']:
  assert d['attempted']==1 and not d['error'] and d['row_count']==1600 and len(d['samples'])==400 and d['separate_logical_reservation']==200000
  for i,s in enumerate(d['samples']):
   assert s['sample']==i and abs(s['elapsed']-.002*(i+1))<=1e-10 and len(s['nominal_q'])==7 and all(math.isfinite(x) for x in s['nominal_q']) and s['full_query_count']==9035
   assert [r['type'] for r in s['selected']]==['true','true','cover','cover']
   for r in s['selected']:
    assert r['sample']==i and r['id']==r['type']+'/'+r['a']+'/'+r['b']+'/cover/'+str(r['cover_index']) and r['units']=='m' and r['lower']==.005 and r['upper']==1000000 and r['Jq']==r['gradient'] and len(r['Jq'])==7 and all(math.isfinite(x) for x in r['Jq']) and r['nominal_value']==r['distance']
    assert abs(sum(v*v for v in r['normal'])**.5-1)<=1e-6 and sum((b-a-r['distance']*n)**2 for a,b,n in zip(r['witness_a'],r['witness_b'],r['normal']))**.5<=1e-6
   assert s['selected'][0]['distance']==s['minimum_true'] and s['selected'][2]['distance']==s['minimum_cover']
 return d
if __name__=='__main__':
 root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(exist_ok=False);result=[]
 for p in sorted(root.glob('cycle-*/nominal_geometry_rows.bin')):
  d=parse(p);(out/(p.parent.name+'.json')).write_text(json.dumps(d,indent=2)+'\n');result.append({'cycle':p.parent.name,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'complete':d['complete'],'error':d['error'],'samples':len(d['samples']),'rows':d['row_count'],'counts':d['provider_cumulative'],'scope':'selected4 and retained full minima checked; all9035 full queries not retained; no fresh collision query'})
 (out/'SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
