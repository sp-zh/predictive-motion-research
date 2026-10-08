#!/usr/bin/env python3
"""Executed v2 API/gate diagnostics; synthetic output controls labeled separately."""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('/home/codextransfer/predictive_motion');REPORT=ROOT/'results/phase5/development/public-coupled-cpp-v2/parity-attempt2/report.json';OUT=ROOT/'figures/phase5'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
d=json.loads(REPORT.read_text());assert d['status']=='PASS_FIXED_RECORDED_CPP_PROTOTYPE_ONLY'
tiny=[b for b in d['boxes'] if b['name'].startswith('tiny_bound_')];native=json.loads((REPORT.parent/'cpp.json').read_text());raw={x['name']:x for x in native['box_cases']}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(13.5,5.5),constrained_layout=True);fig.get_layout_engine().set(rect=(0,.14,1,.82))
etas=[]
for b in tiny:
 point=b['tiny_precision'][0];eta=point['eta']
 if eta not in etas:etas.append(eta)
 index=etas.index(eta);ratio=point['actual']/eta
 ax[0].scatter(index,ratio,color='#007c91' if ratio<0 else '#d57918',marker='o' if ratio<0 else 's',s=70,label='ell = +1 → lower bound' if index==0 and ratio<0 else 'ell = −1 → upper bound' if index==0 and ratio>0 else None)
ax[0].axhline(-1,color='gray',linestyle='--',alpha=.4);ax[0].axhline(1,color='gray',linestyle='--',alpha=.4);ax[0].set_xticks(range(5),['10⁻¹²','10⁻¹⁰⁰','min normal\n2.23×10⁻³⁰⁸','10⁻³¹⁰','min subnormal\n4.94×10⁻³²⁴']);ax[0].set_ylim(-1.5,1.5);ax[0].set_xlabel('Declared positive friction bound η');ax[0].set_ylabel('Actual force / η');ax[0].legend(fontsize=9,loc='center');ax[0].set_title('1D analytic optimum: exact bound and side label')
counts=[8,9,20,len(d['synthetic_schema_gate']['negative_controls'])];labels=['State-input\nrejections','Box-input\nrejections','Profile-input\nrejections','Synthetic output\ngate controls'];colors=['#007c91']*3+['#a765b2'];bars=ax[1].bar(labels,counts,color=colors)
for b,c in zip(bars,counts):ax[1].text(b.get_x()+b.get_width()/2,c+.6,str(c),ha='center')
ax[1].set_ylim(0,39);ax[1].set_ylabel('Cases with expected rejection');ax[1].set_title('Native input validation / synthetic output validation');ax[1].grid(axis='y',alpha=.2)
fig.suptitle('C++ v2: tiny-bound API correction and strict output gate',fontsize=17)
fig.text(.5,.045,'All ten tiny-bound analytic cases match the exact floating bounds (0 ULP error); tiny interior and mixed/zero-bound fixtures also pass.\nPurple bar contains deliberately corrupted output controls, not actual core failures. Report-write failures remain archived. Phase 5 remains unaccepted.',ha='center',fontsize=10)
file=OUT/'phase5_public_coupled_cpp_v2_api.png';fig.savefig(file,dpi=160,bbox_inches='tight');plt.close(fig)
provenance={'scope':'DEVELOPMENT_API_AND_SCHEMA_GATE_DIAGNOSTIC_ONLY','report_sha256':sha(REPORT),'source_sha256':sha(__file__),'figure_sha256':sha(file),'units':'force/eta dimensionless; eta same force unit as ell/H','cases':'All ten predeclared 1D tiny-bound cases, no performance selection; input rejections and synthetic-output controls shown separately.','supported_serialization_observed':'Tested numeric JSON includes min normal,1e-310,min subnormal; none rejected or rounded to zero.','synthetic_controls_not_core_failures':True,'phase5':'NOT_ACCEPTED','frozen_repeat_sha256':d['source_freeze_sha256']};(OUT/'phase5_public_coupled_cpp_v2_api.json').write_text(json.dumps(provenance,indent=2)+'\n');print(file,sha(file))
