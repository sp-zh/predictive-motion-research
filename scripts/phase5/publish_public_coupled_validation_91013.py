#!/usr/bin/env python3
"""Archive the single recorded conditional development validation, all outcomes."""
import datetime,hashlib,json,tarfile
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/public-coupled-v2-development-validation-91013';raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/public-coupled-v2-development-validation-91013');packet=p/'results/phase5/development/public-coupled-validation-91013-protocol-v2'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
freeze=json.loads((packet/'frozen.json').read_text());execution=json.loads((base/'execution.json').read_text());report=json.loads((base/'scored/validation_report.json').read_text());cli=json.loads((base/'scorer_cli_identity.json').read_text())
assert all(sha(f)==digest for f,digest in freeze['files'].items())
assert all(sha(raw/name)==digest for name,digest in execution['raw_files'].items())
assert cli['scorer_source_sha256']==sha(p/'scripts/phase5/score_public_coupled_validation_91013_v2.py')
review=p/'reviews/phase_5_public_coupled_validation_91013_20261007.md'
metrics=report.get('metrics',[]);active=[m for m in metrics if m['scope']=='active'];warm=[m for m in metrics if m['scope']=='warmup'];audit=report.get('capture_integrity',{})
text='''# Single seed91013 conditional development validation

Phase5 remains unaccepted. One approved simulation-only run of previously seen curated accepted-reference input; not hardware, unseen waveform, untouched final holdout, task completion, main-MPC or uniform accuracy-domain acceptance. Model, collector, seed, reference, guards and all 256 prospectively frozen dependencies remain unchanged. No fitting or rerun. Root approval binds schema2/protocol/frozen SHA and previously remote-verified checkpoint 3d41fdd5b274ac7931af8f03dbc1ea95c2b19571.

'''
text+=f"Collector return code {execution['return_code']}, wall {execution['wall_s']:.9f}s; frozen scorer CLI exit {cli['exit_code']}; gate `{report['gate']}`. All raw files/stdout/stderr, execution identity, scoring reports/partials/failures and combined scorer tool output are retained. Offline scorer wall time was not directly measured and is not an online-performance result.\n\n"
if audit:
 text+=f"Full roster: {audit['cycles']} control cycles, 5002 physical 2ms substeps; 500 warmup/195 motion/233 recorded-braking/1572 hold/1 shared-stop cycles. {audit['attempts']} unique tracking/stop attempts, native/API/finite/history/original-row checks pass; one tracking candidate is superseded by stop. Original max SI={audit['actual_original_row_max_SI_violation']:.17g} <=1e-7; max command age={audit['max_command_age_s']:.9f}s<=.05. All five consumed sidecar hashes match capture. {audit['full4ms_deadline_misses']} full-cycle 4ms deadline misses: this does not establish 250Hz.\n\n"
text+='Every full 4ms-aligned window starts from measured q/v once and then uses its own predicted states with recorded future accepted targets as conditional inputs. Future actual q/v are endpoint scores only. All warmup/motion/brake/hold/shared-stop windows and crossings are retained, including the dominant hold-only stratum; overlapping windows are not independent trials. Warmup must be finite, complete and failure-free; its accuracy thresholds are descriptive. Active short/long thresholds are unchanged.\n\n'
text+='| Horizon ms | Active complete windows | Max q error rad | Max v error rad/s | RMS q | RMS v | Failed windows |\n|---|---:|---:|---:|---:|---:|---:|\n'
for m in active:text+=f"| {m['duration_s']*1000:g} | {m['completed_windows']} | {m['max_q_error_rad']:.9g} | {m['max_v_error_rad_s']:.9g} | {m['rmse_q_rad']:.9g} | {m['rmse_v_rad_s']:.9g} | {m['failed_windows']} |\n"
text+=f"\nWarmup windows: {[m['windows'] for m in warm]}; failures {sum(m['failed_windows'] for m in warm)}. Force-QP max original KKT={report.get('max_force_QP_KKT')}, max iterations={report.get('max_force_QP_iterations')}; recorded repeated prediction branches {report.get('repeated_prediction_branches')}; clamps {report.get('prediction_clamps')}. Near-roundoff agreement on this fixed-parameter trace is evidence for the scoped public baseline, not a general numerical certificate.\n\n"
text+='Minimum recorded clearance 0.015563429721572567m, maximum physical velocity 0.029926917865789479rad/s, no contacts. Terminal shared stop at tick2500/time10.004s, after long hold; source w/v thresholds satisfied. It is not a moving-state stop challenge. Actual q/v and accepted derivatives, physical derivative guards, SI/history and timing remain distinct quantities. Exact geometry tail-row count/per-solve options and accepted-solve H/g are not directly captured; source hashes/recorded rows/summary do not authenticate unlogged forces or independently reconstruct nonlinear guard checks. The full limitation list remains in the scorer report.\n\n'
text+='New plots use actual raw/report data and retain the deadline failures. The final-state image uses actual last recorded q/v/target with existing MuJoCo3.3.7 OSMesa and mj_forward only, not new dynamics/control stepping. Geometry is metres, q radians, v rad/s, plotted clearance mm/timing ms; upstream FR3 asset SHA manifest and unchanged renderer/model provenance are recorded. No complete task trajectory exists here, so no task-success video is added. Previous scalar-model/collector failures, v1 scorer false-PASS evidence and Phase4 accepted renders/videos remain intact. Root independently reviews selected model forecasts and the full capture/identity roster, then backs up source/review/figures and two verified archive copies; neither backup nor conditional gate is Phase5 acceptance.\n'
review.write_text(text)
sources=['scripts/phase5/plot_public_coupled_validation_91013.py','scripts/phase5/publish_public_coupled_validation_91013.py',str(review.relative_to(p))]
items={'project/'+name:p/name for name in sources}
for file in base.rglob('*'):
 if file.is_file():items['project/'+str(file.relative_to(p))]=file
