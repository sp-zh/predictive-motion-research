from pathlib import Path
import hashlib, json, shutil, tarfile, sys

root = Path('/Users/uot/Documents/ChatGPT/ros')
configs = {
 'dynamic': {
  'unit':'dynamic-session-actual-v1-20261011',
  'archive':'dynamic-three-current-cycles-v1.tar.gz',
  'review':'root_independent_dynamic_actual_review_20261011',
  'receipt':'DYNAMIC_THREE_CYCLE_V1_DELL_MIRROR_VERIFIED.json',
  'public':['tools/phase5_dynamic_session_v2','reviews/evidence/phase5_dynamic_session_v1_20261011','figures/phase5_dynamic_session_v1_20261011'],
  'extras':['ROOT_PACKET_VERIFICATION.json','ROOT_VISUAL_INSPECTION.json'],
  'supplements':['dynamic-session-runtime-profile-v1-20261011','dynamic-session-source-v1-20261011','dynamic-session-source-v2-20261011'],
  'scope':'Fresh20: one Scene/Session and three reobserved, repropagated current problems; original cost/13156SI/600 strict histories/current terminal reduction and140 extra alpha guards independently verified.1200 nonlinear B values/initial Jacobian-sigma/six actual2ms steps/24 commit events andaccepted history0to3 pass; original budgets cumulative, allcycle wall misses4ms, beta0 andempty QPgeometry diagnostic. All837 producerpayloads andfull independent55 review, raw17hintfailure/18+20passes/source15-20/geometry21-22pureprep/inspectedplots included. No nonzero progress, physicalstop, fulltask,D-E,realtime,hardware orPhase5 acceptance.'},
 'inputtrust': {
  'unit':'pilot-inputtrust-native-v2-20261011',
  'archive':'pilot-inputtrust-bc-v2.tar.gz',
  'review':'root_independent_pilot_inputtrust_bc_actual_review_20261011',
  'receipt':'PILOT_INPUTTRUST_NATIVE_V2_DELL_MIRROR_VERIFIED.json',
  'public':['tools/phase5_pilot_inputtrust_v3','reviews/evidence/phase5_pilot_inputtrust_bc_v2_20261011','figures/phase5_pilot_inputtrust_bc_v2_20261011'],
  'extras':['ROOT_PACKET_VERIFICATION.json','ROOT_VISUAL_INSPECTION.json','ROOT_FIGURE_PREPARATION_FAILURES.json'],
  'supplements':['pilot-inputtrust-runtime-profile-v2-20261011'],
  'scope':'Actual fresh14 restricted beta0/140originalalpha guard domain: nativeSOLVED, original13156SI andstrict200 PASS; genuine400value/Bfull400geometry/sigma/physical checks PASS; oneprivatecurrentowner token consumes twoactual2ms sameCnext steps, acceptedhistory0to1 onlyafterboth; termination and1692 recorded pins PASS. All429producerpayloads, immutable oldguess/compile/source failures, completeindependentactualreview and inspectedproducer/Rootplots included. Numericalhint remainshint; progress0/QPgeometryrows0 means nofulltask, unrestricted optimum, physicalstop, realtime250Hz/continuoushardware or Phase5 acceptance.'},
 'bc': {
  'unit':'pilot-bc-failed-v5-20261010',
  'archive':'pilot-bc-failed-v5.tar.gz',
  'review':'root_independent_pilot_bc_failed_review_20261010',
  'receipt':'PILOT_BC_V5_DELL_MIRROR_VERIFIED.json',
  'public':['tools/phase5_pilot_bc_v5','reviews/evidence/phase5_pilot_bc_failed_v5_20261010','figures/phase5_pilot_bc_failed_v5_20261010'],
  'extras':['ROOT_IMPORT_FAILURES.json','ROOT_VISUAL_INSPECTION.json'],
  'supplements':['pilot-bc-runtime-profile-v4-20261010','pilot-bc-runtime-profile-v5-20261010','pilot-bc-ahead5-delta-review-20261010'],
  'scope':'Actual attempt12: candidate Value400 succeeded, B rejected at sample52/joint6 velocity error8.350320600854352e-5 above unchanged1e-6; geometry only first52 queried. C0/history0, termination and1692 recorded identities pass. Full independent28payloads, raw failures, exactsource24, producer and Root inspected plots; Root undispatched11 withdrawal and actual12 release included. No accepted research result/fulltask/physicalstop/continuous hardware claim.'},
 'numeric': {
  'unit':'task-start-numeric-repairs-v4-20261010',
  'archive':'task-start-numeric-provenance-v4.tar.gz',
  'review':'root_independent_task_start_numeric_repairs_review_20261010',
  'receipt':'TASK_START_NUMERIC_REPAIRS_V4_DELL_MIRROR_VERIFIED.json',
  'public':['reviews/evidence/phase5_task_start_numeric_provenance_v4_20261010'],
  'extras':[], 'supplements':[],
  'scope':'Supplemental frozen A5 actualused attempt4 and A7 final guess identities/KKT arithmetic, unused attempt3 dual mismatch and other failed numerical derivations retained. Full producer60 and independent22payloads; no new native/Model/solver execution. Original dual derivation executable still absent; no complete executable derivation closure or candidate/B/C acceptance claimed.'}
}
configs['geometry']={
 'unit':'geometry-provider-actual-v1-20261011',
 'archive':'recorded-nominal-geometry-provider-v1.tar.gz',
 'review':'root_independent_geometry_provider_actual_review_20261011',
 'receipt':'RECORDED_GEOMETRY_PROVIDER_V1_DELL_MIRROR_VERIFIED.json',
 'public':['tools/phase5_nominal_geometry_provider_v2','reviews/evidence/phase5_geometry_provider_v1_20261011','figures/phase5_geometry_provider_v1_20261011'],
 'extras':['ROOT_PACKET_VERIFICATION.json','ROOT_VISUAL_INSPECTION.json','ROOT_PUBLIC_VIEW_SELECTION.json','ROOT_FIGURE_PREPARATION_FAILURES.json'],
 'supplements':['geometry-provider-profile-v1-20261011'],
 'scope':'Fresh26 one recorded-nominal geometry diagnostic on immutable20 genuine q:1200 full9035-query snapshots/1326 Scene/11980410 primitives/4800 selected assistance rows and9 fixed FD probes; original floors/options/gates/11nonsmooth retained. Complete152 producer payloads,23 compilefailure/24-25 compileonly/26 actual graph, full independent saved-data review and inspected producer/Root plots; native SDK/cache and ELF remain pinned Dell only. No new ModelF1/MuJoCo/optimizer/control/privateowner/full-task/physical-stop/realtime/hardware/phase acceptance. Full FD aggregates are recorded native measurements, not independently replayed collision-engine outputs.'}
