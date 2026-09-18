[CmdletBinding()]
param([int]$Port = 49273)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $root 'local-access/runtime-tools.ps1')
$node = Resolve-RoomProgram 'node'
foreach ($folder in @('room-site/dist','local-access','tests')) {
    foreach ($file in Get-ChildItem -LiteralPath (Join-Path $root $folder) -File -Recurse | Where-Object { $_.Extension -in @('.js','.mjs') }) {
        & $node --check $file.FullName
        if ($LASTEXITCODE -ne 0) { throw "JavaScript syntax failed: $($file.FullName)" }
    }
}
& $node (Join-Path $PSScriptRoot 'assets.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Asset checks failed.' }
& $node --experimental-vm-modules (Join-Path $PSScriptRoot 'viewer-lifecycle.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Viewer lifecycle checks failed.' }
& (Join-Path $PSScriptRoot 'test-start-room.ps1') -Port $Port
Write-Host 'PASS syntax, assets, viewer lifecycle and Windows launcher.' -ForegroundColor Green
