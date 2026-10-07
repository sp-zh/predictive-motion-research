from pathlib import Path
import hashlib,json,shutil,os,sys
r=Path('/home/codextransfer/predictive_motion');store=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/identity-cache');store.mkdir(parents=True,exist_ok=True)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def materialize(frozen):
 files=json.loads(frozen.read_text())['files'];missing=[];recovered=[]
 for name,h in files.items():
  dest=store/h
  if dest.exists():assert sha(dest)==h;continue
  p=Path(name);candidates=[p]
  if name.startswith(str(r)):
   relative=p.relative_to(r)
   candidates.extend(parent/'executed-source'/relative for parent in (r/'results/phase5/development').iterdir() if parent.is_dir())
  match=next((p for p in candidates if p.is_file() and sha(p)==h),None)
  if match is None:missing.append(name);continue
  part=store/(h+'.part')
  with part.open('xb') as out,match.open('rb') as inp:shutil.copyfileobj(inp,out,1024*1024);out.flush();os.fsync(out.fileno())
  assert sha(part)==h;os.rename(part,dest);recovered.append({'path':name,'recovered_from':str(match)})
 report={'frozen':str(frozen),'scope':'materialized immutable input bytes; original pre-run identity remains unchanged','inputs':len(files),'missing':missing,'newly_materialized':recovered,'content_store':str(store)}
 output=frozen.parent/'materialized-identity.json'
 if output.exists():assert json.loads(output.read_text())['missing']==missing
 else:output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'epoch':frozen.parent.name,'inputs':len(files),'missing':missing,'recovered':len(recovered)}),flush=True)
 if missing:raise RuntimeError('Input identity closure incomplete')
if __name__=='__main__':
 for frozen in sorted((r/'results/phase5/development').glob('*/frozen.json')):materialize(frozen)
