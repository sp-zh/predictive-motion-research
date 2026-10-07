#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');src=p/'scripts/phase5/public_coupled_servo_v1.py';freeze=json.loads((p/'results/phase5/development/public-coupled-servo-v1-training/frozen.json').read_text());assert hashlib.sha256(src.read_bytes()).hexdigest()==freeze['files'][str(src)]
s=src.read_text().replace('Uncalibrated causal public-MJCF surrogate; no MuJoCo state or stepping API.','Fixed FR3 public-MJCF baseline with positive-solref friction reference contract. No MuJoCo state/stepping API; no parameter-generalized accuracy certificate.')
s=s.replace("if np.any(solimp[:,0]<=0) or np.any(solimp[:,0]>=1) or np.any(solref<=0) or np.any(self.D<0):raise ValueError('unsupported soft friction parameters')",'''if not np.isfinite(solimp).all() or not np.isfinite(solref).all() or np.any(solref<=0) or np.any(self.D<0):raise ValueError('unsupported/nonfinite soft friction parameters')
        # This prototype retains the inspected compiled FR3 impedance profile.
        expected=np.tile(np.array([.9,.95,.001,.5,2.]),(7,1))
        if not np.array_equal(solimp,expected):raise ValueError('unsupported impedance profile; fixed FR3 baseline only')
        # Engine reference-safety replacement below2*h is not implemented here.
        if np.any(solref[:,0]<2*DT):raise ValueError('unsupported reference timeconst below2*physics_dt')''')
s=s.replace('self.B=2*solref[:,1]/(solimp[:,1]*solref[:,0])','self.B=2/(solimp[:,1]*solref[:,0])\n        if not np.isfinite(self.R).all() or not np.isfinite(self.B).all():raise ValueError("nonfinite friction reference coefficients")')
dest=p/'scripts/phase5/public_coupled_servo_v2.py';assert not dest.exists();dest.write_text(s);assert hashlib.sha256(src.read_bytes()).hexdigest()==freeze['files'][str(src)];print('v2 source prepared, v1 source unchanged; no predictions run')
