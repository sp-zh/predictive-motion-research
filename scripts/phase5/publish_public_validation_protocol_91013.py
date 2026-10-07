#!/usr/bin/env python3
"""Publish protocol/readiness only; never invokes a plant run."""
import datetime,hashlib,json,subprocess,tarfile
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/public-coupled-validation-91013-protocol-v1';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();freeze=json.loads((base/'frozen.json').read_text());assert all(sha(f)==h for f,h in freeze['files'].items());protocol=json.loads((base/'protocol.json').read_text());raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013');run=p/'results/phase5/development/public-coupled-v2-development-validation-91013';assert not raw.exists() and not run.exists()
# Negative execution guard: no approval means refusal before creating run/raw paths.
r=subprocess.run(['python3',str(p/'scripts/phase5/run_public_coupled_validation_91013.py'),'run'],capture_output=True,text=True);assert r.returncode!=0 and 'explicit independent root approval file required' in r.stderr and not raw.exists() and not run.exists();(base/'approval_guard_check.json').write_text(json.dumps({'scope':'Expected pre-execution refusal, not a physical trial','return_code':r.returncode,'stderr':r.stderr,'no_raw_created':True,'no_run_dir_created':True},indent=2)+'\n')
fig,ax=plt.subplots(figsize=(10,3.4),constrained_layout=True);stages=[('Warmup',0.,2.,'#526f8b'),('Reference motion',2.,.780,'#427f86'),('Recorded reference braking',2.780,.932,'#907952'),('Hold (not excitation)',3.712,6.288,'#adb6be')]
for name,start,duration,color in stages:ax.broken_barh([(start,duration)],(0,1),facecolors=color);ax.text(start+duration/2,.5,name if duration>1 else name.replace(' ','\n'),ha='center',va='center',fontsize=9,color='white' if duration<5 else '#263544')
ax.axvline(10,color='#a75f53',ls='--');ax.annotate('Shared stop starts\nactual duration unknown',(10,.9),xytext=(10.15,.6),ha='left',fontsize=9);ax.set_xlim(0,11.8);ax.set_ylim(-.2,1.3);ax.set_yticks([]);ax.set_xlabel('Planned simulation time (s)');ax.set_title('Prepared seed91013 protocol — physical run has not executed',fontsize=13);fig.supxlabel('Known curated input: 1.712 s motion / reference braking; hold-end stop, not a moving-stop challenge.',fontsize=9)
image=base/'phase5_public_validation_91013_protocol.png';fig.savefig(image,dpi=170);plt.close(fig);(base/'phase5_public_validation_91013_protocol.json').write_text(json.dumps({'image_sha256':sha(image),'protocol_sha256':sha(base/'protocol.json'),'source':'scripts/phase5/publish_public_validation_protocol_91013.py','units':'Declared time seconds, not measured result','scope':'Protocol-only illustration; no new simulation/CAD geometry/task/physical/accuracy result'},indent=2)+'\n')
review=p/'reviews/phase_5_public_validation_91013_protocol_20261007.md';review.write_text('''# Prepared prospective development protocol91013

PREPARED_NOT_RUN_REQUIRES_INDEPENDENT_ROOT_APPROVAL. No physical run or new raw/evidence directory exists. A negative run-without-approval check rejects before path creation. Runner requires explicit root approval decision APPROVED_SINGLE_PROSPECTIVE_RUN,seed91013,exact prepared frozen.json SHA; any input change rejects. One-shot fresh raw/run directories refuse overwrite/rerun. Root reviews protocol before authorizing physical execution.

Reuses exact previously verified direct-w+signed-cone collector binary/source, original known accepted-reference input, public_v2 source/constants and all needed ROS/native/SDK/XML/assets/reader identities.248 inputs immutable-Dcache materialized and verified before any newrun, with explicit lineage/source hashes. New YAML keeps every15collector-consumed numerical parameter/reference unchanged; removes misleading unused legacy planner5s/50000 and scalar diagnostic-box metadata. Actual collector hardcodes4000/.05/SI1e-7/nativeSOLVED and uses eps1e-12. No plant/physics/geometry/guard/modelcalibration change, no derivative/C++predictor/mainMPC/Phase6 work. Legacy method CLI argument predictive is only a fixture compatibility label, not the main predictive controller.

Seed91013 is a new development reset/run of seen curated reference, not a new waveform or untouched final research holdout. Planned500warmup/195motion/233recorded-braking/1572hold precede shared stop at tick2500. Actual stop duration/outcome is measured, may fail; long-hold-end stop is not a moving-state challenge. Motion/reference braking is1.712s. All rows and failures retained; no hold/stop deletion or broad-excitation claim.

Original actual command/physical/nonlinear/geometry/age guards and next accepted-history continuation remain in unchanged collector. A/l/u/candidates/native/APIstatus/maxSI/timing are directly recorded, unchangedH/g remain source+reference defined per accepted solve rather than per-solve capture. Failure fullH/g snapshots remain. No API-rejected candidate reuse or position catchup/naive command clip.

Scorer is frozen before newrun: every full4ms-aligned active start forecasts2/4/40/800ms from measured startq/v once, known futureacceptedtarget sequence only. Its own q/v feed subsequent public calculations; futurephysical q/v only endpoint scores. Contact annotations only classify unsupported regime after forecast; any regime/solver/window failure preventsPASS and is retained. Warmup separate, all motion/brake/hold/sharedstop start/intersection counts and hold-only counts explicit. Max/RMSE/worsttick/joint and forceQP originalKKT/iterations/clamps/branch diagnostics recorded. Original shortq1e-6/v1e-4,longq1e-4/v1e-3 gates unchanged. Full collector/stop plus allactive modelgates are necessary, not sufficient for independentRootPhase5 acceptance. No uniform box/fulltask/250Hz/modelcontroller claim.

Unknown/applied/contact/limit/equality forces are outside public_model assumptions; original frozen fixture sources and public parameters identify the declared zero-force/contact-free setup, with actual contacts/limits and dynamicfailures explicitly audited. This does not certify future absence of unknown forces or geometry safety by model-box membership.

The inspected planned-time diagram is explicitly protocol-only and includes unknown stop-duration label. Existing actual FR3 recorded-state renders and taskvideos remain unchanged; no new CAD or motionvideo is produced before physicalrun. Small readiness packet contains source/config/freeze/input identities and review, not a result. Root owns independentprotocolreview/source/showcase/privateGit preservation and eventual single-run authorization.
''')
sources=['scripts/phase5/run_public_coupled_validation_91013.py','scripts/phase5/score_public_coupled_validation_91013.py','scripts/phase5/prepare_public_validation_config_91013.py','scripts/phase5/publish_public_validation_protocol_91013.py','config/phase5_development/public_coupled_validation_91013.yaml',str(review.relative_to(p))];items={'project/'+s:p/s for s in sources}
for f in base.rglob('*'):
 if f.is_file():items['project/'+str(f.relative_to(p))]=f
