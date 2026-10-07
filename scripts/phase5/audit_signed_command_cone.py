#!/usr/bin/env python3
"""Independent exact-binary-input sequence audit of a frozen C++ header.

No production Python import, fitting, QP, or physical simulation. Run from
the repository root; extraction of the two frozen archives is a prerequisite.
"""
import base64
import csv
from fractions import Fraction as F
import hashlib
import io
import json
import math
from pathlib import Path
import random
import subprocess

OUT = Path('results/phase5-reference/root-signed-command-cone-audit-20261007-v1')
SOURCE = Path(__file__).resolve()
SOURCE_SHA = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
CPP = r'''#include "signed_velocity_cone.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
int main(int argc,char** argv){
 if(argc!=2)return 2;
 std::cerr<<"long_double_digits="<<std::numeric_limits<long double>::digits<<"\n";
 std::ifstream in(argv[1]);std::string line;std::getline(in,line);
 std::cout<<std::setprecision(17)<<"kind,id,k,w,alpha,lower,upper,feasible\n";
 while(std::getline(in,line)){
  std::istringstream s(line);std::string c;std::getline(s,c,',');int id=std::stoi(c);
  double x[6];for(double& v:x){std::getline(s,c,',');v=std::stod(c);}
  phase5_diagnostic::Limits l{x[2],x[3],x[4],x[5]};
  try{
   auto t=phase5_diagnostic::accelerationInterval(x[0],x[1],l);
   std::cout<<"interval,"<<id<<",0,"<<x[0]<<','<<x[1]<<','<<t.lower<<','<<t.upper<<','<<t.feasible<<'\n';
   for(auto r:phase5_diagnostic::candidateVelocityRows(x[0],l))
    std::cout<<"row,"<<id<<','<<r.coefficient<<','<<x[0]<<','<<x[1]<<','<<r.lower<<','<<r.upper<<",0\n";
   if(!t.feasible)continue;
   double w=x[0],a=x[1];
   for(int k=0;k<256;++k){
    auto z=phase5_diagnostic::accelerationInterval(w,a,l);
    std::cout<<"greedy,"<<id<<','<<k<<','<<w<<','<<a<<','<<z.lower<<','<<z.upper<<','<<z.feasible<<'\n';
    if(!z.feasible)break;
    double b=std::clamp(-w/l.dt,z.lower,z.upper);w+=l.dt*b;a=b;
    if(std::abs(w)<1e-14&&std::abs(a)<1e-14)break;
   }
  }catch(const std::exception& e){std::cout<<"rejected,"<<id<<",0,0,0,0,0,0\n";}
 }
}'''

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def exact_interval(case):
    w, old, V, A, J, dt = map(F, case)
    if abs(w)>V or abs(old)>A:
        return None
    count = math.ceil(A/(J*dt))+1
    # Exhaustive integer prefixes, rather than a stationary-point shortcut.
    upper = min((V-w)/(dt*k)+J*dt*(k-1)/2 for k in range(1,count+1))
    lower = max((-V-w)/(dt*k)-J*dt*(k-1)/2 for k in range(1,count+1))
    lo, hi = max(-A,old-J*dt,lower), min(A,old+J*dt,upper)
    return (lo,hi) if lo<=hi else None

def recovery(w, a, case):
    """Exact rational maximal-jerk recovery; records all velocity prefixes."""
    V,A,J,dt=map(F,case[2:]);w,a=F(w),F(a)
    seq=[]
    for k in range(math.ceil(A/(J*dt))+2):
        w += dt*a
        seq.append((float(w),float(a)))
        if abs(w)>V:return False,seq,float(abs(w)-V)
        if a==0:return True,seq,0.
        a=max(F(0),a-J*dt) if a>0 else min(F(0),a+J*dt)
    raise AssertionError('finite recovery failed to finish')

