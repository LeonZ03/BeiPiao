[CmdletBinding()]
param([int]$Port = 49273)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
. (Join-Path $root 'local-access/runtime-tools.ps1')
$node = Resolve-RoomProgram 'node'
& $node (Join-Path $PSScriptRoot 'structure.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Room structure checks failed.' }
& $node (Join-Path $PSScriptRoot 'courtyard43-whitebox.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Courtyard43 whitebox checks failed.' }
& $node (Join-Path $PSScriptRoot 'courtyard43-interior.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Courtyard43 interior checks failed.' }
& $node (Join-Path $PSScriptRoot 'courtyard43-memory.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Courtyard43 memory revision checks failed.' }
& $node (Join-Path $PSScriptRoot 'courtyard43-desktop.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Courtyard43 desktop kit checks failed.' }
& $node (Join-Path $PSScriptRoot 'courtyard43-runtime.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Courtyard43 runtime checks failed.' }
& $node (Join-Path $PSScriptRoot 'courtyard43-exterior.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Courtyard43 winter exterior checks failed.' }
& $node (Join-Path $PSScriptRoot 'courtyard43-snow.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Courtyard43 snowfall checks failed.' }
foreach ($folder in @('room-site/dist','local-access','tests')) {
    foreach ($file in Get-ChildItem -LiteralPath (Join-Path $root $folder) -File -Recurse | Where-Object { $_.Extension -in @('.js','.mjs') }) {
        & $node --check $file.FullName
        if ($LASTEXITCODE -ne 0) { throw "JavaScript syntax failed: $($file.FullName)" }
    }
}
& $node (Join-Path $PSScriptRoot 'assets.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Asset checks failed.' }
& $node (Join-Path $PSScriptRoot 'shelf-details.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Shelf detail checks failed.' }
& $node --experimental-vm-modules (Join-Path $PSScriptRoot 'viewer-lifecycle.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Viewer lifecycle checks failed.' }
& $node --experimental-vm-modules (Join-Path $PSScriptRoot 'home-selection.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Homepage room selection checks failed.' }
& $node (Join-Path $PSScriptRoot 'room-session.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Room session checks failed.' }
& $node (Join-Path $PSScriptRoot 'breeze.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Breeze checks failed.' }
& $node (Join-Path $PSScriptRoot 'daylight-cache.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Daylight cache checks failed.' }
& $node (Join-Path $PSScriptRoot 'wardrobe.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Wardrobe interaction checks failed.' }
& $node (Join-Path $PSScriptRoot 'exterior.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Exterior checks failed.' }
& (Join-Path $PSScriptRoot 'test-start-room.ps1') -Port $Port
& $node (Join-Path $PSScriptRoot 'audio.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Audio checks failed.' }
Write-Host 'PASS syntax, assets, viewer lifecycle, breeze, daylight cache, wardrobe, exterior and Windows launcher.' -ForegroundColor Green
