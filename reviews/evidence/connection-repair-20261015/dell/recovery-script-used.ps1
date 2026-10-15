$ErrorActionPreference = 'Stop'
if ((Get-Content -LiteralPath 'D:\CodexTransfer\manifests\setup-owner.txt') -ne 'codextransfer-usb4-v1') { throw 'Dedicated setup ownership marker missing.' }
$usb4Address = Get-NetIPAddress -IPAddress '169.254.118.3' -AddressFamily IPv4
if ((Get-NetAdapter -InterfaceIndex $usb4Address.InterfaceIndex).InterfaceDescription -notmatch 'USB4') { throw 'Expected USB4 interface missing.' }
$keeperFile = 'D:\CodexTransfer\manifests\wsl-keeper.json'
$keeperAlive = $false
if (Test-Path -LiteralPath $keeperFile) {
    $savedKeeper = Get-Content -Raw -LiteralPath $keeperFile | ConvertFrom-Json
    $oldKeeper = Get-Process -Id $savedKeeper.Id -ErrorAction SilentlyContinue
    $savedKeeperTicks = if ($savedKeeper.StartTime -is [datetime]) {
        $savedKeeper.StartTime.ToUniversalTime().Ticks
    } else {
        ([datetimeoffset]::Parse([string]$savedKeeper.StartTime)).UtcDateTime.Ticks
    }
    $keeperAlive = $oldKeeper -and ($oldKeeper.StartTime.ToUniversalTime().Ticks -eq $savedKeeperTicks)
}
if (-not $keeperAlive) {
    $keeper = Start-Process -FilePath 'C:\Windows\System32\wsl.exe' -ArgumentList @('-d','Ubuntu-24.04','-u','codextransfer','--','sleep','infinity') -WindowStyle Hidden -PassThru
    @{Id=$keeper.Id;StartTime=$keeper.StartTime.ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $keeperFile
}
Get-Content -LiteralPath $keeperFile
