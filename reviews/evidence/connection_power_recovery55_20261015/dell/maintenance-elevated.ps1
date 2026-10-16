$ErrorActionPreference = 'Stop'
Start-Transcript -Path (Join-Path $PSScriptRoot 'maintenance-elevated.log') -NoClobber
try {
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Administrator token required.' }
    if ((Get-Content -LiteralPath 'D:\CodexTransfer\manifests\setup-owner.txt') -ne 'codextransfer-usb4-v1') { throw 'Ownership marker mismatch.' }
    $address=Get-NetIPAddress -IPAddress '169.254.118.3' -AddressFamily IPv4
    $adapter=Get-NetAdapter -InterfaceIndex $address.InterfaceIndex
    if($adapter.InterfaceDescription -notmatch 'USB4' -or $adapter.Status -ne 'Up'){throw 'Original USB4 interface not connected.'}
    $rule=Get-NetFirewallRule -Name 'CodexTransfer-USB4-2222'
    $allowed=$rule|Get-NetFirewallAddressFilter
    $ports=$rule|Get-NetFirewallPortFilter
    if($allowed.LocalAddress -ne '169.254.118.3' -or $allowed.RemoteAddress -ne '169.254.142.85' -or $ports.Protocol -ne 'TCP' -or $ports.LocalPort -ne '2222'){throw 'Original firewall scope mismatch.'}
    $backend=New-Object System.Net.Sockets.TcpClient
    try {
        $pending=$backend.ConnectAsync('172.29.211.53',2222)
        if(-not $pending.Wait(5000)){throw 'Original WSL backend unavailable.'}
        $stream=$backend.GetStream();$stream.ReadTimeout=5000
        $reader=New-Object System.IO.StreamReader($stream)
        if($reader.ReadLine() -notlike 'SSH-2.0-*'){throw 'No SSH banner from confirmed WSL target.'}
    } finally {$backend.Dispose()}
    # Refresh exactly the existing mapping; leave firewall/services/other proxies alone.
    & netsh.exe interface portproxy show all
    & netsh.exe interface portproxy delete v4tov4 listenaddress=169.254.118.3 listenport=2222
    if($LASTEXITCODE -ne 0){throw 'Original proxy removal failed.'}
    & netsh.exe interface portproxy add v4tov4 listenaddress=169.254.118.3 listenport=2222 connectaddress=172.29.211.53 connectport=2222
    if($LASTEXITCODE -ne 0){throw 'Original proxy restoration failed.'}
    Get-NetTCPConnection -LocalPort 2222 -State Listen -ErrorAction Stop|Format-Table LocalAddress,LocalPort,OwningProcess
    Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;
public static class MaintenancePowerRead {
 [DllImport("powrprof.dll")]public static extern uint PowerReadACValueIndex(IntPtr r,ref Guid s,ref Guid g,ref Guid k,out uint v);
 [DllImport("powrprof.dll")]public static extern uint PowerReadDCValueIndex(IntPtr r,ref Guid s,ref Guid g,ref Guid k,out uint v);
}
'@
    $planText=(& powercfg.exe /getactivescheme|Out-String)
    $scheme=[guid]([regex]::Match($planText,'[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}').Value)
    $settings=@(
      @{Name='StandbyIdle';Group='238c9fa8-0aad-41ed-83f4-97be242c8f20';Key='29f6c1db-86da-48c5-9fdb-f2b67b1f44da'},
      @{Name='HibernateIdle';Group='238c9fa8-0aad-41ed-83f4-97be242c8f20';Key='9d7815a6-7ee4-497e-8888-515a05f02364'},
      @{Name='LidAction';Group='4f971e89-eebd-4455-a8de-9e59040e7347';Key='5ca83367-6e45-459f-a27b-476b1d01c936'},
      @{Name='UnattendedSleep';Group='238c9fa8-0aad-41ed-83f4-97be242c8f20';Key='7bc4a2f9-d8fc-4469-b07b-33eb785aaca0'}
    )
    function Read-Settings {
      foreach($setting in $settings){
        $group=[guid]$setting.Group;$key=[guid]$setting.Key;[uint32]$ac=0;[uint32]$dc=0
        if([MaintenancePowerRead]::PowerReadACValueIndex([IntPtr]::Zero,[ref]$scheme,[ref]$group,[ref]$key,[ref]$ac) -ne 0){throw 'AC setting read failed.'}
        if([MaintenancePowerRead]::PowerReadDCValueIndex([IntPtr]::Zero,[ref]$scheme,[ref]$group,[ref]$key,[ref]$dc) -ne 0){throw 'DC setting read failed.'}
        [pscustomobject]@{Name=$setting.Name;AC=$ac;DC=$dc}
      }
    }
    $before=@(Read-Settings)
    $batteryBefore=(& powercfg.exe /qh $scheme SUB_BATTERY|Out-String)
    $changed=@()
    foreach($setting in $settings){
      $old=$before|Where-Object{$_.Name -eq $setting.Name}
      if($old.AC -ne 0){
        & powercfg.exe /setacvalueindex $scheme $setting.Group $setting.Key 0
        if($LASTEXITCODE -ne 0){throw ('AC setting failed: '+$setting.Name)}
        $changed+=$setting.Name
      }
    }
    if($changed.Count){& powercfg.exe /setactive $scheme;if($LASTEXITCODE -ne 0){throw 'Apply existing plan failed.'}}
    $after=@(Read-Settings)
    $batteryAfter=(& powercfg.exe /qh $scheme SUB_BATTERY|Out-String)
    foreach($value in $after){
      $old=$before|Where-Object{$_.Name -eq $value.Name}
      if($value.AC -ne 0 -or $value.DC -ne $old.DC){throw 'AC/DC readback verification failed.'}
    }
    if($batteryBefore -ne $batteryAfter){throw 'Battery settings changed unexpectedly.'}
    [ordered]@{ActiveScheme=$scheme.ToString();Before=$before;After=$after;ChangedAC=$changed;BatterySettingsUnchanged=($batteryBefore -eq $batteryAfter);BatteryBefore=$batteryBefore;BatteryAfter=$batteryAfter}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'power-readback.json') -Encoding utf8
    & netsh.exe interface portproxy show all
    Set-Content -LiteralPath (Join-Path $PSScriptRoot 'maintenance.status') -Value 'SUCCESS'
} catch {
    Set-Content -LiteralPath (Join-Path $PSScriptRoot 'maintenance.status') -Value ('FAILED: '+$_.Exception.Message)
    Write-Error $_ -ErrorAction Continue
} finally {Stop-Transcript}
