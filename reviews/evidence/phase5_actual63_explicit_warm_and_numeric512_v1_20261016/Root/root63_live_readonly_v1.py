from pathlib import Path
import os, sys, json, shutil, subprocess, shlex, datetime, base64, ast
sys.path.insert(0, '/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
O = Path('/private/tmp/root63_review_v1_20261016')
O.mkdir(exist_ok=True)
os.environ['P5_DERIVED53_ROOT'] = str(O)
t = ast.parse(Path('/private/tmp/root60_live_connection_power_and_parent_v1.py').read_text())
ps = next((ast.literal_eval(n.value) for n in t.body if isinstance(n, ast.Assign) and any((isinstance(x, ast.Name) and x.id == 'ps' for x in n.targets))))
ps = ps.replace("-eq[datetime]'2026-10-16T01:29:44.8524424Z'", '.Ticks-eq639277109848524424')
a = ps.index(';IdentityMatches=')
b = ps.index('}}else', a)
ps = ps[:a] + ps[b:]
ps = ps.replace('$text=(& powercfg.exe /getactivescheme', '$volumes=@(Get-CimInstance Win32_LogicalDisk -Filter "DeviceID=\'C:\' OR DeviceID=\'D:\'"|Select-Object DeviceID,FreeSpace,Size)\n$text=(& powercfg.exe /getactivescheme').replace('AllOperationsReadOnly=$true', 'Volumes=$volumes;AllOperationsReadOnly=$true')
enc = base64.b64encode(ps.encode('utf-16le')).decode()
code = "from pathlib import Path\nimport os,json,subprocess,base64,datetime\nout={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'active':[],'writer_state':None}\nfor p in Path('/proc').iterdir():\n if not p.name.isdigit():continue\n try:\n  comm=(p/'comm').read_text().strip()\n  if comm.startswith('active_first_cy'):\n   out['active'].append({'pid':int(p.name),'comm':comm,'argv':(p/'cmdline').read_bytes().decode().split('\\0')[:-1]})\n except (FileNotFoundError,ProcessLookupError,PermissionError):continue\np=Path('/home/codextransfer/predictive_motion/PHASE5_WRITER_STATE_20261007.json')\nif p.exists():\n b=p.read_bytes();assert len(b)<1048576;out['writer_state']=json.loads(b)\nr=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',ENC],stdin=subprocess.DEVNULL,capture_output=True,timeout=20)\nassert len(r.stdout)<=1048576 and len(r.stderr)<=1048576\nout['windows']={'exit':r.returncode,'stdout_b64':base64.b64encode(r.stdout).decode(),'stderr_b64':base64.b64encode(r.stderr).decode()};print(json.dumps(out))".replace('ENC', repr(enc))
r = subprocess.run(['/Users/uot/Documents/ChatGPT/ros/tools/dell-ssh.sh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8', 'DellTransfer', 'python3 -I -S -B -c ' + shlex.quote(code)], capture_output=True, timeout=30)
assert r.returncode == 0, r.stderr.decode()
j = json.loads(r.stdout)
w = j['windows']
bounded_write(O / 'LIVE_CONNECTION_RESOURCES_RAW.json', json.dumps(j, indent=2) + '\n')
assert w['exit'] == 0, base64.b64decode(w['stderr_b64']).decode(errors='replace')
p = json.loads(base64.b64decode(w['stdout_b64']).decode('utf-8-sig'))
assert all((x['AC'] == 0 for x in p['Settings'])) and [x['DC'] for x in p['Settings']] == [3600, 2147483647, 1, 120] and (p['ACLineStatus'] == 1)
j['windows'] = p
j['Mac_free_bytes'] = shutil.disk_usage('/Users/uot/Documents/ChatGPT/ros').free
j['scope'] = 'Read-only original fixed-hostkey SSH/physical Windows volume/AC/DC/keeper/proc inventory. No settings, process or project-source writes.'
bounded_write(O / 'LIVE_CONNECTION_RESOURCES_REVIEW.json', json.dumps(j, indent=2) + '\n')
print(json.dumps(j))
