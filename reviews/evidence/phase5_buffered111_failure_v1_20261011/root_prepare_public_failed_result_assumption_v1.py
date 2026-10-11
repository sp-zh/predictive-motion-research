from pathlib import Path
import json,hashlib,shutil
root=Path('/Users/uot/Documents/ChatGPT/ros');p=root/'results/phase5-reference/nonzero-128cycle-buffered-failed-v1-20261011/root-import1';v=root/'reviews/evidence/phase5_buffered111_failure_v1_20261011';code=root/'tools/phase5_nonzero_progress_session_v3';assert not v.exists() and not code.exists();v.mkdir();code.mkdir()
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();base=p/'actual-dell/session-nonzero-progress-128cycle-buffered-v1-20261011-attempt39'
files={}
for q in sorted((base/'src').iterdir()):
 assert q.is_file() and not q.is_symlink() and q.suffix in ['.hpp','.cpp'];shutil.copyfile(q,code/q.name);files[q.name]={'bytes':q.stat().st_size,'sha256':sha(q)}
(code/'SOURCE_IDENTITIES.json').write_text(json.dumps({'schema':'ROOT_EXACT_CONSUMED_SOURCE39_VIEW_V1','source':str(base/'src'),'producer_READY_sha256':sha(p/'READY.json'),'files':files,'native_entry_ELF_sha256':'4b63ef96ced141d01aa3369981dcd2aff0774fc1a51cb2a704a10726821cb82e','scope':'Exact39 copiedsource, fullactual run/pure receipts tiedbystartup/termination pins. Retainedfailurecomponent, notfulltask/stop/phase acceptance orportableCI SDKclosure.'},indent=2)+'\n')
(code/'README.md').write_text('''# Buffered evidence source39 — retained long-prefix failure\n\nExact39 C++ source files from consumed native attempt39. Fixed64KiB codec retains original IEEE/row-major bytes, precharges logical bytes and hashes only actual successful writes; normal/stdexception/golden/budgetrefusal and real RLIMIT_FSIZE partial-write tests passed. Hardkill pending buffers, nonstandard emission exceptions and internal hash failures were not generally certified here; catchall repair belongs to later40.\n\nRequested128 new independent seed91011 cycles;111 transactions complete, then fresh hint boundary-fraction refusal before native solver/B/C in cycle112. Original tolerances/cumulative1.024B Session budget remain unchanged. No fulltask/physicalstop/realtime/heldout/hardware/Phase5 acceptance. Source32/v1, allfailures/oldfreezes remain preserved.\n\nNative build uses retained Dell include/library/dependency configuration in the linked run plans, not a portable CMake/CI target. Exact source identities and the public small failure report identify the consumed program; fullraw/provenance is retained on Mac/Dell archives.\n''')
selected=['READY.json','ACTUAL39_FUNCTIONAL_FAILURE_SUMMARY.json','CAPTURE_VERIFICATION.json','COLLECTION_RECEIPT.json','RETAINED_SCOPE39.json','SCOPE.md','decoded-native/ACTUAL_DYNAMIC_SUMMARY.json','decoded-task/SUMMARY.json','decoded-fine/SUMMARY.json','producer-local/active_run_plan.json','producer-local/dev_compile_plan.json','producer-local/dev_link_plan.json','producer-local/NATIVE_ONESHOT_DISPATCH_EXIT.json','producer-local/NATIVE_ONESHOT_DISPATCH.stdout','producer-local/NATIVE_ONESHOT_DISPATCH.stderr','producer-local/PURE_TEST_DISPATCH.stdout','producer-local/PURE_TEST_DISPATCH.stderr']
selection=[]
for name in selected:
 q=p/name;assert q.is_file() and q.stat().st_size<1048576,name;d=v/'producer'/name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(q,d);selection.append({'path':name,'bytes':q.stat().st_size,'sha256':sha(q)})
for part in ['build-attempt1','link-attempt1','run-attempt1']:
 q=base/part/'BUILD_RESULT.json';d=v/'native'/part/'BUILD_RESULT.json';d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(q,d)
q=base/'profile-version1/active_input.json';d=v/'native/profile-version1/active_input.json';d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(q,d)
shutil.copyfile(p.parent/'ROOT_PACKET_VERIFICATION.json',v/'ROOT_PACKET_VERIFICATION.json')
q=p/'failure-analysis';
for name in ['FRACTION_FIXTURE39.json','FRACTION_FORENSICS40A.stdout','FRACTION_FORENSICS40A.stderr']:
 d=v/'failure-analysis'/name;d.parent.mkdir(exist_ok=True);shutil.copyfile(q/name,d)
fr=Path('/private/tmp/root_independent_current_hint_fraction_review_20261011');d=v/'fraction-review';d.mkdir()
for name in ['READY.json','REVIEW.md','RESULT.json']:shutil.copyfile(fr/name,d/name)
(v/'ROOT_PUBLIC_VIEW_SELECTION.json').write_text(json.dumps({'schema':'ROOT_ACTUAL39_EXPLICIT_SMALL_VIEW_V1','producer_files':selection,'exact_source_files':39,'full_dataset':'Full3675payload8,629,175,621B plusindependentall111 algebra will remainfullarchives; raw8.21MBfixture/largearrays/CSV/SDK/ELF/caches/credentials excludedfromGit. Public views/pinnedfigures containallcompletedprefixpointsandactualfirstfailure.'},indent=2)+'\n')
print('source',len(files),'selected',len(selected))
