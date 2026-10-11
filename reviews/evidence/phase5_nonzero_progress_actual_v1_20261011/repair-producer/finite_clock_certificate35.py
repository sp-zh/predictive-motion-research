from pathlib import Path
from fractions import Fraction as F
import json,struct,hashlib,math,resource,signal
resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));signal.alarm(40)
P=Path('/home/codextransfer/predictive_motion/results/phase5/full144-planning-margin-pure-v1-20261011-attempt35/pure-margin-cases-v1');source=Path('/home/codextransfer/predictive_motion/results/phase5/full144-ieee-terminal-pure-v1-20261011-attempt34/original-fixture-v1/original_input.bin');assert hashlib.sha256(source.read_bytes()).hexdigest()=='896943953327260fdf3c7dbc1f337b90e2d4a013bf6a8fa28c37f1d43d32139c'
f=source.open('rb')
def count():return struct.unpack('<Q',f.read(8))[0]
def mat(skip=False):
 n,m=count(),count();assert n<=20000 and m<=160 and n*m<=3000000
 if skip:f.seek(n*m*8,1);return
 return [list(struct.unpack('<'+'d'*m,f.read(m*8))) for _ in range(n)]
def vec(skip=False):
 n=count();assert n<=20000
 if skip:f.seek(n*8,1);return
 return list(struct.unpack('<'+'d'*n,f.read(n*8)))
mat(True);vec(True);mat(True);vec(True);vec(True);E=mat();rhs=vec();f.close();u=F(1,2**53);h=F(.004);sub=F(.002);Kfloat=.5*.004*.004;Kexact=F(1,2)*h*h
lattice=[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40]
def upward(v):return math.nextafter(float(v),math.inf) if v else 0.
def frac(v):return {'numerator':str(v.numerator),'denominator':str(v.denominator),'upper_float':upward(v)}
def charge(exact,observed):
 error=abs(F(observed)-exact);bound=u*abs(exact);assert error<=bound,(float(error),float(bound));return bound
