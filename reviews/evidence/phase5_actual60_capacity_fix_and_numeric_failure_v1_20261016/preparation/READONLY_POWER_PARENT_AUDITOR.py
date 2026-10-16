from pathlib import Path
import sys,os,json,hashlib,subprocess,shlex,base64,datetime
sys.dont_write_bytecode=True;sys.path.insert(0,'/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
O=Path('/private/tmp/root60_merged_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
ps=r'''$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;
public static class RootReadOnlyPower60 {
 [DllImport("powrprof.dll")]public static extern uint PowerReadACValueIndex(IntPtr r,ref Guid s,ref Guid g,ref Guid k,out uint v);
 [DllImport("powrprof.dll")]public static extern uint PowerReadDCValueIndex(IntPtr r,ref Guid s,ref Guid g,ref Guid k,out uint v);
 [StructLayout(LayoutKind.Sequential)]public struct PowerStatus {public byte ACLineStatus,BatteryFlag,BatteryLifePercent,SystemStatusFlag;public uint BatteryLifeTime,BatteryFullLifeTime;}
 [DllImport("kernel32.dll")]public static extern bool GetSystemPowerStatus(out PowerStatus status);
}
'@
$text=(& powercfg.exe /getactivescheme|Out-String);if($LASTEXITCODE-ne0){throw 'Active scheme read failed'}
$scheme=[guid]([regex]::Match($text,'[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}').Value)
$settings=@(
@{Name='StandbyIdle';Group='238c9fa8-0aad-41ed-83f4-97be242c8f20';Key='29f6c1db-86da-48c5-9fdb-f2b67b1f44da'},
@{Name='HibernateIdle';Group='238c9fa8-0aad-41ed-83f4-97be242c8f20';Key='9d7815a6-7ee4-497e-8888-515a05f02364'},
@{Name='LidAction';Group='4f971e89-eebd-4455-a8de-9e59040e7347';Key='5ca83367-6e45-459f-a27b-476b1d01c936'},
@{Name='UnattendedSleep';Group='238c9fa8-0aad-41ed-83f4-97be242c8f20';Key='7bc4a2f9-d8fc-4469-b07b-33eb785aaca0'})
$values=@(foreach($setting in $settings){$group=[guid]$setting.Group;$key=[guid]$setting.Key;[uint32]$ac=0;[uint32]$dc=0
$a=[RootReadOnlyPower60]::PowerReadACValueIndex([IntPtr]::Zero,[ref]$scheme,[ref]$group,[ref]$key,[ref]$ac)
$d=[RootReadOnlyPower60]::PowerReadDCValueIndex([IntPtr]::Zero,[ref]$scheme,[ref]$group,[ref]$key,[ref]$dc)
if($a-ne0-or$d-ne0){throw 'PowerRead setting query failed'}
[pscustomobject]@{Name=$setting.Name;AC=$ac;DC=$dc}})
$power=New-Object RootReadOnlyPower60+PowerStatus;if(-not[RootReadOnlyPower60]::GetSystemPowerStatus([ref]$power)){throw 'Power status read failed'}
$keeper=Get-Process -Id 29304 -ErrorAction SilentlyContinue
$k=if($keeper){[pscustomobject]@{Id=$keeper.Id;Name=$keeper.ProcessName;StartTimeUtc=$keeper.StartTime.ToUniversalTime().ToString('o');IdentityMatches=($keeper.ProcessName-eq'wsl'-and$keeper.StartTime.ToUniversalTime()-eq[datetime]'2026-10-16T01:29:44.8524424Z')}}else{$null}
$listeners=@(Get-NetTCPConnection -LocalPort 2222 -State Listen -ErrorAction Stop|Select-Object LocalAddress,LocalPort,OwningProcess)
[pscustomobject]@{Utc=[datetime]::UtcNow.ToString('o');ActiveScheme=$scheme.ToString();Settings=$values;ACLineStatus=$power.ACLineStatus;BatteryFlag=$power.BatteryFlag;BatteryLifePercent=$power.BatteryLifePercent;Keeper=$k;Listeners=$listeners;AllOperationsReadOnly=$true}|ConvertTo-Json -Depth 8 -Compress
'''
encoded=base64.b64encode(ps.encode('utf-16le')).decode()
code='''from pathlib import Path
import os,json,subprocess,base64,datetime
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'processes':[]}
for pid in [10448,10449,10447,415,589]:
 p=Path('/proc')/str(pid)
 if not p.exists():out['processes'].append({'pid':pid,'exists':False});continue
 s=(p/'stat').read_text();a=s[s.rfind(')')+2:].split();status={k:v.strip()for k,v in(line.split(':',1)for line in(p/'status').read_text().splitlines()if':'in line)}
 row={'pid':pid,'comm':(p/'comm').read_text().strip(),'state':a[0],'ppid':int(a[1]),'pgrp':int(a[2]),'session':int(a[3]),'tty_nr':int(a[4]),'starttime_ticks':int(a[19]),'SIGHUP_ignored':bool(int(status['SigIgn'],16)&1),'SIGHUP_caught':bool(int(status['SigCgt'],16)&1)}
 if pid in [10448,10449]:row['fd0_1_2']={str(n):os.readlink(p/'fd'/str(n))for n in [0,1,2]};row['argv']=(p/'cmdline').read_bytes().decode().split('\\0')[:-1]
 out['processes'].append(row)
r=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',ENCODED],stdin=subprocess.DEVNULL,capture_output=True,timeout=20)
assert len(r.stdout)<=1024**2 and len(r.stderr)<=1024**2
out['windows_query']={'exit':r.returncode,'stdout_base64':base64.b64encode(r.stdout).decode(),'stderr_base64':base64.b64encode(r.stderr).decode()}
print(json.dumps(out))'''.replace('ENCODED',repr(encoded))
r=subprocess.run(['/Users/uot/Documents/ChatGPT/ros/tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(code)],capture_output=True,timeout=30);assert r.returncode==0,r.stderr.decode();assert len(r.stdout)<=4*1024**2;j=json.loads(r.stdout)
bounded_write(O/'LIVE_POWER_PARENT_RAW_READBACK.json',json.dumps(j,indent=2)+'\n');w=j['windows_query'];assert w['exit']==0,base64.b64decode(w['stderr_base64']).decode(errors='replace');power=json.loads(base64.b64decode(w['stdout_base64']).decode('utf-8-sig'));assert power['AllOperationsReadOnly']
assert len(power['Settings'])==4 and all(x['AC']==0 for x in power['Settings'])and power['ACLineStatus']==1
assert [x['DC']for x in power['Settings']]==[3600,2147483647,1,120]and power['Keeper']['IdentityMatches']
procs={x['pid']:x for x in j['processes']};driver=procs[10448];native=procs[10449];assert driver.get('exists')is not False and native.get('exists')is not False and native['ppid']==10448 and driver['ppid']==10447 and procs[10447]['comm']=='sshd'
out=dict(schema='ROOT60_LIVE_KEEPER_POWER_AND_SSH_ATTACHED_DRIVER_0200_REVIEW_V1',utc=j['utc'],windows=power,linux_processes=j['processes'],all_AC_zero_DC_unchanged=True,keeper29304_exact_original_identity_still_matches=True,current_online_driver_still_child_of_sshd=True,SSH_detached_supervisor_proven=False,scope='Read-only live check. Existing online60 retained and left running under original limits; do not detach/relabel/restart or claim standalone offline supervisor. Native has its own process group but still uses driver pipes, so that alone does not prove SSH-independent supervision. Future distinct ready offline batch needs original reliable finite local supervisor and final manualwait; none dispatched by this check.')
bounded_write(O/'LIVE_POWER_AND_PARENT_REVIEW.json',json.dumps(out,indent=2)+'\n');print(json.dumps(dict(utc=j['utc'],AC=[x['AC']for x in power['Settings']],DC=[x['DC']for x in power['Settings']],ACLineStatus=power['ACLineStatus'],keeper=power['Keeper'],driver_parent=driver['ppid'],native_parent=native['ppid'],SSH_detached_supervisor_proven=False)))