manifest={name:{'sha256':sha(f),'bytes':f.stat().st_size} for name,f in items.items()};(base/'CHECKPOINT_FILE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');small={s:manifest['project/'+s] for s in sources}
for name in ['protocol.json','frozen.json','readiness.json','approval_guard_check.json','phase5_public_validation_91013_protocol.png','phase5_public_validation_91013_protocol.json']:
 f=base/name;small[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size}
(base/'BACKUP_SOURCE_MANIFEST.json').write_text(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items['project/'+str((base/name).relative_to(p))]=base/name
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-validation-91013-protocol-20261007');dest.mkdir(exist_ok=False);part=dest/'public-validation-91013-protocol.tar.gz.part'
with tarfile.open(part,'w:gz',dereference=True) as t:
 for name,f in sorted(items.items()):t.add(f,arcname=name,recursive=False)
archive=dest/'public-validation-91013-protocol.tar.gz';part.rename(archive)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(items)
 for m in t.getmembers():assert m.isfile() and m.name in items and hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(items[m.name])
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'prepared_frozen_sha256':sha(base/'frozen.json'),'Dcache_inputs_verified':248,'mac_copy_verified':False,'source_manifest':str(base/'BACKUP_SOURCE_MANIFEST.json'),'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json'),'scope':'Protocol/readiness/source only, no physical result orRootexecutionapproval; newraw/runabsent'};(dest/'READY.json.part').write_text(json.dumps(ready,indent=2)+'\n');(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2))
