#!/usr/bin/env python3
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/signed-command-cone-cpp-v1';report=base/'report.json';r=json.loads(report.read_text());sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
fig,ax=plt.subplots(figsize=(7.5,4.3),constrained_layout=True);labels=['Acceleration interval','Chosen stop update','Candidate QP row'];values=[r['max_interval_error'],r['max_stop_error'],r['max_row_error']];ax.bar(labels,values,color=['#2c7296','#2c7296','#4a8b77']);ax.axhline(r['tolerance'],color='#b34949',ls='--',label='Frozen parity tolerance');ax.set_yscale('log');ax.set_ylim(1e-17,1e-13);ax.set_ylabel('Maximum absolute implementation difference');ax.legend(fontsize=9)
for i,v in enumerate(values):ax.text(i,v*1.3,format(v,'.2e'),ha='center',fontsize=10)
fig.suptitle('Isolated C++ speed-cone parity: 2,040 cases / 42,666 logged rows',fontsize=12);ax.set_title('Compared with frozen mathematical contract; no plant or controller integration',fontsize=9)
image=base/'phase5_signed_cone_cpp_parity.png';fig.savefig(image,dpi=170);plt.close(fig)
(base/'phase5_signed_cone_cpp_parity.json').write_text(json.dumps({'image_sha256':sha(image),'report_sha256':sha(report),'source':'scripts/phase5/plot_signed_cone_cpp_parity.py','units':'Absolute numerical differences: interval acceleration rad/s²; stop update rad/s or rad/s²; QP-row speed rad/s. Common numerical tolerance is implementation parity only.','scope':'No physical/controller performance or geometry change'},indent=2)+'\n');print(sha(image))
