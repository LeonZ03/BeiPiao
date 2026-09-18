[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [switch]$NonInteractive,
    [ValidateRange(1024, 65535)]
    [int]$Port = 48173,
    [switch]$SkipTunnel
)

$ErrorActionPreference = 'Stop'
$taskDir = $PSScriptRoot
$instanceSuffix = if ($Port -eq 48173) { '' } else { "-$Port" }
$stateFile = Join-Path $taskDir "runtime$instanceSuffix.json"
$linkFile = Join-Path $taskDir "current-link$instanceSuffix.txt"
$serverOutLog = Join-Path $taskDir "server$instanceSuffix.out.log"
$serverErrLog = Join-Path $taskDir "server$instanceSuffix.err.log"
$tunnelOutLog = Join-Path $taskDir "tunnel$instanceSuffix.out.log"
$tunnelErrLog = Join-Path $taskDir "tunnel$instanceSuffix.err.log"
$publicCheckLog = Join-Path $taskDir "public-check$instanceSuffix.log"
$localUrl = "http://127.0.0.1:$Port"
$job = $null
$mutex = $null
$ownsMutex = $false
$failure = $null
$state = $null
$localServer = $null
$tunnel = $null

function Write-RoomLine([string]$message = '', [ConsoleColor]$color = [ConsoleColor]::Gray) {
    # Let PowerShell's Unicode host handle CJK cell widths in the visible console.
    Write-Host -Object $message -ForegroundColor $color
}

function Get-OwnedProcess($record) {
    if (-not $record) { return $null }
    $process = Get-Process -Id $record.id -ErrorAction SilentlyContinue
    if ($process -and $process.StartTime.ToUniversalTime().Ticks.ToString() -eq $record.startedTicks) {
        return $process
    }
    return $null
}

function Get-ProcessRecord($process) {
    return @{
        id = $process.Id
        startedTicks = $process.StartTime.ToUniversalTime().Ticks.ToString()
        name = $process.ProcessName
    }
}

function Open-RoomBrowser([string]$url) {
    if ($NoBrowser) { return }
    try { Start-Process -FilePath $url }
    catch { Write-RoomLine '未能自动打开浏览器，请复制本机地址访问。' Yellow }
}

function Write-State {
    if ($state) { $state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $stateFile -Encoding UTF8 }
}

function Test-RoomMarkup([string]$content) {
    # Stable application identity, independent of homepage layout or module names.
    return $content.Contains('<!-- beipiao-room-app:v1 -->')
}

