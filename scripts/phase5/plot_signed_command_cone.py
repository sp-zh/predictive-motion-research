#!/usr/bin/env python3
import csv,json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/signed-command-cone-v1';raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-safe-reference-v1-validation/raw.csv');sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
rows=[r for r in csv.DictReader(raw.open()) if int(r['substep'])==2 and int(r['tick'])>=760]
dt=.004;J=20.;V=.0625;ticks=np.array([int(r['tick']) for r in rows]);w=np.array([float(r['command_velocity_3']) for r in rows]);a=np.array([float(r['command_acceleration_3']) for r in rows])
# Independent explicit future jerk recovery, selecting direction of acceleration.
excursion=np.array([dt*sum(max(abs(x)-J*dt*k,0) for k in range(1,30)) for x in a])
headroom=np.where(a>=0,V-w,V+w)-excursion
fig,axes=plt.subplots(1,2,figsize=(11,4.5),constrained_layout=True)
axes[0].plot(ticks,w,label='Recorded accepted w, joint 3');axes[0].axhline(-V,color='r',ls=':',label='Hard lower speed bound');axes[0].axvline(785,color='#333333',ls='--',label='First noncontinuable history');axes[0].set_ylabel('Command velocity (rad/s)');axes[0].legend(fontsize=8)
axes[1].plot(ticks,headroom*1000,label='Speed margin after best jerk recovery');axes[1].axhline(0,color='r',ls=':');axes[1].axvline(785,color='#333333',ls='--');axes[1].set_ylabel('Remaining speed margin (millirad/s)');axes[1].legend(fontsize=8)
for ax in axes:ax.set_xlabel('Recorded control tick (4 ms each)')
fig.suptitle('Velocity continuation fails before immediate speed bounds — retained v1 trace',fontsize=12)
image=base/'phase5_signed_velocity_continuation.png';fig.savefig(image,dpi=170);plt.close(fig)
(base/'phase5_signed_velocity_continuation.json').write_text(json.dumps({'image_sha256':sha(image),'source_raw_sha256':sha(raw),'source':'scripts/phase5/plot_signed_command_cone.py','first_noncontinuable_tick':785,'units':{'w':'rad/s','margin':'millirad/s','tick':'4 ms'},'scope':'Command speed only; no position/geometry/physical stopping certificate','model_geometry_changed':False},indent=2)+'\n');print(sha(image))
