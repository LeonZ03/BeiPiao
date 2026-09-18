[CmdletBinding()]
param([switch]$LocalOnly, [switch]$ForcePortable)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'runtime-tools.ps1')
try {
    $node = Resolve-RoomProgram 'node' -ForcePortable:$ForcePortable
    Write-Host "Node.js：$node" -ForegroundColor Green
    if (-not $LocalOnly) {
        $cloudflared = Resolve-RoomProgram 'cloudflared' -ForcePortable:$ForcePortable
        Write-Host "Cloudflare：$cloudflared" -ForegroundColor Green
    }
    Write-Host '初始化完成。双击项目根目录的 启动房间.cmd 即可。' -ForegroundColor Green
} catch {
    Write-Host "初始化未完成：$($_.Exception.Message)" -ForegroundColor Red
    Write-Host '请检查是否能访问 nodejs.org / GitHub，或自行安装 Node.js 22+ 和 cloudflared 后重试。'
    exit 1
}
