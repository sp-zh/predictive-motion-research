#!/usr/bin/env python3
"""Plot one recorded development failure, never a performance distribution."""
import argparse,csv,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():p.error('Refuse output overwrite')
cycles=list(csv.DictReader((a.run/'cycles.csv').open()));iterations=list(csv.DictReader((a.run/'scp.csv').open()))
if not iterations:raise ValueError('No attempted predictive cycle')
summary={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in (a.run/'summary.yaml').read_text().splitlines() if ':' in line}
failure=summary.get('failure','unknown'); progress=summary.get('progress','unknown')
tick=int(iterations[0]['tick']);c=next(x for x in cycles if int(x['tick'])==tick)
primary=float(c['predictive_primary_s']); parts={k:sum(float(x[k]) for x in iterations if int(x['tick'])==tick) for k in ['linearization_s','assembly_s','qp_setup_s','qp_solve_s','validation_s']}
remainder=primary-sum(parts.values())
if remainder < -1e-8:raise ValueError('Primary boundary does not contain logged subcosts')
labels=['Linearize','Assemble','QP setup','QP solve','Validate','Other primary','Command / stop','Physics / observe / raw','Prediction diagnostics','Flush']
values=[*parts.values(),max(0,remainder),float(c['command_projection_and_stop_s']),float(c['physics_observer_raw_s']),float(c['prediction_diagnostic_and_scp_logging_s']),float(c['flush_s'])]
other=float(c['full_cycle_wall_s'])-sum(values)
if other < -1e-8:raise ValueError('Full-cycle boundary does not contain components')
labels.append('Other cycle');values.append(max(0,other))
fig,ax=plt.subplots(figsize=(9,4.8));colors=plt.cm.tab20.colors
ax.barh(range(len(labels)),[1000*v for v in values],color=colors[:len(labels)])
ax.set_yticks(range(len(labels)),labels);ax.invert_yaxis();ax.set_xlabel('Recorded wall cost (ms)')
ax.axvline(4,color='#a52323',linestyle='--',label='4 ms requested control period')
ax.set_title(f'Development attempt: {failure}, progress {progress}')
ax.text(.99,.03,f"Full cycle {1000*float(c['full_cycle_wall_s']):.2f} ms\nOne recorded cycle; no timing distribution",transform=ax.transAxes,ha='right',va='bottom',fontsize=9)
ax.legend(loc='upper right',frameon=False);ax.grid(axis='x',alpha=.2);fig.tight_layout()
a.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.output,dpi=170);plt.close(fig)
metadata={'scope':'single retained development failure, not research comparison or warm steady-state timing','tick':tick,'status':failure,'progress':progress,'full_cycle_s':float(c['full_cycle_wall_s']),'components_s':dict(zip(labels,values)),'matplotlib_version':matplotlib.__version__,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'inputs':{str(a.run/n):hashlib.sha256((a.run/n).read_bytes()).hexdigest() for n in ['cycles.csv','scp.csv','summary.yaml']}}
a.output.with_suffix('.metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
print(a.output)
