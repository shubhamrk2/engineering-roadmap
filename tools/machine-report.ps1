# machine-report.ps1 - inventory a Windows machine before a wipe.
#
# READ-ONLY. Nothing is deleted, moved or modified.
# Takes 2-5 minutes; folder sizing is the slow part.
#
#   powershell -ExecutionPolicy Bypass -File .\machine-report.ps1 > report.txt
#
# Then paste report.txt back.

$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference    = 'SilentlyContinue'

function Section($t) { "`n"; "=" * 68; "  $t"; "=" * 68 }
function GB($bytes)  { "{0,8:N2} GB" -f ($bytes / 1GB) }

function FolderSize($path) {
    if (-not (Test-Path $path)) { return $null }
    $m = Get-ChildItem $path -Recurse -File -Force -ErrorAction SilentlyContinue |
         Measure-Object -Property Length -Sum
    return $m.Sum
}

Section "SYSTEM"
$os  = Get-CimInstance Win32_OperatingSystem
$cs  = Get-CimInstance Win32_ComputerSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
"OS            : $($os.Caption) $($os.OSArchitecture)"
"Build         : $($os.Version)"
"Installed on  : $($os.InstallDate)"
"Last boot     : $($os.LastBootUpTime)"
"CPU           : $($cpu.Name.Trim())  ($($cpu.NumberOfCores)C/$($cpu.NumberOfLogicalProcessors)T)"
"RAM           : $('{0:N1} GB' -f ($cs.TotalPhysicalMemory / 1GB))"
Get-CimInstance Win32_VideoController | ForEach-Object {
    "GPU           : $($_.Name)  driver $($_.DriverVersion)"
}

Section "DISKS"
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    $used = $_.Size - $_.FreeSpace
    $pct  = if ($_.Size -gt 0) { [math]::Round(($used / $_.Size) * 100) } else { 0 }
    "{0}  total {1}  used {2}  free {3}   {4}% full" -f `
        $_.DeviceID, (GB $_.Size), (GB $used), (GB $_.FreeSpace), $pct
}

Section "TOP-LEVEL FOLDERS ON C:  (sizes, largest first)"
Get-ChildItem C:\ -Directory -Force |
  Where-Object { $_.Name -notin @('Windows','$Recycle.Bin','System Volume Information') } |
  ForEach-Object {
    $s = FolderSize $_.FullName
    if ($s) { [PSCustomObject]@{ Bytes = $s; Path = $_.FullName } }
  } | Sort-Object Bytes -Descending | Select-Object -First 12 |
  ForEach-Object { "{0}  {1}" -f (GB $_.Bytes), $_.Path }

Section "YOUR PROFILE - WHAT IS ACTUALLY BIG"
$profileDirs = @(
    "$env:USERPROFILE\Desktop", "$env:USERPROFILE\Documents",
    "$env:USERPROFILE\Downloads", "$env:USERPROFILE\Pictures",
    "$env:USERPROFILE\Videos", "$env:USERPROFILE\Music",
    "$env:USERPROFILE\source", "$env:USERPROFILE\code", "$env:USERPROFILE\projects",
    "$env:USERPROFILE\.cache", "$env:USERPROFILE\.ollama",
    "$env:LOCALAPPDATA", "$env:APPDATA"
)
foreach ($d in $profileDirs) {
    $s = FolderSize $d
    if ($s) { "{0}  {1}" -f (GB $s), $d }
}

Section "LARGEST INDIVIDUAL FILES OVER 1 GB IN YOUR PROFILE"
Get-ChildItem $env:USERPROFILE -Recurse -File -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.Length -gt 1GB } |
  Sort-Object Length -Descending | Select-Object -First 20 |
  ForEach-Object { "{0}  {1}" -f (GB $_.Length), $_.FullName }

Section "WSL"
wsl --list --verbose
""
"VHDX files (the WSL disk images - these are usually the biggest single files):"
Get-ChildItem "$env:LOCALAPPDATA\Packages" -Recurse -Filter "*.vhdx" -ErrorAction SilentlyContinue |
  ForEach-Object { "{0}  {1}" -f (GB $_.Length), $_.FullName }
Get-ChildItem "$env:LOCALAPPDATA\Docker" -Recurse -Filter "*.vhdx" -ErrorAction SilentlyContinue |
  ForEach-Object { "{0}  {1}" -f (GB $_.Length), $_.FullName }

Section "DOCKER"
docker system df 2>$null
if (-not $?) { "Docker not running or not installed." }

Section "OLLAMA MODELS"
if (Test-Path "$env:USERPROFILE\.ollama\models") {
    "{0}  .ollama\models" -f (GB (FolderSize "$env:USERPROFILE\.ollama\models"))
    ollama list 2>$null
} else { "Ollama models directory not found." }

Section "STABLE DIFFUSION / IMAGE TOOLS"
$sd = Get-ChildItem C:\ -Directory -Filter "stable-diffusion*" -Recurse -Depth 3 -ErrorAction SilentlyContinue |
      Select-Object -First 2
if ($sd) {
    foreach ($f in $sd) { "{0}  {1}" -f (GB (FolderSize $f.FullName)), $f.FullName }
} else { "None found in the first 3 levels of C:\" }

Section "GIT REPOSITORIES - CHECK FOR UNCOMMITTED WORK"
$searchRoots = @("$env:USERPROFILE", "C:\dev", "C:\code", "D:\")
$seen = @{}
foreach ($root in $searchRoots) {
    if (-not (Test-Path $root)) { continue }
    Get-ChildItem $root -Recurse -Directory -Filter ".git" -Depth 4 -Force -ErrorAction SilentlyContinue |
      ForEach-Object {
        $repo = $_.Parent.FullName
        if ($seen.ContainsKey($repo)) { return }
        $seen[$repo] = $true
        Push-Location $repo
        $dirty  = (git status --porcelain 2>$null | Measure-Object).Count
        $branch = git rev-parse --abbrev-ref HEAD 2>$null
        $remote = git remote get-url origin 2>$null
        $unpush = (git log --branches --not --remotes --oneline 2>$null | Measure-Object).Count
        Pop-Location
        $flag = ""
        if ($dirty  -gt 0) { $flag += " [$dirty UNCOMMITTED]" }
        if ($unpush -gt 0) { $flag += " [$unpush UNPUSHED]" }
        if (-not $remote)  { $flag += " [NO REMOTE]" }
        "$repo  ($branch)$flag"
        if ($remote) { "    origin: $remote" }
      }
}

Section "IRREPLACEABLE - THESE CANNOT BE RE-DOWNLOADED"
"SSH keys:"
Get-ChildItem "$env:USERPROFILE\.ssh" -File -ErrorAction SilentlyContinue |
  ForEach-Object { "    $($_.Name)" }
"`nAWS config (DO NOT upload credentials to cloud storage):"
Get-ChildItem "$env:USERPROFILE\.aws" -File -ErrorAction SilentlyContinue |
  ForEach-Object { "    $($_.Name)" }
