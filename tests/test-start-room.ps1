param([int]$Port = 49273, [switch]$WithTunnel, [switch]$Portable)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$localDir = Join-Path $taskRoot 'local-access'
$launcher = Join-Path $localDir 'start-room.ps1'
$tokens = $null; $parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($launcher, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw ($parseErrors | Out-String) }
$check = $ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Test-RoomMarkup'}, $true)
. ([scriptblock]::Create($check.Extent.Text))
$html = Get-Content -LiteralPath (Join-Path $taskRoot 'room-site/dist/index.html') -Raw -Encoding UTF8
if (-not (Test-RoomMarkup $html)) { throw 'New timeline homepage must be accepted.' }
if (Test-RoomMarkup '<html><main id="app"></main><script src="main.js"></script></html>') { throw 'Unrelated pages must not pass.' }
if (Test-RoomMarkup '<html>Cloudflare error 1033</html>') { throw 'Tunnel errors must not pass.' }
if (-not (Test-RoomMarkup '<!-- beipiao-room-app:v1 --><main id="a-future-layout"></main>')) { throw 'Future layouts must not affect identity.' }
$ps = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
$arguments = '-NoLogo -NoProfile -ExecutionPolicy Bypass -File "' + $launcher + '" -NoBrowser -NonInteractive -Port ' + $Port
if (-not $WithTunnel) { $arguments += ' -SkipTunnel' }
$controller = $null; $serverRecord = $null; $tunnelRecord = $null
$previousPortable = $env:BEIPIAO_PREFER_PORTABLE
if ($Portable) { $env:BEIPIAO_PREFER_PORTABLE = '1' }
$statePath = Join-Path $localDir "runtime-$Port.json"
try {
    $controller = Start-Process -FilePath $ps -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot "launcher-$Port.out.log") -RedirectStandardError (Join-Path $PSScriptRoot "launcher-$Port.err.log")
    $deadline = [DateTime]::UtcNow.AddSeconds($(if ($Portable) { 720 } elseif ($WithTunnel) { 230 } else { 25 }))
    $observed = ''
    do {
        if ($controller.HasExited) { throw "Launcher exited: $($controller.ExitCode). See tests/launcher-$Port.*.log" }
        if (Test-Path -LiteralPath $statePath) {
            try { $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $state = $null }
            if ($state -and $state.controller.id -eq $controller.Id) {
                if ($state.status -ne $observed) { Write-Output "state=$($state.status)"; $observed = $state.status }
                $serverRecord = $state.server; $tunnelRecord = $state.tunnel
                if ((-not $WithTunnel -and $state.status -eq 'local-ready') -or ($WithTunnel -and $state.status -in @('public-ready','local-only'))) { break }
            }
        }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)
    if ($state.status -notin @('local-ready','public-ready','local-only')) { throw 'Readiness timed out.' }
    $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/" -TimeoutSec 5
    if ($response.StatusCode -ne 200 -or -not (Test-RoomMarkup $response.Content)) { throw 'Live homepage failed.' }
    foreach ($asset in @('archive.js','main.js','assets/full-room/scene.json')) {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/$asset" -TimeoutSec 5
        if ($response.StatusCode -ne 200) { throw "Missing asset: $asset" }
    }
    if (-not $WithTunnel) {
        $duplicate = Start-Process -FilePath $ps -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot "launcher-$Port-duplicate.out.log") -RedirectStandardError (Join-Path $PSScriptRoot "launcher-$Port-duplicate.err.log")
        [void]$duplicate.Handle
        if (-not $duplicate.WaitForExit(10000)) { $duplicate.Kill(); throw 'Duplicate launcher did not exit.' }
        if ($duplicate.ExitCode -ne 0) { throw 'Duplicate launcher failed.' }
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/" -TimeoutSec 5
        if (-not (Test-RoomMarkup $response.Content)) { throw 'Duplicate launch interrupted the server.' }
    }
    Write-Output "PASS Windows PowerShell 5 launch, live homepage and assets. status=$($state.status)"
    if ($WithTunnel) {
        Write-Output "Public verification=$($state.publicVerification); error=$($state.publicError)"
        if ($state.status -ne 'public-ready') { throw 'Public tunnel did not pass HTTPS page verification.' }
    }
} finally {
    $env:BEIPIAO_PREFER_PORTABLE = $previousPortable
    # Simulate closing the owning PowerShell; do not call the separate stop script.
    if ($controller -and -not $controller.HasExited) { $controller.Kill(); $controller.WaitForExit() }
    foreach ($record in @($serverRecord,$tunnelRecord)) {
        if (-not $record) { continue }
        $deadline = [DateTime]::UtcNow.AddSeconds(8)
        do {
            $child = Get-Process -Id $record.id -ErrorAction SilentlyContinue
            if (-not $child -or $child.StartTime.ToUniversalTime().Ticks.ToString() -ne $record.startedTicks) { $child = $null; break }
            Start-Sleep -Milliseconds 100
        } while ([DateTime]::UtcNow -lt $deadline)
        if ($child) { throw "Child process survived controller closure: $($record.name)" }
    }
    Write-Output 'PASS controller closure stops only its server and tunnel.'
}
