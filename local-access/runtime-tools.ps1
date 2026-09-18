# Shared by the double-click launcher and the optional initialization command.
$script:RoomRuntimeRoot = Join-Path (Split-Path $PSScriptRoot -Parent) '.runtime'
$script:RoomRuntimeVersions = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'runtime-versions.json') -Raw | ConvertFrom-Json

function Test-RoomExecutable([string]$Path, [string]$Kind) {
    if (-not $Path -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    try {
        $version = [string](& $Path --version 2>$null)
        if ($LASTEXITCODE -ne 0) { return $false }
        if ($Kind -eq 'node') {
            return $version -match '^v(\d+)\.' -and [int]$Matches[1] -ge $script:RoomRuntimeVersions.node.minimumMajor
        }
        return $version -match 'cloudflared version'
    } catch { return $false }
}

function Get-RoomDownload([string]$Url, [string]$Sha256, [string]$Destination) {
    # HTTPS plus a pinned digest: never execute an unverified download.
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $partial = "$Destination.$([Guid]::NewGuid().ToString('N')).download"
    $oldProgress = $ProgressPreference
    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $partial -TimeoutSec 240
        if ((Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash -ne $Sha256) {
            throw '下载文件校验不一致，已拒绝使用。请重试或从官方渠道安装。'
        }
        Move-Item -LiteralPath $partial -Destination $Destination -Force
    } finally {
        $ProgressPreference = $oldProgress
        if (Test-Path -LiteralPath $partial) { Remove-Item -LiteralPath $partial -Force }
    }
}

function Resolve-RoomProgram([ValidateSet('node','cloudflared')][string]$Kind, [switch]$ForcePortable) {
    if (-not [Environment]::Is64BitOperatingSystem) { throw '自动初始化支持 64 位 Windows。' }
    $preferPortable = $ForcePortable -or $env:BEIPIAO_PREFER_PORTABLE -eq '1'
    if (-not $preferPortable) {
        $command = Get-Command "$Kind.exe" -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        $paths = @($command.Source)
        if ($Kind -eq 'node') { $paths += "$env:ProgramFiles\nodejs\node.exe" }
        else {
            $paths += "$env:ProgramFiles\cloudflared\cloudflared.exe"
            $paths += (Join-Path ([Environment]::GetFolderPath('ProgramFilesX86')) 'cloudflared\cloudflared.exe')
        }
        foreach ($candidate in $paths) {
            if (Test-RoomExecutable $candidate $Kind) { return $candidate }
        }
    }
    $architecture = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') { 'arm64' } else { 'x64' }
    $release = $script:RoomRuntimeVersions.$Kind
    $nodeDirectory = Join-Path $script:RoomRuntimeRoot "node-v$($release.version)-win-$architecture"
    $target = if ($Kind -eq 'node') { Join-Path $nodeDirectory 'node.exe' } else { Join-Path $script:RoomRuntimeRoot "cloudflared-$($release.version).exe" }
    if (Test-RoomExecutable $target $Kind) { return $target }

    [void](New-Item -ItemType Directory -Force -Path $script:RoomRuntimeRoot)
    if ($Kind -eq 'cloudflared' -and $architecture -eq 'arm64') {
        Write-Host 'Cloudflare 使用官方 x64 版本，需要 Windows 11 ARM 的 x64 兼容支持。' -ForegroundColor Yellow
    }
    $download = if ($Kind -eq 'node') { $release.$architecture } else { $release.x64 }
    Write-Host "正在从官方源准备 $Kind $($release.version)，首次下载可能需要几分钟…" -ForegroundColor Cyan
    if ($Kind -eq 'node') {
        $archive = Join-Path $script:RoomRuntimeRoot "node-v$($release.version)-win-$architecture.zip"
        Get-RoomDownload $download.url $download.sha256 $archive
        Expand-Archive -LiteralPath $archive -DestinationPath $script:RoomRuntimeRoot -Force
        Remove-Item -LiteralPath $archive -Force
    } else { Get-RoomDownload $download.url $download.sha256 $target }
    if (-not (Test-RoomExecutable $target $Kind)) { throw "$Kind 下载完成，但无法运行。请检查系统兼容性或安全软件提示。" }
    Write-Host "$Kind 已准备好；文件仅保存在项目的 .runtime 目录。" -ForegroundColor Green
    return $target
}
