# why-slow.ps1 - diagnose hangs and stutters, and identify unknown large files.
#
# READ-ONLY. Nothing is changed. Run in a normal (non-admin) PowerShell;
# a few sections show more detail if you run as Administrator.
#
#   powershell -ExecutionPolicy Bypass -File .\why-slow.ps1 > slow.txt

$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference    = 'SilentlyContinue'

function Section($t) { "`n"; "=" * 70; "  $t"; "=" * 70 }
function GB($b) { "{0,7:N2} GB" -f ($b / 1GB) }

$admin = ([Security.Principal.WindowsPrincipal] `
          [Security.Principal.WindowsIdentity]::GetCurrent()
         ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
"Running as Administrator: $admin"

# ── 1. DISK SPACE ─────────────────────────────────────────────────────────────
Section "1. FREE SPACE  (the single most common cause of Windows hanging)"
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    $pctFree = if ($_.Size) { [math]::Round(($_.FreeSpace / $_.Size) * 100, 1) } else { 0 }
    $verdict = if ($pctFree -lt 5)  { "  *** CRITICAL - this alone explains the hang ***" }
          elseif ($pctFree -lt 10) { "  *** TOO LOW - Windows needs 10-15% headroom ***" }
          elseif ($pctFree -lt 15) { "  (tight)" } else { "  (ok)" }
    "{0}  total {1}  free {2}  = {3}% free{4}" -f `
        $_.DeviceID, (GB $_.Size), (GB $_.FreeSpace), $pctFree, $verdict
}

# ── 2. MEMORY ─────────────────────────────────────────────────────────────────
Section "2. MEMORY PRESSURE"
$os = Get-CimInstance Win32_OperatingSystem
$totalGB  = $os.TotalVisibleMemorySize / 1MB
$freeGB   = $os.FreePhysicalMemory / 1MB
$usedGB   = $totalGB - $freeGB
$commitGB = ($os.TotalVirtualMemorySize - $os.FreeVirtualMemory) / 1MB
"Physical RAM      : {0:N1} GB" -f $totalGB
"In use            : {0:N1} GB  ({1}%)" -f $usedGB, [math]::Round(($usedGB/$totalGB)*100)
"Free              : {0:N1} GB" -f $freeGB
"Commit charge     : {0:N1} GB" -f $commitGB
if ($commitGB -gt $totalGB) {
    "  *** Commit exceeds physical RAM - the machine is paging to disk. This is your stutter. ***"
}
"`nPage file:"
Get-CimInstance Win32_PageFileUsage | ForEach-Object {
    "  {0}   allocated {1} MB   peak {2} MB" -f $_.Name, $_.AllocatedBaseSize, $_.PeakUsage
}

