#!/usr/bin/env python3
"""Publish strict scorer/protocol and retained QA only; never execute plant."""
import datetime,hashlib,json,subprocess,tarfile
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/public-coupled-validation-91013-protocol-v2'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
freeze=json.loads((base/'frozen.json').read_text());protocol=json.loads((base/'protocol.json').read_text());assert all(sha(f)==h for f,h in freeze['files'].items())
qa=p/'results/phase5/development/public-validation-91013-gating-v2-attempt2';recorded=p/'results/phase5/development/public-validation-91013-v2-recorded-v3-attempt2'
audit=json.loads((qa/'audit.json').read_text());replay=json.loads((recorded/'report.json').read_text());assert audit['all_expected_outcomes'] and replay['gate']=='PASS_RECORDED_91012_CAPTURE_INTEGRITY_REPLAY_ONLY'
assert audit['scorer_sha256']==sha(p/'scripts/phase5/score_public_coupled_validation_91013_v2.py')==replay['scorer_sha256']
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013');run=p/'results/phase5/development/public-coupled-v2-development-validation-91013';assert not raw.exists() and not run.exists()
r=subprocess.run(['python3',str(p/'scripts/phase5/run_public_coupled_validation_91013_v2.py'),'run'],capture_output=True,text=True)
assert r.returncode!=0 and 'explicit independent root approval file required' in r.stderr and not raw.exists() and not run.exists()
(base/'approval_guard_check.json').write_text(json.dumps({'scope':'Expected no-approval refusal before path creation; no physical trial','return_code':r.returncode,'stderr':r.stderr,'no_raw_created':True,'no_run_dir_created':True},indent=2)+'\n')
fig,(ax,timeline)=plt.subplots(2,1,figsize=(10.5,6.2),gridspec_kw={'height_ratios':[3,1]},constrained_layout=True)
cases=audit['cases'];positive=[c for c in cases if c['expected_pass']];negative=[c for c in cases if not c['expected_pass']]
groups=[('Complete synthetic controls',len(positive),'#357d86'),('Retained v1 corruption classes',9,'#536f8c'),('Additional capture integrity mutations',13,'#536f8c'),('Warmup / nonfinite predictor failures',2,'#536f8c'),('Superseded candidate boundary failure',1,'#536f8c')]
for i,(label,count,color) in enumerate(groups):
 ax.barh(i,count,color=color);ax.text(count+.15,i,str(count)+' expected outcomes',va='center',fontsize=9)
ax.set_yticks(range(len(groups)),[g[0] for g in groups]);ax.invert_yaxis();ax.set_xlim(0,18);ax.set_xlabel('Executed synthetic gate cases (counts, no controller-performance measure)');ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
ax.set_title('Scorer v2: complete controls accepted; all corrupted / failed traces rejected',fontsize=12)
stages=[('Warmup',0,2,'#536f8c'),('Motion',2,.780,'#357d86'),('Recorded brake',2.780,.932,'#97794f'),('Hold',3.712,6.288,'#a9b5bf')]
for label,start,duration,color in stages:
 timeline.broken_barh([(start,duration)],(0,1),facecolors=color);timeline.text(start+duration/2,.5,label if duration>1 else label.replace(' ','\n'),ha='center',va='center',fontsize=8,color='white')
