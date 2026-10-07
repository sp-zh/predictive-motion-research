#!/usr/bin/env python3
"""Independent extremal-sequence and grid oracles; tests no real plant."""
import json,math,random,unittest
from signed_command_velocity_cone import acceleration_interval,candidate_velocity_rows,continuation_stop
V=.0625;A=1.;J=20.;dt=.004;h=J*dt

def sequence_safe(w,a):
    # Independently step max-jerk recovery to zero; no closed-form cone.
    for _ in range(100):
        w+=dt*a
        if abs(w)>V+3e-15:return False
        if a==0:return True
        a=math.copysign(max(0.,abs(a)-h),a)
    raise AssertionError('oracle did not recover')

class Contract(unittest.TestCase):
    def test_actual_failed_history(self):
        w=-.061980006326262695;a=-.51999999999999091
        self.assertIsNone(acceleration_interval(w,a,V,A,J,dt))
        for k in range(101):self.assertFalse(sequence_safe(w,a-h+2*h*k/100))
        self.assertIsNone(continuation_stop(w,a,V,A,J,dt))
    def test_one_step_feasible_but_future_dead_end(self):
        # Immediate derivative and speed guards all pass; continuation fails.
        w=.062;a=.16;next_a=.12
        self.assertLess(w+dt*next_a,V);self.assertLess(abs(next_a-a),h)
        self.assertFalse(sequence_safe(w,next_a))
        interval=acceleration_interval(w,a,V,A,J,dt)
        self.assertIsNotNone(interval);self.assertGreater(next_a,interval[1])
    def test_reflection_and_hard_boundaries(self):
        for w,a in ((0,0),(.04,.5),(-.02,.2),(V,0),(-V,0)):
            x=acceleration_interval(w,a,V,A,J,dt);y=acceleration_interval(-w,-a,V,A,J,dt)
            if x is None:self.assertIsNone(y)
            else:self.assertAlmostEqual(x[0],-y[1],14);self.assertAlmostEqual(x[1],-y[0],14)
        self.assertIsNone(acceleration_interval(V+.000001,0,V,A,J,dt))
        self.assertIsNone(acceleration_interval(0,A+.000001,V,A,J,dt))
    def test_random_interval_vs_independent_sequences(self):
        rng=random.Random(20261007)
        for _ in range(1500):
            w=rng.uniform(-V,V);alpha=rng.uniform(-A,A);interval=acceleration_interval(w,alpha,V,A,J,dt)
            # Enumerated acceleration candidates cover immediate derivative interval.
            lower=max(-A,alpha-h);upper=min(A,alpha+h)
            for i in range(33):
                a=lower+(upper-lower)*i/32;safe=sequence_safe(w,a)
                inside=interval is not None and interval[0]-1e-13<=a<=interval[1]+1e-13
                self.assertEqual(safe,inside)
            if interval:
                self.assertTrue(sequence_safe(w,interval[0]));self.assertTrue(sequence_safe(w,interval[1]))
    def test_rows_vs_independent_sequences(self):
        rng=random.Random(20261008)
        for _ in range(3000):
            w=rng.uniform(-V,V);a=rng.uniform(-A,A);wn=w+dt*a
            rows=candidate_velocity_rows(w,V,A,J,dt)
            feasible=all(lo-1e-15<=K*wn<=hi+1e-15 for K,lo,hi in rows)
            self.assertEqual(feasible,sequence_safe(w,a))
    def test_repeated_stop_continuation(self):
        rng=random.Random(20261009);count=0
        for _ in range(500):
            w=rng.uniform(-V,V);alpha=rng.uniform(-A,A)
            if acceleration_interval(w,alpha,V,A,J,dt) is None:continue
            count+=1
            for k in range(160):
                nxt=continuation_stop(w,alpha,V,A,J,dt);self.assertIsNotNone(nxt)
                wn,an=nxt;self.assertLessEqual(abs(wn),V+1e-15);self.assertLessEqual(abs(an),A);self.assertLessEqual(abs(an-alpha),h+1e-15)
                w,alpha=wn,an
                if abs(w)<1e-14 and abs(alpha)<1e-14:break
            else:self.fail('not stopped')
        self.assertGreater(count,100)

if __name__=='__main__':unittest.main(verbosity=2)