c=configs[sys.argv[1]]
unit=root/'results/phase5-reference'/c['unit']
store=unit/'root-archive1'; payload=store/'payload'
assert not store.exists(); payload.mkdir(parents=True)
shutil.copytree(unit/'root-import1',payload/'root-import1')
shutil.copytree(Path('/private/tmp')/c['review'],payload/'root-reviews'/c['review'])
shutil.copyfile(Path('/private/tmp')/c['receipt'],payload/c['receipt'])
for name in c['extras']: shutil.copyfile(unit/name,payload/name)
for name in c['supplements']:
 shutil.copytree(root/'results/phase5-reference'/name,payload/'root-supplements'/name)
for name in c['public']:
 shutil.copytree(root/name,payload/'source-snapshot'/name)
for name in ['docs/phase5_development_status.md','docs/showcase.md']:
 dest=payload/'source-snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(root/name,dest)
shutil.copyfile(__file__,payload/Path(__file__).name)
sha=lambda b:hashlib.sha256(b).hexdigest()
files={str(p.relative_to(payload)):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
 for p in sorted(payload.rglob('*')) if p.is_file()}
assert not any(p.is_symlink() for p in payload.rglob('*'))
mf=payload/'ARCHIVE_MANIFEST.json'
mf.write_text(json.dumps({'schema':'ROOT_UNIT_ARCHIVE_MANIFEST_V1','files':files,'scope':c['scope'],
 'native_cache_scope':'ELF/cache/dependency binaries excluded from copied packets; actual native paths and hashes retained.',
 'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED'},indent=2)+'\n')
archive=store/c['archive']
with tarfile.open(archive,'w:gz',compresslevel=6) as tf:
 for p in sorted(payload.rglob('*')):
  if p.is_file():tf.add(p,arcname=str(p.relative_to(payload)),recursive=False)
with tarfile.open(archive,'r:gz') as tf:
 members=tf.getmembers();assert len(members)==len(files)+1
 assert all(m.isfile() for m in members) and len({m.name for m in members})==len(members)
 for m in members:
  b=tf.extractfile(m).read()
  if m.name=='ARCHIVE_MANIFEST.json':assert sha(b)==sha(mf.read_bytes())
  else:assert len(b)==files[m.name]['bytes'] and sha(b)==files[m.name]['sha256'],m.name
r={'schema':'ROOT_UNIT_ARCHIVE_READY_V1','unit':c['unit'],'archive':str(archive),
 'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive.read_bytes()),
 'manifest_sha256':sha(mf.read_bytes()),'regular_members':len(files)+1,'payloads':len(files),
 'payload_bytes':sum(e['bytes'] for e in files.values()),'Mac_all_payloads_verified':True,
 'Dell_copy_verified':False,'scope':c['scope'],'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED'}
ready=store/'ARCHIVE_READY.json';ready.write_text(json.dumps(r,indent=2)+'\n')
for p in sorted(payload.rglob('*'),key=lambda p:len(p.parts),reverse=True):
 p.chmod(0o444 if p.is_file() else 0o555)
payload.chmod(0o555);archive.chmod(0o444);ready.chmod(0o444)
print(json.dumps(r))
