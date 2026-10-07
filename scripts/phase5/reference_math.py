#!/usr/bin/env python3
"""Root analytic reference cases for later Phase5 audits, not controller tests."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import argparse


def integrate(q, v, a, h):
    return q+h*v+h*h*a/2, v+h*a


def solve2(h00, h01, h11, rhs0, rhs1):
    det=h00*h11-h01*h01
    return ((h11*rhs0-h01*rhs1)/det, (h00*rhs1-h01*rhs0)/det)


def references():
    # .5[(q2-1)^2+v2^2+.1(a0^2+a1^2)], q0=v0=0, h0=h1=1.
    a0,a1=solve2(F('3.35'),F('1.75'),F('1.35'),F('1.5'),F('.5'))
    q1,v1=integrate(F(0),F(0),a0,F(1));q2,v2=integrate(q1,v1,a1,F(1))
    assert a0==F(115,146) and a1==F(-95,146)
    assert F('3.35')*a0+F('1.75')*a1==F('1.5')
    assert F('1.75')*a0+F('1.35')*a1==F('.5')
    # .5(q1-s1)^2-.2*s1+.05(a^2+b^2), q0=v0=s0=0,r0=.1,h=1.
    a,b=solve2(F('.35'),F('-.25'),F('.35'),F('.05'),F('.05'))
    assert a==b==F('.5')
    qs,vs=integrate(F(0),F(0),a,F(1));ss,rs=integrate(F(0),F('.1'),b,F(1))
    end,_=integrate(F('.9'),F(2),F(-4),F(1))
    peak,_=integrate(F('.9'),F(2),F(-4),F('.5'))
    assert end==F('.9') and peak==F('1.4')
    shifted_q,shifted_v=integrate(F('.1'),F('.2'),F(1),F('.004'))
    after_first_q,after_first_v=integrate(shifted_q,shifted_v,F(1),F('.036'))
    exact_q,exact_v=integrate(after_first_q,after_first_v,F(-1),F('.004'))
    average_q,average_v=integrate(shifted_q,shifted_v,F('.8'),F('.04'))
    assert average_v==exact_v and exact_q-average_q==F('.000144')
    actual_command_acc=(F('.1')+F('.004')*F('.5')-F('.15'))/F('.004')
    assert actual_command_acc==F(-12)
    return {
      'two_stage_coupling':{'objective':'.5*((q2-1)^2+v2^2+.1*(a0^2+a1^2))','h':[1.,1.],
          'H':[[3.35,1.75],[1.75,1.35]],'g':[-1.5,-.5],
          'optimal_inputs':[a0,a1],'rollout':[[0.,0.],[q1,v1],[q2,v2]]},
      'joint_progress_coupling':{'objective':'.5*(q1-s1)^2-.2*s1+.05*(a^2+b^2)',
          'initial_q_v_s_r':[0.,0.,0.,.1],'h':1.,'H':[[.35,-.25],[-.25,.35]],
          'g':[-.05,-.05],'optimal_a_b':[a,b],'next_q_v_s_r':[qs,vs,ss,rs]},
      'interior_position_violation':{'initial_q_v':[.9,2.],'a':-4.,'h':1.,
          'position_upper':1.,'endpoint_q':end,'interior_peak_time':.5,'interior_peak_q':peak},
      'fractional_shift':{'initial_q_v':[.1,.2],'old_accelerations':[1.,-1.],
          'old_intervals':[.04,.04],'elapsed':.004,'shifted_initial_q_v':[shifted_q,shifted_v],
          'old_plan_state_at_t044':[exact_q,exact_v],
          'single_average_acceleration_reintegrated_state':[average_q,average_v],
          'position_moment_difference':exact_q-average_q},
      'measured_vs_commanded_first_acceleration':{'measured_velocity':.1,'previous_accepted_velocity':.15,
          'dt':.004,'planned_acceleration':.5,'vcmd':.102,'actual_command_acceleration':actual_command_acc}}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('Refuse overwrite')
    d={'scope':'exact rational analytic references; does not validate production Phase5 or count as experiment trials',
       'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':references()}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(d,default=lambda x:float(x) if isinstance(x,F) else x,indent=2)+'\n')
    print('Five exact analytic reference cases generated; production validation pending')


if __name__=='__main__':main()
