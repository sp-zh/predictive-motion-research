$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @'
using System;using System.Text;using System.Runtime.InteropServices;
public static class OriginalKeeperLaunch {
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)]public struct Startup {
  public uint cb; public string reserved,desktop,title;
  public uint x,y,xsize,ysize,xchars,ychars,fill,flags;public ushort show,reservedBytes;
  public IntPtr reserved2,stdin,stdout,stderr;
 }
 [StructLayout(LayoutKind.Sequential)]public struct ProcessInfo {public IntPtr process,thread;public uint pid,tid;}
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]public static extern bool CreateProcess(string app,StringBuilder command,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string cwd,ref Startup startup,out ProcessInfo info);
 [DllImport("kernel32.dll",SetLastError=true)]public static extern bool IsProcessInJob(IntPtr process,IntPtr job,out bool result);
 [DllImport("kernel32.dll")]public static extern bool CloseHandle(IntPtr handle);
}
'@
if((Get-Content -LiteralPath 'D:\CodexTransfer\manifests\setup-owner.txt') -ne 'codextransfer-usb4-v1'){throw 'Ownership marker mismatch.'}
$startup=New-Object OriginalKeeperLaunch+Startup
$startup.cb=[Runtime.InteropServices.Marshal]::SizeOf($startup)
$startup.flags=1;$startup.show=0
$info=New-Object OriginalKeeperLaunch+ProcessInfo
$command=[Text.StringBuilder]::new('"C:\Windows\System32\wsl.exe" -d Ubuntu-24.04 -u codextransfer -- sleep infinity')
# Ask Windows for its supported breakaway operation. If the job forbids it,
# preserve the existing keeper and report the OS error; no workaround is used.
$created=[OriginalKeeperLaunch]::CreateProcess('C:\Windows\System32\wsl.exe',$command,[IntPtr]::Zero,[IntPtr]::Zero,$false,0x09000000,[IntPtr]::Zero,'C:\Windows\System32',[ref]$startup,[ref]$info)
if(-not $created){
 $errorCode=[Runtime.InteropServices.Marshal]::GetLastWin32Error()
 [ordered]@{Created=$false;Win32Error=$errorCode;Message=([ComponentModel.Win32Exception]::new($errorCode)).Message;ExistingKeeperPreserved=$true;PersistentTaskOrServiceAdded=$false}|ConvertTo-Json
 exit 1
}
try {
 $inJob=$false
 $checked=[OriginalKeeperLaunch]::IsProcessInJob($info.process,[IntPtr]::Zero,[ref]$inJob)
 Start-Sleep -Milliseconds 800
 $p=Get-Process -Id $info.pid -ErrorAction Stop
 if($p.ProcessName -ne 'wsl' -or -not $checked -or $inJob){throw 'New keeper is not verified outside the executor job; existing record retained.'}
 $record=@{Id=$p.Id;StartTime=$p.StartTime.ToUniversalTime().ToString('o')}
 $record|ConvertTo-Json|Set-Content -LiteralPath 'D:\CodexTransfer\manifests\wsl-keeper.json'
 [ordered]@{Created=$true;Id=$p.Id;StartTimeUtc=$record.StartTime;IsInJob=$inJob;WindowsUser=[Security.Principal.WindowsIdentity]::GetCurrent().Name;PersistentTaskOrServiceAdded=$false;OriginalKeeperNotTerminated=$true}|ConvertTo-Json
} finally {
 [void][OriginalKeeperLaunch]::CloseHandle($info.thread)
 [void][OriginalKeeperLaunch]::CloseHandle($info.process)
}
