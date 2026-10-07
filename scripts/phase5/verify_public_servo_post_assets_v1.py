#!/usr/bin/env python3
import datetime,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
p=Path('/home/codextransfer/predictive_motion');base=p/'results/phase5/development/public-coupled-servo-v1-training';trainfreeze=p/'results/phase5/development/servo-identification-v1-training/frozen.json';old=json.loads(trainfreeze.read_text());sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();cache=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/identity-cache');docs=[];visited=set()
def visit(file):
 file=file.resolve()
 if file in visited:return
 visited.add(file);tree=ET.parse(file);docs.append((file,tree))
 for include in tree.findall('.//include'):visit(file.parent/include.attrib['file'])
visit(p/'experiments/generated/inspection/scene.xml');directories={}
for file,tree in docs:
 for node in tree.findall('.//compiler'):
  for key in ['assetdir','meshdir','texturedir']:
   if key in node.attrib:
    f=Path(node.attrib[key]);directories[key]=f if f.is_absolute() else file.parent/f
files=set(f for f,t in docs);refs=[]
for file,tree in docs:
 for node in tree.iter():
  if node.tag not in ['mesh','texture','hfield','skin'] or 'file' not in node.attrib:continue
  f=Path(node.attrib['file']);key='meshdir' if node.tag=='mesh' else 'texturedir' if node.tag=='texture' else 'assetdir'
  if not f.is_absolute():f=directories.get(key,directories.get('assetdir',file.parent))/f
  f=f.resolve();assert f.is_file();files.add(f);refs.append({'source_xml':str(file),'tag':node.tag,'reference':node.attrib['file'],'resolved':str(f)})
records=[];missing=[]
for file in sorted(files):
 h=sha(file);prior=old['files'].get(str(file));matches=prior==h
 if prior is None:missing.append(str(file))
 if prior is not None:assert matches and sha(cache/prior)==prior
 records.append({'path':str(file),'sha256':h,'bytes':file.stat().st_size,'original_TRAIN_freeze_sha256':prior,'same_as_original_TRAIN':matches,'immutable_D_cache_blob':str(cache/h) if matches else None})
result={'recorded_after_training_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Post-run transitive XML/mesh closure verification only; never backdated into public baseline40pre-scan freeze','original_TRAIN_freeze_sha256':sha(trainfreeze),'files':records,'references':refs,'unmatched_original_TRAIN':missing,'all_current_bytes_equal_original_TRAIN':not missing and all(x['same_as_original_TRAIN'] for x in records)}
(base/'post_run_transitive_asset_closure.json').write_text(json.dumps(result,indent=2)+'\n');assert result['all_current_bytes_equal_original_TRAIN'];print(json.dumps({'files':len(records),'asset_references':len(refs),'unmatched':missing,'closure_sha256':sha(base/'post_run_transitive_asset_closure.json')},indent=2))
