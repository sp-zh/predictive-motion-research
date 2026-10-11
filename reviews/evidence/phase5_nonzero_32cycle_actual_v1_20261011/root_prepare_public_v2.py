from pathlib import Path
import json,hashlib,shutil
root=Path('/Users/uot/Documents/ChatGPT/ros');p=root/'results/phase5-reference/nonzero-32cycle-actual-v1-20261011/root-import1'
v=root/'reviews/evidence/phase5_nonzero_32cycle_actual_v1_20261011';f=root/'figures/phase5_nonzero_32cycle_actual_v1_20261011'
v.mkdir(exist_ok=True);f.mkdir(exist_ok=True)
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
selected=['READY.json','ACTUAL38_FUNCTIONAL_SUMMARY.json','CAPTURE_VERIFICATION.json','COLLECTION_RECEIPT.json','SCOPE.md','decoded-native/ACTUAL_DYNAMIC_SUMMARY.json','decoded-task/SUMMARY.json','decoded-fine/SUMMARY.json','decoded-geometry/SUMMARY.json','producer-local/RESOURCE_AND_STORAGE_PLAN.json','producer-local/active_run_plan.json','producer-local/dev_compile_plan.json','producer-local/dev_link_plan.json','producer-local/PHYSICAL_VOLUME_PRECHECK.json','producer-local/NATIVE_ONESHOT_DISPATCH_EXIT.json','producer-local/NATIVE_ONESHOT_DISPATCH.stdout','producer-local/NATIVE_ONESHOT_DISPATCH.stderr','producer-local/PURE_TEST_DISPATCH.stdout','producer-local/PURE_TEST_DISPATCH.stderr']
selection=[]
for name in selected:
 q=p/name;assert q.is_file() and q.stat().st_size<1048576,name
 d=v/'producer'/name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(q,d);selection.append({'source':name,'destination':str(d.relative_to(root)),'bytes':q.stat().st_size,'sha256':sha(q)})
for name in ['ROOT_PACKET_VERIFICATION.json','ROOT_IMPORT_FAILURES.json']:
 shutil.copyfile(p.parent/name,v/name)
shutil.copyfile('/private/tmp/NONZERO32_COMPLETE_DELL_D_MIRROR_VERIFIED.json',v/'PRODUCER_DELL_D_MIRROR_VERIFIED.json')
for name in ['actual32_diagnostic.png','actual32_tcp_prefix.png','plot.py','functional.json','task_points.json','native.json','fine.json','RENDER_RECEIPT.json']:
 q=p/'visuals'/name;shutil.copyfile(q,f/name)
# Preserve exact producer renderer. This portable copy removes only Linux resource setup,
# uses external cache and identical retained inputs; no new model or native query.
s=(f/'plot.py').read_text();s=s.replace('import os,resource,signal,json,pathlib,hashlib\nresource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));signal.alarm(40)','import os,json,pathlib,hashlib');s=s.replace("os.environ['MPLCONFIGDIR']=str(p/'mpl-local-cache')","os.environ.setdefault('MPLCONFIGDIR','/private/tmp/phase5-foundation-figure-mpl-cache-v2')")
(f/'render_portable.py').write_text(s)
qa={'schema':'ROOT_ACTUAL38_VISUAL_INSPECTION_V1','inspected':['actual32_diagnostic.png','actual32_tcp_prefix.png'],'method':'Root view_image displayed both actual producer PNGs before copying; exact bytes pinned here','findings':'Labels/units readable; 32/32 timing misses and incomplete128ms scope visible; nested timings explicitly overlap; 3D actual/reference uses first actual TCP origin, not fabricated arm motion. Final0.1267% annotation close to curve but no material data obstruction.','native_execution':False,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED'}
(f/'ROOT_VISUAL_INSPECTION.json').write_text(json.dumps(qa,indent=2)+'\n')
(f/'PROVENANCE.json').write_text(json.dumps({'schema':'ACTUAL38_PUBLIC_FIGURE_PROVENANCE_V1','seed':91011,'run':'attempt38 single consumed32','source_READY_sha256':sha(p/'READY.json'),'input_scope':'All32 committedcycles/64 actual2ms TCP poses; these plots have no successful-case filtering','encoding':'PNG160dpi; actual recorded native values. portable renderer retains exact plotting instructions except Mac-compatible resource/cache setup','files':{q.name:{'bytes':q.stat().st_size,'sha256':sha(q)} for q in sorted(f.iterdir()) if q.is_file()},'limits':'128ms development prefix, final0.1267%; no fulltask/stop/realtime/hardware/phase acceptance; inclusive nested timings must not be summed','rendered_by':'producer Matplotlib3.10.3; Root copied exact inspected PNGs'},indent=2)+'\n')
(v/'ROOT_PUBLIC_VIEW_SELECTION.json').write_text(json.dumps({'schema':'ACTUAL38_SMALL_PUBLIC_SELECTION_V1','files':selection,'omitted':'Full raw binary/geometry/value tables and complete audit/failure inputs stay in full SHA-verified archives; selected summaries and all supplied figure inputs are public. This is not a complete SDK/dependency copy.'},indent=2)+'\n')
print(json.dumps({'public_files':len(selection),'producer_READY_sha256':sha(p/'READY.json'),'figure_files':len(list(f.iterdir()))}))
