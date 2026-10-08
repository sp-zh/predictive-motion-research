$ErrorActionPreference = 'Stop'
$localAddress = '169.254.118.3'
$macAddress = '169.254.142.85'
$ruleName = 'CodexTransfer-USB4-2222'
if ((Get-Content -LiteralPath 'D:\CodexTransfer\manifests\setup-owner.txt') -ne 'codextransfer-usb4-v1') { throw 'Dedicated setup ownership marker missing.' }
$adapter = Get-NetIPAddress -IPAddress $localAddress -AddressFamily IPv4
if ((Get-NetAdapter -InterfaceIndex $adapter.InterfaceIndex).InterfaceDescription -notmatch 'USB4') { throw 'Expected USB4 interface missing.' }
$keeperFile = 'D:\CodexTransfer\manifests\wsl-keeper.json'
$keeperAlive = $false
if (Test-Path -LiteralPath $keeperFile) {
    $savedKeeper = Get-Content -Raw -LiteralPath $keeperFile | ConvertFrom-Json
    $oldKeeper = Get-Process -Id $savedKeeper.Id -ErrorAction SilentlyContinue
    $keeperAlive = $oldKeeper -and ($oldKeeper.StartTime.ToUniversalTime().ToString('o') -eq $savedKeeper.StartTime)
}
if (-not $keeperAlive) {
    $keeper = Start-Process -FilePath 'C:\Windows\System32\wsl.exe' -ArgumentList @('-d','Ubuntu-24.04','-u','codextransfer','--','sleep','infinity') -WindowStyle Hidden -PassThru
    @{Id=$keeper.Id;StartTime=$keeper.StartTime.ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $keeperFile
}
$rawAddress = & wsl.exe -d Ubuntu-24.04 -- hostname -I
if ($LASTEXITCODE -ne 0) { throw 'Cannot read WSL address.' }
$wslAddress = ($rawAddress.Trim() -split '\s+' | Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' } | Select-Object -First 1)
if (-not $wslAddress) { throw 'No WSL IPv4 address.' }
& wsl.exe -d Ubuntu-24.04 -u root -- sed -i "s/^ListenAddress .*/ListenAddress $wslAddress/" /etc/ssh/sshd_config_codextransfer
if ($LASTEXITCODE -ne 0) { throw 'Cannot update dedicated SSH listener.' }
& wsl.exe -d Ubuntu-24.04 -u root -- bash -lc 'mkdir -p /run/sshd && /usr/sbin/sshd -t -f /etc/ssh/sshd_config_codextransfer && systemctl enable codextransfer-sshd && systemctl restart codextransfer-sshd'
if ($LASTEXITCODE -ne 0) { throw 'Dedicated SSH start failed.' }
Remove-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
New-NetFirewallRule -Name $ruleName -DisplayName 'CodexTransfer USB4 Mac only' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 2222 -LocalAddress $localAddress -RemoteAddress $macAddress -InterfaceAlias $adapter.InterfaceAlias -Profile Any | Out-Null
if (-not (Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue)) { throw 'Firewall rule unavailable.' }
& netsh.exe interface portproxy delete v4tov4 listenaddress=$localAddress listenport=2222 | Out-Null
& netsh.exe interface portproxy add v4tov4 listenaddress=$localAddress listenport=2222 connectaddress=$wslAddress connectport=2222
if ($LASTEXITCODE -ne 0) { throw 'Port proxy configuration failed.' }
if (-not (Test-NetConnection -ComputerName $wslAddress -Port 2222 -InformationLevel Quiet)) { throw 'WSL SSH port is not reachable.' }
Write-Output "Prepared codextransfer@$localAddress port 2222; Mac must still verify end-to-end access."
& wsl.exe -d Ubuntu-24.04 -- cat /etc/ssh/codextransfer_host_ed25519_key.pub
& wsl.exe -d Ubuntu-24.04 -- ssh-keygen -lf /etc/ssh/codextransfer_host_ed25519_key.pub -E sha256
