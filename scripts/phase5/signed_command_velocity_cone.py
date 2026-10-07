#!/usr/bin/env python3
"""Isolated discrete signed-command velocity continuation; no plant or geometry.

History w,alpha; candidate a; next w=w+dt*a; |a-alpha|<=J*dt.
The extremal recovery uses a,a-sign(a)*J*dt,..., clipped at zero.
For every integer K>=1 require -V <= w+K*dt*a +/-
J*dt**2*K*(K-1)/2 <= V. Acceleration bound makes the finite K
range ceil(A/(J*dt))+1 sufficient. This is the RET002 speed cone
under r=w+V,R=2V, without its progress position s constraint.
"""
import math

def _check(w,alpha,V,A,J,dt):
    if not all(math.isfinite(x) for x in (w,alpha,V,A,J,dt)) or min(V,A,J,dt)<=0:
        raise ValueError('finite positive limits and timestep required')
    if A/(J*dt)>4096:raise ValueError('continuation row budget')

def recovery_acceleration_limit(distance,J,dt):
    """Minimum across positive integer K; stationary point and neighbours."""
    if distance<0:raise ValueError('outside hard velocity bound')
    z=max(0.,math.sqrt(2*distance/J)/dt-1.)
    def value(n):return distance/(dt*(n+1))+.5*J*dt*n
    exact=min(value(math.floor(z)),value(math.ceil(z)))
    # RET002 roundoff interior margin; no enlargement of physical limits.
    return 0. if distance==0 else max(0.,exact-64*math.ulp(1.)*max(abs(exact),J*dt))

def acceleration_interval(w,alpha,V,A,J,dt):
    _check(w,alpha,V,A,J,dt)
    if abs(w)>V or abs(alpha)>A:return None
    lo=max(-A,alpha-J*dt,-recovery_acceleration_limit(w+V,J,dt))
    hi=min(A,alpha+J*dt,recovery_acceleration_limit(V-w,J,dt))
    return (lo,hi) if lo<=hi else None

def candidate_velocity_rows(w,V,A,J,dt):
    """QP rows K*w_next, bounds (K-1)*w +/- V +/- recovery.

    Original command derivatives, position, geometry and physical guards
    remain separate and required. No native solver or main MPC integration.
    """
    _check(w,0.,V,A,J,dt)
    return [(K,(K-1)*w-V-.5*J*dt*dt*K*(K-1),
                 (K-1)*w+V+.5*J*dt*dt*K*(K-1))
            for K in range(1,math.ceil(A/(J*dt))+2)]

def continuation_stop(w,alpha,V,A,J,dt):
    interval=acceleration_interval(w,alpha,V,A,J,dt)
    if interval is None:return None
    a=min(max(-w/dt,interval[0]),interval[1])
    return w+dt*a,a