all_results=[]
for name in ['zero','reduced','planning']:
 data=(P/(name+'.stdout')).read_bytes();lines=data.decode().splitlines();U=[float(x) for x in next(s for s in lines if s.startswith('U,')).split(',')[1:]];assert len(U)==160 and all(math.isfinite(x) for x in U);beta=[U[8*k+7] for k in range(20)];macro=[s.split(',') for s in lines if s.startswith('progress_point,')];refs=[s.split(',') for s in lines if s.startswith('reference_point,')];assert len(macro)==200 and len(refs)==400
 target=float(next(s for s in lines if s.startswith('target,')).split(',')[1]);ideal_s=ideal_r=F(0);S=R=0.;B_s=B_r=F(0);index=0;refindex=0;maximum_ref_S_error=maximum_ref_R_error=F(0);maximum_ref_S_bound=maximum_ref_R_bound=F(0);valid_domains=0;records=[]
 for k,n in enumerate(lattice):
  b=beta[k];bf=F(b);origin_s,origin_r=S,R;ideal_origin_s,ideal_origin_r=ideal_s,ideal_r;origin_Bs,origin_Br=B_s,B_r
  for cycle in range(n):
   for half in [1,2]:
    z=refs[refindex];refindex+=1;assert [int(v) for v in z[1:4]]==[k,cycle,half];dt,os_,or_,sh,rh=[float(v) for v in z[4:]];assert os_==origin_s and or_==origin_r
    time_a=.004*cycle;time_b=.002*half;dt_expected=time_a+time_b;assert dt==dt_expected;time_exact=h*cycle+sub*half;Bt=charge(h*cycle,time_a)+charge(sub*half,time_b)+charge(F(time_a)+F(time_b),dt);assert abs(F(dt)-time_exact)<=Bt
    prod=dt*origin_r;half_t=.5*dt;quad=half_t*dt;qb=quad*b;sum1=origin_s+prod;assert sh==sum1+qb;localBs=charge(F(dt)*F(origin_r),prod)+charge(F(1,2)*F(dt),half_t)*abs(F(dt)*bf)+charge(F(half_t)*F(dt),quad)*abs(bf)+charge(F(quad)*bf,qb)+charge(F(origin_s)+F(prod),sum1)+charge(F(sum1)+F(qb),sh)
    ideal_sh=ideal_origin_s+time_exact*ideal_origin_r+F(1,2)*time_exact*time_exact*bf;refBs=origin_Bs+abs(F(dt))*origin_Br+Bt*abs(ideal_origin_r)+F(1,2)*Bt*(abs(F(dt))+abs(time_exact))*abs(bf)+localBs
    rb=dt*b;assert rh==origin_r+rb;localBr=charge(F(dt)*bf,rb)+charge(F(origin_r)+F(rb),rh);ideal_rh=ideal_origin_r+time_exact*bf;refBr=origin_Br+Bt*abs(bf)+localBr
    es,er=abs(F(sh)-ideal_sh),abs(F(rh)-ideal_rh);assert es<=refBs and er<=refBr;maximum_ref_S_error=max(maximum_ref_S_error,es);maximum_ref_R_error=max(maximum_ref_R_error,er);maximum_ref_S_bound=max(maximum_ref_S_bound,refBs);maximum_ref_R_bound=max(maximum_ref_R_bound,refBr);valid_domains+=int(0<=sh<=1 and 0<=rh<=.2);records.append({'sample':refindex-1,'S_error':float(es),'S_bound':upward(refBs),'R_error':float(er),'R_bound':upward(refBr)})
   z=macro[index];index+=1;assert [int(v) for v in z[1:3]]==[k,cycle];s0,r0,ns,nr=[float(v) for v in z[3:]];assert s0==S and r0==R
   mulr=.004*R;mulb=Kfloat*b;sum1=S+mulr;assert ns==sum1+mulb and nr==R+.004*b
   localS=charge(h*F(R),mulr)+charge(F(Kfloat)*bf,mulb)+charge(F(S)+F(mulr),sum1)+charge(F(sum1)+F(mulb),ns);newBs=B_s+abs(h)*B_r+abs(F(Kfloat)-Kexact)*abs(bf)+localS
   mulprog=.004*b;localR=charge(h*bf,mulprog)+charge(F(R)+F(mulprog),nr);newBr=B_r+localR
   ideal_s,ideal_r=ideal_s+h*ideal_r+Kexact*bf,ideal_r+h*bf;S,R=ns,nr;B_s,B_r=newBs,newBr;assert abs(F(S)-ideal_s)<=B_s and abs(F(R)-ideal_r)<=B_r
 exact_e=sum((F(E[15][j])*F(U[j]) for j in range(160)),F(0))-F(rhs[15]);linear_mapping_residual=abs(exact_e-F(target));coefficient_clock_difference=abs(ideal_r-exact_e);total_tail_bound=linear_mapping_residual+coefficient_clock_difference+B_r;assert abs(F(R)-F(target))<=total_tail_bound
 exact_abs_terms=sum((h*n*abs(F(beta[k])) for k,n in enumerate(lattice)),F(0));gamma400=400*u/(1-400*u);gamma_bound=gamma400*exact_abs_terms;assert abs(F(R)-ideal_r)<=gamma_bound
 result={'case':name,'target':target,'terminal_r':R,'valid_reference_domains':valid_domains,'denominator':400,'macro_points':200,'all_operations_within_u_relative_bound':True,'u':'2^-53','rounding_mode_scope':'Finite concrete normal IEEE operands/outputs from compiled fno-fast-math ff-contract-off saved trial; exact rational per-operation certificates verified; not a universal bound for unseen replans','macro_r_rounding_charge_bound':frac(B_r),'macro_s_rounding_charge_bound':frac(B_s),'maximum_cell_reference_r_bound':frac(maximum_ref_R_bound),'maximum_cell_reference_s_bound':frac(maximum_ref_S_bound),'maximum_cell_reference_r_actual_error':frac(maximum_ref_R_error),'original_E0_exact_r_residual':frac(abs(exact_e)),'planning_E_exact_r_residual':frac(linear_mapping_residual),'original_E_vs_exact_clock_coefficient_difference':frac(coefficient_clock_difference),'total_terminal_r_distance_from_target_bound':frac(total_tail_bound),'gamma400_r_rounding_bound':frac(gamma_bound),'certified_terminal_r_lower':float(F(target)-total_tail_bound),'source_stdout_sha256':hashlib.sha256(data).hexdigest(),'actual_r_tail_zero':R==0,'new_Model_or_MuJoCo':0}
 (P/(name+'.ROUNDING_CERTIFICATE.json')).write_text(json.dumps(result,indent=2)+'\n');(P/(name+'.REFERENCE_ERROR_BOUNDS.json')).write_text(json.dumps(records,indent=2)+'\n');all_results.append(result);print(json.dumps({k:result[k] for k in ['case','target','terminal_r','valid_reference_domains','certified_terminal_r_lower']}))
 assert (P/(name+'.stdout')).read_bytes()==data
 if name=='planning':assert F(target)>total_tail_bound and valid_domains==400 and 0<R<=.2
(P/'FINITE_CLOCK_CERTIFICATES.json').write_text(json.dumps({'schema':'EXACT_RATIONAL_FINITE_IEEE_PROGRESS_CLOCK_CERTIFICATES_V1','cases':all_results,'scope':'source-only pure saved30 input; both immutable Model polynomial cell-reference and literal recursive clocks; exact targets do not prove actual execution/stop'},indent=2)+'\n')
