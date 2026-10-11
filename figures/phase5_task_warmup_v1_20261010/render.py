from pathlib import Path
import json,hashlib,re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import argparse
parser=argparse.ArgumentParser(description='Render retained actual bootstrap diagnostics; no acceptance inference')
parser.add_argument('packet', type=Path, help='Verified immutable task-warmup V1 packet')
P=parser.parse_args().packet;
config_path=Path(__file__).resolve().parents[2]/'config/phase5_reference.yaml'
config_bytes=config_path.read_bytes()
config_text=config_bytes.decode()
for key,expected in [('executed_acceleration_rad_s2',5.0),('executed_jerk_rad_s3',500.0)]:
 match=re.search(r'^'+key+r':\s*([0-9.]+)\s*$',config_text,re.MULTILINE)
 assert match and float(match.group(1))==expected, 'Review changed physical plot limit before rendering'

ready_bytes=(P/'READY.json').read_bytes()
assert hashlib.sha256(ready_bytes).hexdigest()=='4aaf556d9bea6112373996287004f18d442f06e616e066a78ff5f8c13f702094'
ready=json.loads(ready_bytes)
for name in ['warmup_points.json','WARMUP_AUDIT.json']:
 b=(P/name).read_bytes(); entry=ready['files'][name]; assert len(b)==entry['bytes'] and hashlib.sha256(b).hexdigest()==entry['sha256']
p=json.loads((P/'warmup_points.json').read_text());a=json.loads((P/'WARMUP_AUDIT.json').read_text());F=Path(__file__).resolve().parent;F.mkdir(exist_ok=True);t=[x['t'] for x in p]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
fig,ax=plt.subplots(2,2,figsize=(12,8),layout='constrained');colors=plt.cm.tab10.colors
for j in range(7):
 for axis,key in [(ax[0,0],'v'),(ax[0,1],'acc'),(ax[1,0],'jerk')]:axis.plot(t,[x[key][j] for x in p],color=colors[j],lw=1.4,label=f'Joint {j+1}')
ax[0,0].set(title='Actual measured joint velocity',ylabel='rad/s');ax[0,1].set(title='Actual acceleration, 2 ms differences',ylabel='rad/s²');ax[1,0].set(title='Actual jerk, first sample unavailable',ylabel='rad/s³');ax[0,1].axhline(5,color='#555555',ls='--',lw=1,label='Task physical limit ±5');ax[0,1].axhline(-5,color='#555555',ls='--',lw=1);ax[1,0].axhline(500,color='#555555',ls='--',lw=1,label='Task physical limit ±500');ax[1,0].axhline(-500,color='#555555',ls='--',lw=1)
ax[1,1].plot(t,[1000*x['minimum_true'] for x in p],label='Full true geometry',lw=2);ax[1,1].plot(t,[1000*x['minimum_cover'] for x in p],label='Cover geometry',lw=2);ax[1,1].axhline(5,color='#555555',ls='--',label='Warmup end threshold 5 mm');ax[1,1].set(title='Full scene minimum clearance',ylabel='mm')
for x in ax.flat:x.grid(alpha=.2);x.set_xlabel('Actual simulation time (s)')
ax[0,0].legend(ncol=4,fontsize=9);ax[1,1].legend(fontsize=9);ax[0,1].legend(fontsize=8);ax[1,0].legend(handles=[ax[1,0].lines[-2]],fontsize=8)
fig.suptitle('Actual FR3 task initialization and 2 s hold warmup · seed 91011',fontsize=17)
fig.supxlabel('1000 actual 2 ms steps · zero task commits · bootstrap diagnostic; Phase 5 NOT_ACCEPTED\nStartup acceleration/jerk exceed task limits and remain recorded. End hold conditions pass.',fontsize=11)
for ext in ['png','svg']:fig.savefig(F/f'actual_warmup.{ext}',dpi=170,bbox_inches='tight')
prov={'source':'actual recorded MuJoCo full scene/Coal geometry warmup','seed':91011,'playback':'static actual trace','audit':a,'files':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(F.iterdir()) if p.suffix in ['.png','.svg']},'scope':'Bootstrap diagnostic only; no task motion or candidate/controller acceptance.', 'root_marker_repair':'V1 original plot had unlabeled ±100 jerk markers; corrected to unchanged task executed jerk ±500 rad/s3 from config/phase5_reference.yaml. Original figure remains in immutable packet.', 'config_sha256':hashlib.sha256(config_bytes).hexdigest(), 'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'source_packet_ready_sha256':hashlib.sha256(ready_bytes).hexdigest()};(F/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n')
print('rendered actual warmup diagnostics')
