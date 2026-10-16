#!/usr/bin/env python3
"""Run one pre-reviewed local command; no network, retries, or source changes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--driver', required=True)
p.add_argument('--driver-sha256', required=True)
p.add_argument('--plan', required=True)
p.add_argument('--plan-sha256', required=True)
p.add_argument('--status-directory', required=True)
p.add_argument('--wall-seconds', type=int, default=300)
p.add_argument('--output-bytes', type=int, default=2147483648)
a = p.parse_args()
assert a.wall_seconds == 3600
assert a.output_bytes == 6845104128
driver, plan = Path(a.driver), Path(a.plan)
for q, expected in [(driver, a.driver_sha256), (plan, a.plan_sha256)]:
    assert hashlib.sha256(q.read_bytes()).hexdigest() == expected, str(q)
data = json.loads(plan.read_text())
target = Path(data['output_directory'])
assert not target.exists(), 'A previous attempt must never be reused'
status = Path(a.status_directory)
status.mkdir(mode=0o700, exist_ok=False)
assert shutil.disk_usage(target.parent).free >= 10737418240
os.umask(0o077)
started = time.monotonic()
child = None
received_signal = None

metadata_charged = 0
def record(name, value):
    global metadata_charged
    encoded = (json.dumps(value, indent=2)+'\n').encode()
    assert len(encoded) <= 16777216-metadata_charged, 'auxiliary metadata prewrite cap'
    metadata_charged += len(encoded)
    tmp = status / (name + '.part')
    with tmp.open('xb') as f:
        f.write(encoded)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, status / name)

def on_signal(signum, frame):
    global received_signal
    received_signal = signum

for sig in (signal.SIGTERM, signal.SIGINT):
    signal.signal(sig, on_signal)

def descendants(pid):
    pairs = {}
    for q in Path('/proc').glob('[0-9]*/stat'):
        try:
            s = q.read_text(); fields = s[s.rfind(')') + 2:].split()
            pairs[int(q.parent.name)] = int(fields[1])
        except (OSError, ValueError, IndexError):
            pass
    result = {pid}
    changed = True
    while changed:
        old = len(result)
        result.update(k for k, parent in pairs.items() if parent in result)
        changed = len(result) != old
    return result

def stop_owned_tree():
    # Existing driver starts its native child in a separate session. Signal the
    # driver first so its own cleanup runs, retaining a snapshot for hard stop.
    owned = descendants(child.pid)
    try: child.terminate()
    except ProcessLookupError: pass
    try: child.wait(timeout=7)
    except subprocess.TimeoutExpired: pass
    owned.update(descendants(child.pid))
    for pid in owned:
        try: os.kill(pid, signal.SIGKILL)
        except ProcessLookupError: pass
    child.wait(timeout=5)

reason = None
try:
    with (status / 'driver.stdout').open('xb') as out, (status / 'driver.stderr').open('xb') as err:
        child = subprocess.Popen(['/usr/bin/python3.12', '-I', '-B', str(driver), str(plan)],
            stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True,
            env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC'})
        record('STARTED.json', {'supervisor_pid':os.getpid(), 'supervisor_sid':os.getsid(0), 'supervisor_pgid':os.getpgid(0), 'driver_pgid':os.getpgid(child.pid), 'started_utc_epoch':time.time(),
            'driver_pid':child.pid, 'driver_sha256':a.driver_sha256, 'plan_sha256':a.plan_sha256,
            'output_directory':str(target), 'maximum_wall_seconds':a.wall_seconds,
            'maximum_output_bytes':a.output_bytes, 'minimum_free_bytes':10737418240,
            'program_attempts':1, 'automatic_retries':0})
        while child.poll() is None:
            if received_signal: reason = 'SUPERVISOR_SIGNAL'
            elif time.monotonic()-started >= a.wall_seconds: reason = 'OUTER_WALL_LIMIT'
            elif shutil.disk_usage(target.parent).free < 10737418240: reason = 'FREE_SPACE_RESERVE'
            else:
                size = 0
                for base in (target, status):
                    if base.exists():
                        for q in base.rglob('*'):
                            if q.is_file() and not q.is_symlink():
                                size += q.stat().st_size
                if size > a.output_bytes: reason = 'OUTER_OUTPUT_LIMIT'
            if reason:
                stop_owned_tree()
                break
            time.sleep(2.0)
        code = child.wait(timeout=5)
        record('MANUAL_WAIT_AFTER_61.json', {'automatic_retries':0,'next_experiment_started':False,'direct_human_resume_required':True,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED','scope':'Finite offline61 ended; preserve result/necessary cleanup only. Network restoration does not resume62.'})
        record('EXIT.json', {'driver_exit_code':code, 'stop_reason':reason,
            'elapsed_wall_seconds':time.monotonic()-started, 'signal':received_signal,
            'scope':'Driver completion only; actual results require content review',
            'program_attempts':1, 'automatic_retries':0, 'remote_backup_complete':False})
        files = {}
        for q in sorted(target.rglob('*')):
            if time.monotonic()-started > a.wall_seconds+1200:
                raise TimeoutError('Final output hash inventory time cap; keep prefix')
            if q.is_file() and not q.is_symlink():
                h = hashlib.sha256()
                with q.open('rb') as f:
                    while True:
                        b = f.read(1048576)
                        if not b: break
                        h.update(b)
                files[str(q.relative_to(target))] = {'bytes':q.stat().st_size,'sha256':h.hexdigest()}
        record('READY.json', {'schema':'OFFLINE_FRESH61_BYTE_INVENTORY_V1', 'files':files, 'driver_exit_code':code, 'stop_reason':reason, 'scope':'Local output byte hashes only; no research acceptance or Git backup', 'remote_backup_complete':False})
except BaseException as e:
    if child is not None and child.poll() is None:
        stop_owned_tree()
    record('MANUAL_WAIT_AFTER_61.json', {'automatic_retries':0,'next_experiment_started':False,'direct_human_resume_required':True,'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED','scope':'61 supervision failed, preserve allbytes; do not rerun or start62 automatically.'}) if not(status/'MANUAL_WAIT_AFTER_61.json').exists() else None
    record('SUPERVISOR_FAILURE.json', {'error':type(e).__name__+': '+str(e),
        'elapsed_wall_seconds':time.monotonic()-started, 'automatic_retries':0})
    raise