def run():
    frozen=OUT/'frozen/project'
    inputs={}
    for stem, expected in [('signed-command-cone-cpp','b13fee314f7b1717725424bdf564b478b3add9ad025da177ff54c941c2340d47'),('signed-command-cone','263126c58e090ea7f9bb5f44b41000fb3b894f1f4ff4121872cbd643afb6a62d')]:
        p=Path('results/phase5-executor-checkpoints-01a114d9')/stem/(stem+'-v1.tar.gz')
        assert sha(p)==expected
        inputs[str(p)]={'sha256':expected,'bytes':p.stat().st_size}
    for folder in [OUT/'frozen/project',OUT/'python_frozen/project']:
        manifest=next(folder.glob('results/phase5/development/*/BACKUP_SOURCE_MANIFEST.json'))
        for name, meta in json.loads(manifest.read_text()).items():
            p=folder/name
            assert sha(p)==meta['sha256'] and p.stat().st_size==meta['bytes']
        inputs[str(manifest)]={'sha256':sha(manifest)}
    header=frozen/'tools/phase5_command_cone/signed_velocity_cone.hpp'
    py=frozen/'scripts/phase5/signed_command_velocity_cone.py'
    assert sha(py)==sha(OUT/'python_frozen/project/scripts/phase5/signed_command_velocity_cone.py')
    raw=OUT/'frozen/raw/retained-v1/raw.csv'
    assert sha(raw)=='561d63684b3acc591acf2f287e6f7f264a340207cebe8767887b5107dadc661c'
    inputs.update({str(p):{'sha256':sha(p)} for p in [header,py,raw]})
    history={int(r['tick']):r for r in csv.DictReader(raw.open())}
    base=(.0625,1.,20.,.004)
    cases=[]; names=[]
    def add(name,w,a,limits=base):names.append(name);cases.append((w,a,*limits))
    for tick in (785,792):
        r=history[tick];add('actual_tick_'+str(tick),float(r['command_velocity_3']),float(r['command_acceleration_3']))
    for w,a in ((0,0),(.0625,0),(-.0625,0),(.062,.16),(-.0008,.2),(.0008,-.2),(.0625,.08),(-.0625,-.08),(.062500001,0),(0,1.000001)):
        add('edge_'+str(len(cases)),w,a)
    rng=random.Random(90261007)
    for i in range(48):
        w=rng.uniform(-base[0],base[0]);a=rng.uniform(-base[1],base[1]);add('random_'+str(i),w,a);add('reflection_'+str(i),-w,-a)
    for limits in ((.1,.8,10.,.01),(.004,.3,30.,.002),(.2,4.,7.,.008)):
        for w,a in ((0,0),(limits[0]*.8,limits[1]*.7),(-limits[0]*.8,-limits[1]*.7)):
            add('other_limits_'+str(len(cases)),w,a,limits)
    for limits in ((.1,1.,0.,.004),(.1,1.,1.,.0001)):
        add('invalid_'+str(len(cases)),0,0,limits)
    text='case,w,alpha,V,A,J,dt\n'+''.join(str(i)+','+','.join(map(repr,c))+'\n' for i,c in enumerate(cases))
    (OUT/'cases.csv').write_text(text);(OUT/'consumer.cpp').write_text(CPP)
    # An independent isolated consumer on the Linux target's extended precision.
    remote='/home/codextransfer/clean-audits/signed-command-cone-independent-20261007-v1'
    payload=json.dumps({'header':header.read_text(),'consumer':CPP,'cases':text})
    setup="import base64,json,pathlib,subprocess; p=pathlib.Path("+repr(remote)+"); p.mkdir(exist_ok=False); d=json.loads(base64.b64decode("+repr(base64.b64encode(payload.encode()).decode())+")); [(p/n).write_text(d[k]) for n,k in [('signed_velocity_cone.hpp','header'),('consumer.cpp','consumer'),('cases.csv','cases')]]; subprocess.run(['c++','-O2','-std=c++17','-Wall','-Wextra','-Werror',str(p/'consumer.cpp'),'-o',str(p/'consumer')],check=True); subprocess.run([str(p/'consumer'),str(p/'cases.csv')],check=True)"
    import shlex
    proc=subprocess.run(['tools/dell-ssh.sh','DellTransfer','python3 -c '+shlex.quote(setup)],capture_output=True,text=True,check=True)
    (OUT/'consumer.csv').write_text(proc.stdout);(OUT/'compiler.log').write_text(proc.stderr)
    rows=list(csv.DictReader(io.StringIO(proc.stdout)))
    intervals={int(r['id']):r for r in rows if r['kind']=='interval'}
    failures=[]; maxerr=0.; strict_jerk=0.; strict_speed=0.; row_outward=0.; corner_count=0; greedy=[]; actual=[]
    for i,c in enumerate(cases):
        if names[i].startswith('invalid'):
            assert any(r['kind']=='rejected' and int(r['id'])==i for r in rows);continue
        r=intervals[i];ref=exact_interval(c);ok=int(r['feasible'])==1
        if ok!=(ref is not None):failures.append([names[i],'feasibility mismatch'])
        if ref is not None:
            lo,hi=map(float,(r['lower'],r['upper']))
            maxerr=max(maxerr,abs(lo-float(ref[0])),abs(hi-float(ref[1])))
            # The deliberate 64eps margin reduces the interval by tiny amounts.
            for a in (lo,(lo+hi)/2,hi):
                corner_count+=1
                safe,seq,excess=recovery(c[0],a,c)
                strict_speed=max(strict_speed,excess)
                strict_jerk=max(strict_jerk,float(max(F(0),abs(F(a)-F(c[1]))-F(c[4])*F(c[5]))))
                if not safe and excess>1e-15:failures.append([names[i],'unsafe exact recovery',excess])
            if max(abs(lo-float(ref[0])),abs(hi-float(ref[1])))>5e-13:failures.append([names[i],'interval error'])
        for rr in (r for r in rows if r['kind']=='row' and int(r['id'])==i):
            k=int(rr['k']);w,_,V,A,J,dt=map(F,c)
            lower=(k-1)*w-V-J*dt*dt*k*(k-1)/2;upper=(k-1)*w+V+J*dt*dt*k*(k-1)/2
            row_outward=max(row_outward,float(max(F(0),lower-F(float(rr['lower'])),F(float(rr['upper']))-upper)))
            for a in (-float(A),0.,float(A)):
                wn=w+dt*F(a)
                # All-row condition vs independent exact clipped-jerk sequence.
                if k==1:
                    ns=math.ceil(A/(J*dt))+1
                    supports=all(-V <= w+kk*dt*F(a)+(J*dt*dt*kk*(kk-1)/2) and w+kk*dt*F(a)-(J*dt*dt*kk*(kk-1)/2)<=V for kk in range(1,ns+1))
                    if supports!=recovery(c[0],a,c)[0]:failures.append([names[i],'finite-K/sequence disagreement'])
        gg=[r for r in rows if r['kind']=='greedy' and int(r['id'])==i]
        if gg:
            prev=None
            for step in gg:
                ww,aa=float(step['w']),float(step['alpha'])
                if int(step['feasible'])!=1:failures.append([names[i],'greedy dead end'])
                if abs(ww)>c[2]+1e-15 or abs(aa)>c[3]+1e-15:failures.append([names[i],'greedy hard bound'])
                if prev and abs(aa-prev)>c[4]*c[5]+1e-15:failures.append([names[i],'greedy jerk'])
                prev=aa
            last=gg[-1];a=min(max(-float(last['w'])/c[5],float(last['lower'])),float(last['upper']));wn=float(last['w'])+c[5]*a
            if abs(wn)>1e-14 or abs(a)>1e-14:failures.append([names[i],'greedy not stopped'])
            greedy.append({'case':names[i],'steps':len(gg),'history':gg if names[i].startswith('edge_6') else []})
        if names[i].startswith('actual'):
            w,a,V,A,J,dt=map(F,c);low=max(-A,a-J*dt);high=min(A,a+J*dt)
            safe,seq,excess=recovery(c[0],float(high),c)
            actual.append({'name':names[i],'w':float(w),'alpha':float(a),'immediate_alpha_interval':[float(low),float(high)],'most_favorable_recovery_speed_excess':excess,'continuation_feasible':ok,'fastest_recovery':seq})
    for i in range(12,108,2):
        x,y=intervals[i],intervals[i+1]
        if x['feasible']!=y['feasible']:failures.append(['reflection','feasibility'])
        if int(x['feasible']) and max(abs(float(x['lower'])+float(y['upper'])),abs(float(x['upper'])+float(y['lower'])))>1e-15:failures.append(['reflection','interval'])
    report={'verdict':'PASS_ISOLATED_SIGNED_COMMAND_CONTINUATION' if not failures else 'FAIL','source_sha256':SOURCE_SHA,'inputs':inputs,'consumer_sha256':sha(OUT/'consumer.cpp'),'remote_clean_audit':remote,'long_double_runtime':proc.stderr.strip(),'cases':len(cases),'valid_cases':len(cases)-2,'interval_corners_checked':corner_count,'rows_checked':sum(r['kind']=='row' for r in rows),'max_interval_absolute_difference_exact_binary_input':maxerr,'max_exact_endpoint_speed_excess':strict_speed,'max_exact_endpoint_jerk_excess':strict_jerk,'max_QP_row_outward_roundoff':row_outward,'actual_history':actual,'greedy_valid_histories':len(greedy),'max_greedy_steps':max(g['steps'] for g in greedy),'zero_velocity_nonzero_acceleration_fixture':[g for g in greedy if g['case']=='edge_6'],'failures':failures,'scope':'Command speed, command acceleration and jerk continuation only. Not joint position, geometry, physical stopping, full MPC, or Phase5 acceptance. Floating point QP row bounds are not inward-rounded; retain SI guards and independently validate candidate continuation after solving. No production Python predictor used.'}
    assert sha(SOURCE)==SOURCE_SHA
    (OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'SOURCE_SNAPSHOT.py').write_bytes(SOURCE.read_bytes())
    print(json.dumps({k:v for k,v in report.items() if k not in ('inputs','zero_velocity_nonzero_acceleration_fixture','actual_history')},indent=2))

if __name__=='__main__':run()