"`n.env files found (names only, contents NOT read):"
Get-ChildItem $env:USERPROFILE -Recurse -File -Filter ".env*" -Force -Depth 5 -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch 'node_modules|\.venv|site-packages' } |
  Select-Object -First 25 | ForEach-Object { "    $($_.FullName)" }
"`nKeys and certificates:"
Get-ChildItem $env:USERPROFILE -Recurse -File -Include "*.pem","*.key","*.pfx","*.p12" -Force -Depth 5 -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch 'node_modules|\.venv' } |
  Select-Object -First 15 | ForEach-Object { "    $($_.FullName)" }

Section "RECLAIMABLE WITHOUT A RESET"
$junk = @{
    "Windows.old (previous Windows)" = "C:\Windows.old"
    "User temp"                      = $env:TEMP
    "Windows temp"                   = "C:\Windows\Temp"
    "Windows Update cache"           = "C:\Windows\SoftwareDistribution\Download"
    "pip cache"                      = "$env:LOCALAPPDATA\pip\Cache"
    "npm cache"                      = "$env:APPDATA\npm-cache"
    "HuggingFace cache"              = "$env:USERPROFILE\.cache\huggingface"
    "Torch cache"                    = "$env:USERPROFILE\.cache\torch"
    "NuGet packages"                 = "$env:USERPROFILE\.nuget\packages"
    "Gradle cache"                   = "$env:USERPROFILE\.gradle"
    "Maven repository"               = "$env:USERPROFILE\.m2"
    "VS Code server (WSL)"           = "$env:USERPROFILE\.vscode-server"
    "Delivery Optimization"          = "C:\Windows\ServiceProfiles\NetworkService\AppData\Local\Microsoft\Windows\DeliveryOptimization"
}
$total = 0
foreach ($k in $junk.Keys | Sort-Object) {
    $s = FolderSize $junk[$k]
    if ($s -gt 100MB) { "{0}  {1}" -f (GB $s), $k; $total += $s }
}
"`nRecycle Bin:"
$rb = FolderSize "C:\`$Recycle.Bin"
if ($rb) { "{0}  Recycle Bin" -f (GB $rb); $total += $rb }
"`n{0}  <-- RECLAIMABLE WITHOUT REINSTALLING ANYTHING" -f (GB $total)

Section "INSTALLED APPLICATIONS"
winget list --disable-interactivity 2>$null | Select-Object -Skip 2

Section "END OF REPORT"
