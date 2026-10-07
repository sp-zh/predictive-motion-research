#!/usr/bin/env python3
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/causal-soft-servo-cpp-v3';r=json.loads((base/'report.json').read_text());fig,ax=plt.subplots(figsize=(10,4.8),constrained_layout=True)
labels=['Root finite-input\noverflow rejected','Scalar / cell\noverflow rejections','Horizon sensitivity\noverflow rejections','Malformed public\nentry rejections','Fixed-root\nbranches matched','Original domain /\nmesh rejections'];counts=[int(r['root_counterexample']['threw']),sum(not x.startswith('composed,') for x in r['overflow_regression_rows']),sum(x['rejected'] for x in r['horizon_overflow_rejections']),r['API_invalid_entry_checks'],len(r['branch_cases']),r['original_domain_mesh_rejections']];x=range(6);ax.bar(x,counts,color=['#b07352']*3+['#447b92']*3);ax.set_xticks(list(x),labels,fontsize=9);ax.set_ylabel('Executed checks / fixed cases');ax.set_yscale('log');ax.set_ylim(.8,150)
for i,value in enumerate(counts):ax.text(i,value*1.13,str(value),ha='center',fontsize=11)
ax.set_title('Causal model v3: nonfinite derived arithmetic is rejected\nFrozen FR3 parameters and nominal state / sensitivity results are preserved',fontsize=13);fig.supxlabel('Finite one-cycle positive control retained; no controller integration or model accuracy certificate.',fontsize=10)
image=base/'phase5_causal_servo_finite_v3.png';fig.savefig(image,dpi=170);plt.close(fig);sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();(base/'phase5_causal_servo_finite_v3.json').write_text(json.dumps({'image_sha256':sha(image),'report_sha256':sha(base/'report.json'),'source':'scripts/phase5/plot_causal_servo_finite_v3.py','units':'Counts of executed isolated checks/cases; logarithmic count axis','scope':'Component arithmetic/input regression diagnostics only; no robot performance/model accuracy/Phase5 acceptance; no geometry change'},indent=2)+'\n');print(sha(image))
