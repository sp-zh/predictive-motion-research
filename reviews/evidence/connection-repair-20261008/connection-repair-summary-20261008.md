# Dell USB4 SSH channel recovery

Scope: host/communications recovery only. No project source modification, project experiment, Windows reboot, WSL shutdown or termination of existing project processes.

Observed failure: Windows USB4 169.254.118.3:2222 portproxy was listening and IP Helper was Running/Automatic, but Ubuntu-24.04 was Stopped and the recorded keeper PID20732 no longer existed. Thus a successful TCP connection to the Windows proxy did not imply an SSH backend. The retained portproxy target172.29.211.53 was correct after startup; no dynamic-IP mismatch was found. Original Mac-only firewall constraints were correct.

Recovery: started the original Ubuntu-24.04 through WSL; its enabled codextransfer-sshd service started automatically. Recreated the original hidden wsl.exe/sleep infinity keeper using the existing Prepare.ps1 keeper logic. Keeper Windows PID27144, UTC StartTime2026-10-08T17:57:23.7428152Z, Linux sleep PID409. Exact PID/start-time identity matches. Re-running the corrected keeper restoration retained the same PID and startup time.

Incidental script correction: PowerShell7 ConvertFrom-Json parsed the ISO StartTime as System.DateTime. The original string-versus-DateTime comparison incorrectly reported a mismatch. Prepare.ps1 and the keeper-only recovery script now compare UTC ticks for both string and DateTime readers. Original Prepare.ps1 is preserved as Prepare.before-20261008.ps1. This prevents erroneous keeper re-creation; it does not prove why the old keeper exited.

Validation: WSL Running; dedicated SSH active/enabled and listening only on172.29.211.53:2222; both direct WSL and Windows USB4 proxy returned SSH-2.0-OpenSSH_9.6p1 Ubuntu-3ubuntu13.19. Dedicated account remains codextransfer, public-key authentication only, password authentication disabled, root login disabled. Firewall remains Local169.254.118.3, Remote169.254.142.85, TCP2222 on the original USB4 adapter. No portproxy, firewall or IP Helper reconfiguration was needed or performed. Dell Codex processes are present and this conversation successfully executed Windows and WSL commands; no command execution failure was observed.

Mac coordinator reported successful login using its original fixed host-key configuration and is independently validating1MiB bidirectional rsync/SHA256. Server logs show successful public-key sessions. End-to-end file-integrity outcome must be reported by that Mac check; these Dell checks alone do not substitute for it.

Old keeper exit cause: UNKNOWN. Evidence shows the old process was absent, previous dedicated service ended via systemd/SIGTERM, and WSL was stopped. These observations do not identify who/what terminated the keeper or prove an app crash, Windows reboot, power event or timeout. Windows last-boot time predates this incident. No speculative cause is asserted.

The old chat continues to perform communications recovery only. The new chat remains the sole project development writer.
