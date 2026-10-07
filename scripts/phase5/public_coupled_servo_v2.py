"""Fixed FR3 public-MJCF baseline with positive-solref friction reference contract. No MuJoCo state/stepping API; no parameter-generalized accuracy certificate."""
import numpy as np
import pinocchio as pin
from coupled_friction_box_v1 import solve_box
DT=.002

class PublicServo:
    def __init__(self,xml,constants):
        self.constants=constants;c=constants
        if pin.__version__!='4.1.0' or c['version']!='3.3.7' or (c['nq'],c['nv'],c['nu'],c['neq'])!=(7,7,7,0) or c['integrator']!=3 or c['timestep']!=DT:raise ValueError('frozen public model/clock identity')
        if c['disableflags'] or c['actuator_disablegroups'] or c['density'] or c['viscosity'] or any(c['wind']) or any(c['joint_stiffness']) or any(c['body_gravity_compensation']):raise ValueError('unsupported public force regime')
        if any(c['actuator_dyntype']) or any(c['actuator_gaintype']) or c['actuator_biastype']!=[1]*7 or any(c['actuator_trntype']):raise ValueError('unsupported instantaneous affine actuator')
        if np.asarray(c['actuator_trnid']).reshape(7,2)[:,0].tolist()!=list(range(7)):raise ValueError('joint/actuator mapping')
        self.model=pin.buildModelFromMJCF(str(xml));self.data=self.model.createData()
        if self.model.nq!=7 or self.model.nv!=7 or list(self.model.names)[1:]!=c['joint_names']:raise ValueError('public dynamics mapping')
        self.model.gravity.linear=np.array(c['gravity'])
        if not np.array_equal(self.model.armature,np.array(c['armature'])):raise ValueError('armature identity')
        gain=np.array(c['gainprm']).reshape(7,10);bias=np.array(c['biasprm']).reshape(7,10);gear=np.array(c['gear']).reshape(7,6)
        if not np.array_equal(gear[:,0],np.ones(7)) or np.any(gear[:,1:]) or np.any(gain[:,1:]) or np.any(bias[:,3:]):raise ValueError('unsupported actuator law')
        self.kp=gain[:,0];self.bias0=bias[:,0];self.biasq=bias[:,1];self.biasv=bias[:,2];self.passive=np.array(c['passive_damping']);self.D=self.passive-self.biasv
        self.eta=np.array(c['friction_bounds']);solimp=np.array(c['solimp']).reshape(7,5);solref=np.array(c['solref']).reshape(7,2)
        if not np.isfinite(solimp).all() or not np.isfinite(solref).all() or np.any(solref<=0) or np.any(self.D<0):raise ValueError('unsupported/nonfinite soft friction parameters')
        # This prototype retains the inspected compiled FR3 impedance profile.
        expected=np.tile(np.array([.9,.95,.001,.5,2.]),(7,1))
        if not np.array_equal(solimp,expected):raise ValueError('unsupported impedance profile; fixed FR3 baseline only')
        # Engine reference-safety replacement below2*h is not implemented here.
        if np.any(solref[:,0]<2*DT):raise ValueError('unsupported reference timeconst below2*physics_dt')
        self.R=np.maximum(c['minimum_value'],(1-solimp[:,0])/solimp[:,0]*np.array(c['invweight0']));self.B=2/(solimp[:,1]*solref[:,0])
        if not np.isfinite(self.R).all() or not np.isfinite(self.B).all():raise ValueError("nonfinite friction reference coefficients")
        self.ranges={k:np.array(c[k]).reshape(7,2) for k in ['control_range','actuator_force_range','joint_actuator_force_range','joint_range']}
        self.flags={k:np.array(c[k],bool) for k in ['control_limited','actuator_force_limited','joint_actuator_force_limited','joint_limited']}
    def state(self,q,v):
        if q.shape!=(7,) or v.shape!=(7,) or not np.isfinite(q).all() or not np.isfinite(v).all():raise ValueError('state dimension/nonfinite')
        limited=self.flags['joint_limited'];bounds=self.ranges['joint_range']
        if np.any(limited&((q<=bounds[:,0])|(q>=bounds[:,1]))):raise ValueError('joint-limit-free regime violated')
    def step(self,q,v,target):
        q,v,target=[np.asarray(x,float) for x in (q,v,target)];self.state(q,v)
        if target.shape!=(7,) or not np.isfinite(target).all():raise ValueError('target dimension/nonfinite')
        controls=target.copy();limits=self.ranges['control_range'];f=self.flags['control_limited'];controls[f]=np.clip(controls[f],limits[f,0],limits[f,1]);control_clips=int(np.count_nonzero(controls!=target))
        actuator=self.kp*controls+self.bias0+self.biasq*q+self.biasv*v;unclipped=actuator.copy()
        for ranges,flags in [('actuator_force_range','actuator_force_limited'),('joint_actuator_force_range','joint_actuator_force_limited')]:
            bounds=self.ranges[ranges];active=self.flags[flags];actuator[active]=np.clip(actuator[active],bounds[active,0],bounds[active,1])
        force_clips=int(np.count_nonzero(actuator!=unclipped))
        upper=np.triu(np.asarray(pin.crba(self.model,self.data,q)).copy());M=upper+np.triu(upper,1).T
        # Installed CRBA already includes armature; never add it a second time.
        rigid_bias=np.asarray(pin.nonLinearEffects(self.model,self.data,q,v)).copy();smooth=actuator-self.passive*v-rigid_bias
        W=np.linalg.solve(M,np.eye(7));H=W+np.diag(self.R);ell=W@smooth+self.B*v
        friction,info=solve_box(H,ell,self.eta)
        # Engine qDeriv contract keeps affine velocity bias even at force clamps.
        nextv=v+DT*np.linalg.solve(M+DT*np.diag(self.D),smooth+friction);nextq=q+DT*nextv;self.state(nextq,nextv)
        if not all(np.isfinite(x).all() for x in (M,W,H,ell,rigid_bias,smooth)):raise ArithmeticError('nonfinite public model arithmetic')
        return nextq,nextv,dict(info,control_clips=control_clips,force_clips=force_clips)