for file in raw.rglob('*'):
 if file.is_file():items['raw/'+str(file.relative_to(raw))]=file
for file in [packet/'frozen.json',packet/'protocol.json',p/'reviews/evidence/public_validation_91013_v2_run_approval_20261007.json']:
 items['project/'+str(file.relative_to(p))]=file
manifest={name:{'sha256':sha(file),'bytes':file.stat().st_size} for name,file in items.items()};(base/'CHECKPOINT_FILE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
small={name:{'sha256':sha(p/name),'bytes':(p/name).stat().st_size} for name in sources}
for file in [base/'execution.json',base/'scorer_cli_identity.json',base/'scored/validation_report.json',base/'phase5_public_validation_91013_actual.png',base/'phase5_public_validation_91013_recorded_final_state.png',base/'phase5_public_validation_91013_visuals.json']:
 small[str(file.relative_to(p))]={'sha256':sha(file),'bytes':file.stat().st_size}
(base/'BACKUP_SOURCE_MANIFEST.json').write_text(json.dumps(small,indent=2)+'\n')
for name in ['CHECKPOINT_FILE_MANIFEST.json','BACKUP_SOURCE_MANIFEST.json']:items['project/'+str((base/name).relative_to(p))]=base/name
dest=Path('/mnt/d/CodexTransfer/projects/predictive_motion/checkpoints/public-coupled-v2-validation-91013-20261007');dest.mkdir(exist_ok=False);part=dest/'public-coupled-v2-validation-91013.tar.gz.part'
with tarfile.open(part,'w:gz',dereference=True) as tar:
 for name,file in sorted(items.items()):tar.add(file,arcname=name,recursive=False)
archive=dest/'public-coupled-v2-validation-91013.tar.gz';part.rename(archive)
with tarfile.open(archive) as tar:
 members=tar.getmembers();assert len(members)==len(items)
 for member in members:
  assert member.isfile() and not member.name.startswith('/') and '..' not in Path(member.name).parts and member.name in items
  data=tar.extractfile(member).read();assert len(data)==items[member.name].stat().st_size and hashlib.sha256(data).hexdigest()==sha(items[member.name])
assert all(sha(file)==digest for file,digest in freeze['files'].items())
ready={'archive':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'members':len(items),'archive_members_verified':True,'source_manifest_sha256':sha(base/'BACKUP_SOURCE_MANIFEST.json'),'raw_sha256':sha(raw/'raw.csv'),'frozen_sha256':sha(packet/'frozen.json'),'conditional_gate':report['gate'],'single_approved_simulation_run':True,'all_failures_retained':True,'task_success_video_created':False,'Mac_copy_verified':False,'scope':'Recorded known-curated development conditional validation only; no full task, uniform domain, controller, 250Hz or Phase5 acceptance'}
(dest/'READY.json.part').write_text(json.dumps(ready,indent=2)+'\n');(dest/'READY.json.part').rename(dest/'READY.json');print(json.dumps(ready,indent=2),flush=True)