function Test-RoomPage([string]$url, [int]$timeoutSeconds = 6) {
    try {
        $separator = if ($url.Contains('?')) { '&' } else { '?' }
        $probeUrl = $url + $separator + '__room_probe=' + [Guid]::NewGuid().ToString('N')
        $response = Invoke-WebRequest -Uri $probeUrl -UseBasicParsing -TimeoutSec $timeoutSeconds `
            -Headers @{ 'Cache-Control' = 'no-cache'; 'Pragma' = 'no-cache' }
        $isRoom = $response.StatusCode -eq 200 -and (Test-RoomMarkup ([string]$response.Content))
        return [pscustomobject]@{
            Success = $isRoom
            Error = if ($isRoom) { $null } else { "返回了 HTTP $($response.StatusCode)，但不是房间首页。" }
        }
    } catch {
        return [pscustomobject]@{ Success = $false; Error = $_.Exception.Message }
    }
}

function Resolve-PublicAddress([string]$hostName) {
    foreach ($resolver in @('1.1.1.1', '8.8.8.8')) {
        try {
            $addresses = @(Resolve-DnsName $hostName -Type A -Server $resolver -DnsOnly -QuickTimeout -ErrorAction Stop |
                Where-Object { $_.IPAddress } | Select-Object -ExpandProperty IPAddress -Unique)
            if ($addresses.Count -gt 0) { return $addresses }
        } catch { }
    }
    return @()
}

function Test-RoomPageWithAddress([string]$url, [string]$ipAddress, [int]$timeoutSeconds = 8) {
    $curl = Get-Command 'curl.exe' -ErrorAction SilentlyContinue
    if (-not $curl) { return [pscustomobject]@{ Success = $false; Error = '找不到 curl.exe，无法执行独立 DNS 验证。' } }
    $uri = New-Object System.Uri($url)
    $probeUrl = $url + '?__room_probe=' + [Guid]::NewGuid().ToString('N')
    # Windows PowerShell 5 can promote redirected native stderr to NativeCommandError
    # when the script uses ErrorActionPreference=Stop. Keep a failed curl probe as data
    # so the bounded retry loop can continue instead of aborting the public check.
    $previousErrorPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = & $curl.Source '--silent' '--show-error' '--fail' '--location' '--max-time' $timeoutSeconds `
            '--noproxy' '*' '--resolve' "$($uri.DnsSafeHost):443:$ipAddress" `
            '--header' 'Cache-Control: no-cache' $probeUrl 2>&1
        $exitCode = $LASTEXITCODE
    } catch {
        return [pscustomobject]@{ Success = $false; Error = $_.Exception.Message }
    } finally {
        $ErrorActionPreference = $previousErrorPreference
    }
    $content = [string]::Join([Environment]::NewLine, @($output))
    $isRoom = $exitCode -eq 0 -and (Test-RoomMarkup $content)
    return [pscustomobject]@{
        Success = $isRoom
        Error = if ($isRoom) { $null } elseif ($exitCode -ne 0) { "curl 退出码 $exitCode：$content" } else { 'HTTPS 返回内容不是房间首页。' }
    }
}

function Test-PublicRoom([string]$url) {
    $normal = Test-RoomPage $url 7
    if ($normal.Success) {
        return [pscustomobject]@{ Success = $true; Method = 'normal'; Warning = $null; Error = $null }
    }

    $uri = New-Object System.Uri($url)
    $systemDnsWorks = $true
    try {
        [void](Resolve-DnsName $uri.DnsSafeHost -Type A -DnsOnly -QuickTimeout -ErrorAction Stop)
    } catch { $systemDnsWorks = $false }

    $publicAddresses = @(Resolve-PublicAddress $uri.DnsSafeHost)
    foreach ($address in $publicAddresses) {
        $direct = Test-RoomPageWithAddress $url $address 8
        if ($direct.Success) {
            $warning = if (-not $systemDnsWorks) {
                '公网隧道已验证，但这台电脑的系统 DNS 暂时无法解析该临时域名。本机请使用已打开的本机地址；手机可切换到移动网络后再试公开链接。'
            } else {
                '公网隧道已验证，但这台电脑的常规 HTTPS 路径未通过，可能受当前代理规则影响。本机请使用已打开的本机地址。'
            }
            return [pscustomobject]@{ Success = $true; Method = 'verified-direct'; Warning = $warning; Error = $normal.Error }
        }
    }

    $detail = $normal.Error
    if (-not $systemDnsWorks -and $publicAddresses.Count -gt 0) {
        $detail = "系统 DNS 返回该域名不存在；公共 DNS 能解析，但独立 HTTPS 探针仍未取得房间页面。原始错误：$detail"
    } elseif ($publicAddresses.Count -eq 0) {
        $detail = "公开域名尚未在公共 DNS 中出现。原始错误：$detail"
    }
    return [pscustomobject]@{ Success = $false; Method = 'failed'; Warning = $null; Error = $detail }
}

function Set-LocalOnlyState([string]$reason, [string]$candidateUrl) {
    $state.status = 'local-only'
    $state.publicError = $reason
    if ($candidateUrl) { $state.candidateUrl = $candidateUrl }
    Write-State
    @(
        "本机地址：$localUrl"
        '公开链接尚未通过房间页面验证。'
        $(if ($candidateUrl) { "候选地址（未验证）：$candidateUrl" })
        "原因：$reason"
    ) | Where-Object { $_ } | Set-Content -LiteralPath $linkFile -Encoding UTF8
}

try {
    try { $Host.UI.RawUI.WindowTitle = '永旺家园 · 关闭此窗口即停止' } catch { }

    $mutex = New-Object System.Threading.Mutex($false, "Local\YongwangRoom_$Port")
    try { $ownsMutex = $mutex.WaitOne(0) }
    catch [System.Threading.AbandonedMutexException] { $ownsMutex = $true }
    if (-not $ownsMutex) {
        Write-RoomLine '房间已在另一个 PowerShell 窗口运行。' Yellow
        Write-RoomLine "本机地址：$localUrl" Cyan
        $existing = $null
        try { $existing = Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json } catch { }
        if ($existing.status -eq 'public-ready' -and $existing.url -match '^https://[a-z0-9-]+\.trycloudflare\.com$') {
            Write-RoomLine '已验证的公开地址：' Green
            Write-RoomLine ([string]$existing.url) Cyan
            if ($existing.accessWarning) { Write-RoomLine ([string]$existing.accessWarning) Yellow }
        } elseif ($existing.candidateUrl) {
            Write-RoomLine "公开地址仍未验证：$($existing.candidateUrl)" Yellow
        } else {
            Write-RoomLine '另一个窗口正在启动公开通道，请稍候。'
        }
        Open-RoomBrowser $localUrl
        Write-RoomLine '关闭原来的运行窗口，才会停止服务。本窗口即将关闭。'
        if (-not $NonInteractive) { Start-Sleep -Seconds 4 }
        return
    }

    Write-RoomLine ''
    Write-RoomLine '  永旺家园 · 房间漫游' Cyan
    Write-RoomLine '  保持本窗口打开；关闭窗口即可结束网页服务和 Cloudflare。'
    Write-RoomLine ''

    . (Join-Path $taskDir 'runtime-tools.ps1')
    $node = Resolve-RoomProgram 'node'
    if (-not (Test-Path -LiteralPath (Join-Path $taskDir '..\room-site\dist\index.html'))) {
        throw '未找到房间网页成品：room-site\dist\index.html。'
    }
    Add-Type -Path (Join-Path $taskDir 'RoomProcessJob.cs')
    $job = New-Object RoomProcessJob

    # Only migrate processes whose PID and exact creation time match our prior record.
    if (Test-Path -LiteralPath $stateFile) {
        try { $previous = Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json }
        catch { $previous = $null }
        foreach ($record in @($previous.tunnel, $previous.server)) {
            $oldProcess = Get-OwnedProcess $record
            if ($oldProcess -and $oldProcess.ProcessName -in @('node', 'cloudflared')) {
                Stop-Process -Id $oldProcess.Id -ErrorAction SilentlyContinue
                [void]$oldProcess.WaitForExit(5000)
            }
        }
    }

    $state = @{ controller = Get-ProcessRecord (Get-Process -Id $PID); status = 'starting'; server = $null; tunnel = $null; localUrl = $localUrl }
    Write-State
    "正在检查本机网页：$localUrl" | Set-Content -LiteralPath $linkFile -Encoding UTF8
    Write-RoomLine '[1/2] 正在启动本地网页…'
    $localServer = $job.Start($node, [string[]]@((Join-Path $taskDir 'serve-room.mjs'), '--port', $Port.ToString()), $taskDir,
        $serverOutLog, $serverErrLog)
    $state.server = Get-ProcessRecord $localServer
    Write-State
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($localServer.HasExited) { throw "本地网页启动失败，请查看 $serverErrLog（可能端口已被占用）。" }
        $localCheck = Test-RoomPage $localUrl 2
        if ($localCheck.Success) { $ready = $true; break }
        Start-Sleep -Milliseconds 250
    }
    if ($localServer.HasExited) { throw "本地网页进程已退出，请查看 $serverErrLog。" }
    if (-not $ready) { throw "本地网页检查未通过：$($localCheck.Error) 地址：$localUrl。网页进程已启动，详细输出见 $serverOutLog。" }
    $state.status = 'local-ready'
    Write-State
    Write-RoomLine "      本机访问：$localUrl" Green
    Open-RoomBrowser $localUrl

    if ($SkipTunnel) {
        "仅本机测试：$localUrl" | Set-Content -LiteralPath $linkFile -Encoding UTF8
        Write-RoomLine '      已按测试参数跳过公开通道。' Yellow
    } else {
        Write-RoomLine '[2/2] 正在连接 Cloudflare，并验证公开页面…'
        $candidateUrl = $null
        $publicReady = $false
        $publicReason = $null
        try {
            $cloudflared = Resolve-RoomProgram 'cloudflared'
            $tunnel = $job.Start($cloudflared,
                [string[]]@('tunnel', '--no-autoupdate', '--protocol', 'http2', '--url', $localUrl), $taskDir,
                $tunnelOutLog, $tunnelErrLog)
            $state.tunnel = Get-ProcessRecord $tunnel
            Write-State

            $registrationDeadline = [DateTime]::UtcNow.AddSeconds(90)
            $registered = $false
            while ([DateTime]::UtcNow -lt $registrationDeadline) {
                if ($localServer.HasExited) { throw '本地网页服务意外结束。' }
                if ($tunnel.HasExited) { throw 'Cloudflare 进程提前结束。' }
                $log = [string](Get-Content -LiteralPath $tunnelErrLog -Raw -ErrorAction SilentlyContinue)
                $match = [regex]::Match($log, 'https://[a-z0-9-]+\.trycloudflare\.com')
                if ($match.Success) { $candidateUrl = $match.Value }
                if ($candidateUrl -and $log -match 'Registered tunnel connection') { $registered = $true; break }
                Start-Sleep -Milliseconds 500
            }
            if (-not $registered) { throw 'Cloudflare 在 90 秒内没有完成连接注册。' }

            "[$([DateTime]::Now.ToString('s'))] Candidate: $candidateUrl" | Set-Content -LiteralPath $publicCheckLog -Encoding UTF8
            $probeDeadline = [DateTime]::UtcNow.AddSeconds(90)
            $probeAttempt = 0
            while ([DateTime]::UtcNow -lt $probeDeadline) {
                if ($localServer.HasExited) { throw '本地网页服务意外结束。' }
                if ($tunnel.HasExited) { throw 'Cloudflare 进程在公开验证期间结束。' }
                $probeAttempt++
                $probe = Test-PublicRoom $candidateUrl
                "[$([DateTime]::Now.ToString('s'))] Attempt $probeAttempt; method=$($probe.Method); success=$($probe.Success); error=$($probe.Error)" |
                    Add-Content -LiteralPath $publicCheckLog -Encoding UTF8
                if ($probe.Success) {
                    $publicReady = $true
                    $state.status = 'public-ready'
                    $state.url = $candidateUrl
                    $state.publicVerification = $probe.Method
                    if ($probe.Warning) { $state.accessWarning = $probe.Warning }
                    Write-State
                    @($candidateUrl, $(if ($probe.Warning) { "提示：$($probe.Warning)" })) | Where-Object { $_ } |
                        Set-Content -LiteralPath $linkFile -Encoding UTF8
                    break
                }
                $publicReason = $probe.Error
                if ($probeAttempt % 3 -eq 0) { Write-RoomLine '      公开地址尚未返回房间页面，继续等待…' Yellow }
                Start-Sleep -Seconds 3
            }
            if (-not $publicReady -and -not $publicReason) { $publicReason = '公开地址在 90 秒内未返回房间页面。' }
        } catch {
            $publicReason = $_.Exception.Message
        }

        Write-RoomLine ''
        if ($publicReady) {
            Write-RoomLine '  公网房间页面已经过 HTTPS 内容验证：' Green
            Write-RoomLine "  $candidateUrl" Cyan
            if ($state.accessWarning) { Write-RoomLine "  $($state.accessWarning)" Yellow }
        } else {
            Set-LocalOnlyState $publicReason $candidateUrl
            Write-RoomLine '  本地房间已启动；公开地址未通过验证，因此没有标记为可用。' Yellow
            if ($candidateUrl) { Write-RoomLine "  候选地址（未验证）：$candidateUrl" Cyan }
            Write-RoomLine "  原因：$publicReason" Yellow
            Write-RoomLine '  可保持本窗口运行；本机地址仍可正常使用。'
            Write-RoomLine "  诊断记录：$publicCheckLog"
        }
    }

    Write-RoomLine ''
    Write-RoomLine '  停止：直接关闭此 PowerShell 窗口，或按 Ctrl+C。'
    Write-RoomLine ''

    $tunnelExitReported = $false
    while ($true) {
        Start-Sleep -Seconds 1
        if ($localServer.HasExited) { throw '本地网页服务已结束，请重新双击启动。' }
        if ($tunnel -and $tunnel.HasExited -and -not $tunnelExitReported) {
            $tunnelExitReported = $true
            Set-LocalOnlyState 'Cloudflare 进程已结束；本机房间继续运行。' $candidateUrl
            Write-RoomLine 'Cloudflare 已结束；本机房间仍在运行。关闭窗口后可重新双击尝试公开连接。' Yellow
        }
    }
}
catch {
    $failure = $_.Exception.Message
}
finally {
    # Closing the console also closes this job handle; only our server and tunnel are members.
    if ($job) { $job.Dispose() }
    if ($ownsMutex) {
        if ($state) {
            $state.status = 'stopped'
            if ($failure) { $state.failure = $failure }
            Write-State
            "已停止。重新双击启动器可创建新的公开地址；本机地址为 $localUrl。" |
                Set-Content -LiteralPath $linkFile -Encoding UTF8 -ErrorAction SilentlyContinue
        }
        $mutex.ReleaseMutex()
    }
    if ($mutex) { $mutex.Dispose() }
}

if ($failure) {
    Write-RoomLine ''
    Write-RoomLine "启动或运行失败：$failure" Red
    Write-RoomLine '本次启动的服务已停止。修复后重新双击即可。'
    if (-not $NonInteractive) { [void](Read-Host '按回车关闭窗口') }
    exit 1
}
