"""Independent closed-form command/progress oracle; no physics/plant call.

Public-coupled augmentation must compose 4ms command cycles, never treat a
40ms cell as one Euler command update. Input states preserve physical q/v
separately; this file only derives accepted C/w and progress references.
"""
import math
from fractions import Fraction

DELTA=Fraction(1,250)

def exact_command_progress(C,w,s,r,cells):
    """Rational oracle at each2ms substep for declared integer4ms cells.

    cells is a sequence of (cycles, alpha7, b). C/w and alpha7 are floats
    converted to their exact binary rationals before closed-form evaluation.
    Command has updated C_next held at both half-cycle points. Progress is
    evaluated from the cell's initial state and constant b at elapsed time.
    This oracle deliberately uses a closed-form sum, not production recurrence.
    """
    if len(C)!=7 or len(w)!=7:raise ValueError('command dimension7')
    def finite(x):
        if type(x) not in (int,float) or not math.isfinite(x):raise ValueError('finite real input')
        return Fraction(x)
    c=[finite(x) for x in C];v=[finite(x) for x in w];s0=finite(s);r0=finite(r)
    result=[];elapsed=Fraction(0)
    for cycles,alpha,b in cells:
        if type(cycles) is not int or cycles<1:raise ValueError('positive integer4ms cycles')
        if len(alpha)!=7:raise ValueError('alpha dimension7')
        a=[finite(x) for x in alpha];b=finite(b)
        for k in range(1,cycles+1):
            ck=[c[j]+k*DELTA*v[j]+DELTA*DELTA*k*(k+1)/2*a[j] for j in range(7)]
            wk=[v[j]+k*DELTA*a[j] for j in range(7)]
            for half in (1,2):
                t=(Fraction(k-1)+Fraction(half,2))*DELTA
                result.append({'elapsed_s':float(elapsed+t),'C':list(map(float,ck)),'w':list(map(float,wk)),
                               's':float(s0+t*r0+t*t*b/2),'r':float(r0+t*b)})
        t=cycles*DELTA;c=[c[j]+t*v[j]+DELTA*DELTA*cycles*(cycles+1)/2*a[j] for j in range(7)]
        v=[v[j]+t*a[j] for j in range(7)];s0=s0+t*r0+t*t*b/2;r0=r0+t*b;elapsed+=t
    return result

# Declared root cases; source remains fixed before augmented-model forecasts.
DECLARED_MESH_CYCLES=(1,10,3,2)  # 4,40,12,8ms; four independently held controls
DECLARED_ALPHA_SCALARS=(.07,-.04,.02,0.)
DECLARED_PROGRESS_ACCELERATIONS=(.03,-.01,.02,0.)
DECLARED_INITIAL_PROGRESS=(.2,.08)
DECLARED_NONPHYSICAL_COMMAND_OFFSETS=(2e-4,1e-4)  # C-q [rad], w-v [rad/s]