timeline.broken_barh([(10,5)],(0,1),facecolors='none',edgecolors='#a66b56',hatch='///');timeline.text(12.5,.5,'Shared stop: 1..1250 cycles\nactual outcome not yet recorded',ha='center',va='center',fontsize=8)
timeline.set_xlim(0,15);timeline.set_ylim(-.15,1.15);timeline.set_yticks([]);timeline.set_xlabel('Declared protocol time (s); seed91013 has NOT run')
fig.supxlabel('Synthetic gate evidence only. Old seed91012 recorded capture passes integrity replay; no new plant or model-accuracy result.',fontsize=9)
image=base/'phase5_public_validation_91013_protocol_v2.png';fig.savefig(image,dpi=170);plt.close(fig)
(base/'phase5_public_validation_91013_protocol_v2.json').write_text(json.dumps({'image_sha256':sha(image),'audit_sha256':sha(qa/'audit.json'),'recorded_integrity_replay_sha256':sha(recorded/'report.json'),'protocol_sha256':sha(base/'protocol.json'),'source':'scripts/phase5/publish_public_validation_protocol_91013_v2.py','units':'Synthetic case counts; declared seconds; no new physical/model performance','scope':'Development QA and unexecuted protocol only; accepted Phase4 remains intact, Phase5 pending','synthetic_positive_controls':len(positive),'synthetic_negative_controls':len(negative)},indent=2)+'\n')
review=p/'reviews/phase_5_public_validation_91013_protocol_v2_20261007.md'
review.write_text('''# Scorer v2 and replacement seed91013 protocol

PREPARED_NOT_RUN_REQUIRES_INDEPENDENT_ROOT_APPROVAL. Phase5 remains unaccepted. Original v1 scorer, runner, protocol and all nine false-PASS counterexamples remain unchanged. No seed91013 raw/run directory or run-approval file is created. The runner refuses missing approval before creating paths, binds schema2/protocol/frozen SHA to a single explicit root approval, verifies dependencies and refuses overwrites.

The source-defined mesh requires 500 warmup, 195 reference-motion, 233 reference-recorded-braking and 1572 hold cycles, followed by 1..1250 shared-stop cycles. Full CSV schema, finite values, continuous tick/substep/time and measured states, paired held commands, accepted position/velocity/acceleration/jerk histories, physical derivative consistency/guards, summary extrema, phase/cycle coverage and terminal max|w|<1e-6,max|physicalv|<1e-4 are mandatory. Terminal alpha is not required to be zero. Any warmup/window/model/regime failure prevents PASS. Warmup accuracy values are descriptive; only active windows compare the original short/long accuracy thresholds.

Every unique ordered tracking/stop attempt must have native status1, wrapperSOLVED, API error0, finite candidate size7, source policy timing/iteration/SI bounds and strict candidate/history continuation, including tracking candidates superseded by stop. The applied candidate must equal recorded w. Every attempt has continuous recorded row indices and the frozen-source 119 base rows: 7 combined bounds, 14 interleaved derivative rows, 98 signed-speed cone rows. Coefficients and bounds are checked against the accepted prior history and static URDF/MJCF limits. Finite A*x/Ax and original SI<=1e-7 are checked on every row; base bounds are finite and geometry upper+inf is legal, with finite lower and no NaN/reversed infinity.

All five consumed capture files must match execution hashes before and after scoring; all frozen model/collector/source/asset/runtime inputs are checked. An execution record and hashes bind supplied bytes, not producer authentication. Exact geometry tail-row count/per-solve options are absent, so missing final tail rows cannot be independently excluded. H/g remain source/reference-defined, not directly captured per accepted solve. No new geometry oracle or collector modification is introduced, and unlogged nonlinear guards/unknown forces are not independently certified.

Twenty-eight synthetic NoPlant gate cases are actually executed: three complete valid controls and twenty-five invalid/failure cases, including the nine original classes, malformed clocks/states/schema/history/rows/sidecars, nonfinite predictions and a single warmup forecast failure. A boundary control reaches w=V; changing only superseded tracking x to V+1e-13 remains within original row SI tolerance but fails strict continuation. Synthetic positive gates are labeled PASS_SYNTHETIC_GATE_CONTROL_ONLY and establish no plant/model accuracy. The existing seed91012 v3 data also pass inspect_capture-only: an isolated synthetic seed-mapped summary/execution adapts the gate, original five capture hashes are preserved, no predictor or plant is executed, and this is not seed91013 validation. Initial development attempts/source snapshots are retained as historical evidence.

The replacement protocol retains the same public_v2 model/constants, collector binary, seed, curated reference and 15 consumed numerical fields, original 5mm clearance, command/physical guards and solver policy. It remains a new reset of previously seen curated input, with only 1.712s motion/reference braking and a hold-end shared stop; no unseen waveform, moving-stop challenge, untouched research holdout, task success, broad excitation, 250Hz, main-MPC, uniform-domain or Phase6 claim. Full conditional 2/4/40/800ms windows are retained and overlapping windows are not independent trials. The figure depicts synthetic QA and planned time only; existing actual renders/CAD/task videos remain unchanged. Root owns independent review, source import/private Git backup and any future single-run approval.
''')
sources=['scripts/phase5/score_public_coupled_validation_91013_v2.py','scripts/phase5/audit_validation_91013_gating_v2.py','scripts/phase5/audit_validation_91013_v2_recorded_v3.py','scripts/phase5/run_public_coupled_validation_91013_v2.py','scripts/phase5/prepare_public_validation_config_91013_v2.py','scripts/phase5/publish_public_validation_protocol_91013_v2.py','config/phase5_development/public_coupled_validation_91013_v2.yaml',str(review.relative_to(p))]
items={'project/'+name:p/name for name in sources}
retained=[base,qa,recorded,p/'results/phase5/development/public-validation-91013-gating-v2-attempt1',p/'results/phase5/development/public-validation-91013-gating-v2-attempt1-source-snapshots',p/'results/phase5/development/public-validation-91013-v2-recorded-v3-attempt1']
for folder in retained:
 for file in folder.rglob('*'):
  if file.is_file():items['project/'+str(file.relative_to(p))]=file
manifest={name:{'sha256':sha(file),'bytes':file.stat().st_size} for name,file in items.items()};(base/'CHECKPOINT_FILE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
small={name:{'sha256':sha(p/name),'bytes':(p/name).stat().st_size} for name in sources}
for file in [base/'protocol.json',base/'frozen.json',base/'readiness.json',base/'approval_guard_check.json',base/'phase5_public_validation_91013_protocol_v2.png',base/'phase5_public_validation_91013_protocol_v2.json',qa/'audit.json',recorded/'report.json']:
 small[str(file.relative_to(p))]={'sha256':sha(file),'bytes':file.stat().st_size}
(base/'BACKUP_SOURCE_MANIFEST.json').write_text(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items['project/'+str((base/name).relative_to(p))]=base/name
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-validation-91013-protocol-v2-20261007');dest.mkdir(exist_ok=False);part=dest/'public-validation-91013-protocol-v2.tar.gz.part'
with tarfile.open(part,'w:gz',dereference=True) as tar:
 for name,file in sorted(items.items()):tar.add(file,arcname=name,recursive=False)
archive=dest/'public-validation-91013-protocol-v2.tar.gz';part.rename(archive)
with tarfile.open(archive) as tar:
 members=tar.getmembers();assert len(members)==len(items)
 for member in members:
  assert member.isfile() and member.name in items and not member.name.startswith('/') and '..' not in Path(member.name).parts
  data=tar.extractfile(member).read();assert hashlib.sha256(data).hexdigest()==sha(items[member.name]) and len(data)==items[member.name].stat().st_size
assert all(sha(file)==digest for file,digest in freeze['files'].items())
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'frozen_sha256':sha(base/'frozen.json'),'Dcache_inputs_verified':len(freeze['files']),'mac_copy_verified':False,'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json'),'scope':'Strict scorer QA/replacement protocol only, retained earlier attempts; no seed91013 plant/model run, no approval, Phase5 pending'}
(dest/'READY.json.part').write_text(json.dumps(ready,indent=2)+'\n');(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2),flush=True)