Section "TOP 15 PROCESSES BY MEMORY"
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 15 |
  ForEach-Object {
    "{0,9:N0} MB   {1,-30} (x{2})" -f `
      ($_.WorkingSet64/1MB), $_.ProcessName, (Get-Process $_.ProcessName).Count
  } | Select-Object -Unique

Section "MEMORY GROUPED BY APPLICATION"
Get-Process | Group-Object ProcessName |
  ForEach-Object {
    [PSCustomObject]@{
      App = $_.Name
      MB  = [math]::Round((($_.Group | Measure-Object WorkingSet64 -Sum).Sum)/1MB)
      Instances = $_.Count
    }
  } | Sort-Object MB -Descending | Select-Object -First 20 |
  ForEach-Object { "{0,9:N0} MB  x{1,-3}  {2}" -f $_.MB, $_.Instances, $_.App }

# ── 3. WSL AND DOCKER ─────────────────────────────────────────────────────────
Section "3. WSL AND DOCKER FOOTPRINT"
"On 16 GB of RAM, a .wslconfig memory cap of 8 GB leaves Windows very little"
"once Chrome, Teams and Docker Desktop are also resident.`n"
$wslcfg = "$env:USERPROFILE\.wslconfig"
if (Test-Path $wslcfg) { "--- $wslcfg"; Get-Content $wslcfg }
else { "No .wslconfig - WSL defaults to 50% of RAM (8 GB here)." }
""
wsl --list --verbose
"`nvmmem / WSL process memory:"
Get-Process vmmem*, vmmemWSL -ErrorAction SilentlyContinue |
  ForEach-Object { "  {0,9:N0} MB  {1}" -f ($_.WorkingSet64/1MB), $_.ProcessName }
"`nDocker:"
docker system df 2>$null
if (-not $?) { "  Docker CLI not responding (not running, or not installed)." }

# ── 4. STARTUP LOAD ───────────────────────────────────────────────────────────
Section "4. THINGS THAT START WITH WINDOWS"
Get-CimInstance Win32_StartupCommand |
  Select-Object Name, Location, Command |
  Sort-Object Name | ForEach-Object {
    "  {0,-32} [{1}]" -f $_.Name, $_.Location
  }
"`nStartup folder items:"
foreach ($p in "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup",
               "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Startup") {
    Get-ChildItem $p -File | ForEach-Object { "  $($_.Name)" }
}

# ── 5. DISK HEALTH ────────────────────────────────────────────────────────────
Section "5. DISK TYPE AND HEALTH"
Get-PhysicalDisk | ForEach-Object {
    "{0}`n  Media      : {1}`n  Bus        : {2}`n  Size       : {3}`n  Health     : {4}" -f `
      $_.FriendlyName, $_.MediaType, $_.BusType, (GB $_.Size), $_.HealthStatus
    $rc = $_ | Get-StorageReliabilityCounter
    if ($rc) {
        "  Power-on hrs: $($rc.PowerOnHours)"
        "  Wear        : $($rc.Wear)"
        "  Read errors : $($rc.ReadErrorsTotal)"
        "  Temperature : $($rc.Temperature) C"
    }
}

# ── 6. RECENT CRASHES AND HANGS ───────────────────────────────────────────────
Section "6. RECENT CRITICAL EVENTS  (last 14 days)"
"Kernel-Power 41 = the machine stopped responding or lost power abruptly."
"BugCheck        = a blue screen."
""
Get-WinEvent -FilterHashtable @{
    LogName   = 'System'
    Level     = 1,2
    StartTime = (Get-Date).AddDays(-14)
} -MaxEvents 40 |
  Group-Object Id, ProviderName |
  Sort-Object Count -Descending |
  ForEach-Object {
    $e = $_.Group[0]
    "  x{0,-4} Event {1,-6} {2}" -f $_.Count, $e.Id, $e.ProviderName
    "         last: $($e.TimeCreated)"
    "         $(($e.Message -split "`n")[0])"
  }

Section "APPLICATION HANGS (last 14 days)"
Get-WinEvent -FilterHashtable @{
    LogName='Application'; ProviderName='Application Hang'; StartTime=(Get-Date).AddDays(-14)
} -MaxEvents 20 |
  Group-Object { ($_.Message -split "`n")[0] } |
  Sort-Object Count -Descending | Select-Object -First 10 |
  ForEach-Object { "  x{0}  {1}" -f $_.Count, $_.Name }

# ── 7. POWER AND THERMAL ──────────────────────────────────────────────────────
Section "7. POWER PLAN"
powercfg /getactivescheme
"`nA laptop stuck on Power Saver, or with the AMD chipset driver missing,"
"will feel like a hang under load. Check Balanced or Performance."

# ── 8. PENDING UPDATES / REBOOT ───────────────────────────────────────────────
Section "8. PENDING REBOOT"
$pending = @()
if (Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending") { $pending += "Component Based Servicing" }
if (Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired") { $pending += "Windows Update" }
if ($pending) { "REBOOT PENDING: $($pending -join ', ')" } else { "No pending reboot." }
"Last boot: $((Get-CimInstance Win32_OperatingSystem).LastBootUpTime)"
"Uptime   : $((Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime)"

# ── 9. UNKNOWN LARGE FILES ────────────────────────────────────────────────────
Section "9. LARGEST FILES OVER 500 MB - WHAT ARE THEY?"
"Each line is annotated so you can decide what is safe to delete."
""
$notes = @(
    @{ m = 'ext4\.vhdx$';                   n = 'WSL Linux disk. Contains your ~/code. Export before deleting.' },
    @{ m = 'docker_data\.vhdx|DockerDesktop'; n = 'Docker images and volumes. Safe: docker system prune -a' },
    @{ m = '\\pagefile\.sys$';              n = 'Windows page file. System-managed. Do not delete.' },
    @{ m = '\\hiberfil\.sys$';              n = 'Hibernation file. Reclaim with: powercfg /h off' },
    @{ m = '\\swapfile\.sys$';              n = 'Windows swap. System-managed. Do not delete.' },
    @{ m = '\\Windows\.old\\';              n = 'Previous Windows install. Safe to delete via Disk Cleanup.' },
    @{ m = '\.ollama\\models';              n = 'Ollama model weights. Re-downloadable: ollama pull' },
    @{ m = 'stable-diffusion';              n = 'Stable Diffusion. Removal steps in assets/images/README.md' },
    @{ m = '\\node_modules\\';              n = 'Node dependencies. Re-downloadable: npm install' },
    @{ m = '\.venv\\|\\venv\\';             n = 'Python virtualenv. Re-downloadable: uv sync' },
    @{ m = '\\\.gradle\\|\\\.m2\\';         n = 'Java build cache. Re-downloadable.' },
    @{ m = '\\\.cache\\huggingface';        n = 'HuggingFace model cache. Re-downloadable.' },
    @{ m = '\\vscode-server';               n = 'VS Code WSL server. Rebuilt automatically.' },
    @{ m = '\\Temp\\|\\Downloads\\';        n = 'Temp or Downloads. Review, then usually safe.' },
    @{ m = '\.(iso|zip|rar|7z)$';           n = 'Archive or disc image. Check before deleting.' },
    @{ m = '\.(mp4|mkv|mov|avi)$';          n = 'VIDEO - likely personal. BACK THIS UP.' },
    @{ m = '\.(jpg|jpeg|png|heic|raw|cr2)$';n = 'PHOTO - likely personal. BACK THIS UP.' },
    @{ m = '\.(pst|ost)$';                  n = 'Outlook mailbox. Personal - back up.' }
)

$drives = (Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3").DeviceID
foreach ($d in $drives) {
    Get-ChildItem "$d\" -Recurse -File -Force -ErrorAction SilentlyContinue |
      Where-Object { $_.Length -gt 500MB } |
      Sort-Object Length -Descending | Select-Object -First 30 |
      ForEach-Object {
        $note = "unrecognised - check before deleting"
        foreach ($r in $notes) { if ($_.FullName -match $r.m) { $note = $r.n; break } }
        "{0}  {1}" -f (GB $_.Length), $_.FullName
        "            -> $note"
      }
}

Section "END OF REPORT"
