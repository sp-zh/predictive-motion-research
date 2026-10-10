# SOURCE ONLY: no function invoked by this preparation packet.
# Trusted Root staging release/hash comes through a separate explicit dispatch.
from pathlib import Path
import base64,hashlib,json,os

def install_released_profile(manifest_bytes,expected_manifest_sha256,payloads):
 assert hashlib.sha256(manifest_bytes).hexdigest()==expected_manifest_sha256
 m=json.loads(manifest_bytes)
 assert m['schema']=='FIRST_CYCLE_FUTURE_PROFILE_STAGE_MANIFEST_1'
 assert m['decision']=='RELEASED_FOR_ONE_FRESH_PROFILE_STAGE_ONLY'
 profile=Path(m['profile_directory']);assert profile.is_absolute() and not profile.exists()
 assert len(m['files'])==21 and len(m['readonly_rosters'])==3
 for row in m['files']:
  n=row['packet_relative_path'];assert n in payloads
  b=base64.b64decode(payloads[n]);assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
  target=Path(row['requested_path']);assert profile in target.parents and str(target)==row['resolved_path'] and row['mode']==0o444
 os.umask(0o077);profile.mkdir(mode=0o700)
 # FIRST files; any failure retains the created prefix. Never unlink/retry.
 for row in m['files']:
  target=Path(row['requested_path']);target.parent.mkdir(parents=True,exist_ok=True)
  b=base64.b64decode(payloads[row['packet_relative_path']])
  with target.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  target.chmod(0o444)
 for d in sorted((p for p in profile.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):d.chmod(0o555)
 profile.chmod(0o555)
 observed=[]
 for row in m['files']:
  p=Path(row['requested_path']);b=p.read_bytes();s=p.stat();value={'path':str(p),'resolved_path':str(p.resolve(strict=True)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'mode':s.st_mode&0o7777,'device':s.st_dev,'inode':s.st_ino}
  for key in ['resolved_path','bytes','sha256','mode']:assert value[key]==row[key]
  observed.append(value)
 for row in m['readonly_rosters']:
  p=Path(row['path']);assert {'path':str(p),'mode':p.stat().st_mode&0o7777,'entries':sorted(x.name for x in p.iterdir())}==row
 return {'status':'ONE_PROFILE_STAGED_REVIEW_AND_RUNTIME_STILL_REQUIRED','files':observed,'native_project_entries':0,'runtime_entries':0}
