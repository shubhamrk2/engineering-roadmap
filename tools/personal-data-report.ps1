# personal-data-report.ps1 - find everything worth backing up before a wipe.
#
# READ-ONLY. Reads file names, sizes and paths. Never opens file contents.
# Ignores dev artefacts, Windows, Program Files and app internals.
#
#   powershell -ExecutionPolicy Bypass -File .\personal-data-report.ps1 > personal.txt

$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference    = 'SilentlyContinue'

function Section($t) { "`n"; "=" * 70; "  $t"; "=" * 70 }
function GB($b) { "{0,8:N2} GB" -f ($b / 1GB) }
function MB($b) { "{0,8:N1} MB" -f ($b / 1MB) }

$categories = @{
    'PHOTOS'    = @('*.jpg','*.jpeg','*.png','*.heic','*.gif','*.bmp','*.webp',
                    '*.raw','*.cr2','*.nef','*.dng','*.arw','*.tiff')
    'VIDEOS'    = @('*.mp4','*.mov','*.avi','*.mkv','*.wmv','*.3gp','*.m4v','*.flv','*.webm')
    'DOCUMENTS' = @('*.pdf','*.doc','*.docx','*.xls','*.xlsx','*.ppt','*.pptx',
                    '*.odt','*.ods','*.rtf','*.csv','*.txt','*.md')
    'AUDIO'     = @('*.mp3','*.wav','*.flac','*.m4a','*.aac','*.ogg','*.wma')
    'ARCHIVES'  = @('*.zip','*.rar','*.7z','*.tar','*.gz','*.iso')
}

# Anything matching these is re-downloadable or system noise - not personal data.
$skip = 'node_modules|\\\.venv|\\venv\\|site-packages|\\\.git\\|AppData\\Local\\Temp|' +
        '\\Windows\\|\\Program Files|\\ProgramData\\|\\\$Recycle|\\\.cache\\|' +
        '\\\.gradle|\\\.m2\\|\\\.nuget|\\\.ollama|stable-diffusion|' +
        '\\vscode-server|\\\.docker\\|System Volume Information|\\WpSystem\\|' +
        'AppData\\Local\\Packages\\.*\\LocalCache'

Section "DRIVES"
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    "{0}  total {1}  free {2}" -f $_.DeviceID, (GB $_.Size), (GB $_.FreeSpace)
}

# ---- scan roots -------------------------------------------------------------
$roots = @()
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    if ($_.DeviceID -eq 'C:') {
        $roots += "$env:USERPROFILE"
        Get-ChildItem 'C:\' -Directory -Force |
          Where-Object { $_.Name -notin @('Windows','Program Files','Program Files (x86)',
                          'ProgramData','Users','$Recycle.Bin','System Volume Information',
                          'Recovery','PerfLogs','Intel','AMD','NVIDIA') } |
          ForEach-Object { $roots += $_.FullName }
    } else {
        $roots += "$($_.DeviceID)\"
    }
}
"`nScanning: $($roots -join '  |  ')"
"This takes a few minutes."

# ---- collect ----------------------------------------------------------------
$all = @()
foreach ($cat in $categories.Keys) {
    foreach ($pat in $categories[$cat]) {
        foreach ($r in $roots) {
            Get-ChildItem $r -Recurse -File -Filter $pat -Force -ErrorAction SilentlyContinue |
              Where-Object { $_.FullName -notmatch $skip } |
              ForEach-Object {
                  $all += [PSCustomObject]@{
                      Cat = $cat; Path = $_.FullName; Dir = $_.DirectoryName
                      Size = $_.Length; Modified = $_.LastWriteTime
                  }
              }
        }
    }
}

Section "SUMMARY BY CATEGORY"
"{0,-12} {1,8} {2,>12}" -f "CATEGORY","FILES","SIZE"
"-" * 36
$grand = 0
$all | Group-Object Cat | Sort-Object { ($_.Group | Measure-Object Size -Sum).Sum } -Descending |
  ForEach-Object {
    $s = ($_.Group | Measure-Object Size -Sum).Sum
    $grand += $s
    "{0,-12} {1,8} {2}" -f $_.Name, $_.Count, (GB $s)
  }
"-" * 36
"{0,-12} {1,8} {2}" -f "TOTAL", $all.Count, (GB $grand)

Section "WHERE IT LIVES - TOP 30 FOLDERS"
$all | Group-Object Dir |
  ForEach-Object {
    [PSCustomObject]@{
      Bytes = ($_.Group | Measure-Object Size -Sum).Sum
      Files = $_.Count
      Dir   = $_.Name
    }
  } | Sort-Object Bytes -Descending | Select-Object -First 30 |
  ForEach-Object { "{0} {1,6} files   {2}" -f (GB $_.Bytes), $_.Files, $_.Dir }

Section "LARGEST 25 FILES"
$all | Sort-Object Size -Descending | Select-Object -First 25 |
  ForEach-Object { "{0}  {1}" -f (GB $_.Size), $_.Path }

Section "STANDARD USER FOLDERS"
foreach ($f in 'Desktop','Documents','Downloads','Pictures','Videos','Music') {
    $p = "$env:USERPROFILE\$f"
    if (Test-Path $p) {
        $m = Get-ChildItem $p -Recurse -File -Force -ErrorAction SilentlyContinue |
             Measure-Object -Property Length -Sum
        "{0} {1,6} files   {2}" -f (GB $m.Sum), $m.Count, $p
    }
}

Section "OTHER LARGE FOLDERS IN YOUR PROFILE (over 500 MB, not dev-related)"
Get-ChildItem $env:USERPROFILE -Directory -Force |
  Where-Object { $_.Name -notin @('AppData','Desktop','Documents','Downloads',
                  'Pictures','Videos','Music') -and $_.Name -notmatch '^\.' } |
  ForEach-Object {
    $m = Get-ChildItem $_.FullName -Recurse -File -Force -ErrorAction SilentlyContinue |
         Measure-Object -Property Length -Sum
    if ($m.Sum -gt 500MB) { "{0} {1,6} files   {2}" -f (GB $m.Sum), $m.Count, $_.FullName }
  }

Section "APP DATA WORTH RESCUING"
$appData = @{
    'WhatsApp Desktop media' = "$env:APPDATA\WhatsApp"
    'Telegram Desktop'       = "$env:APPDATA\Telegram Desktop"
    'Chrome profile'         = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default"
    'Edge profile'           = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default"
    'Firefox profiles'       = "$env:APPDATA\Mozilla\Firefox\Profiles"
    'Sticky Notes'           = "$env:LOCALAPPDATA\Packages\Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe\LocalState"
    'Saved Games'            = "$env:USERPROFILE\Saved Games"
    'Outlook data files'     = "$env:LOCALAPPDATA\Microsoft\Outlook"
}
foreach ($k in $appData.Keys | Sort-Object) {
    if (Test-Path $appData[$k]) {
        $m = Get-ChildItem $appData[$k] -Recurse -File -Force -ErrorAction SilentlyContinue |
             Measure-Object -Property Length -Sum
        if ($m.Sum -gt 10MB) { "{0}  {1}" -f (GB $m.Sum), $k }
    }
}

Section "SAFETY CHECK - DO NOT UPLOAD THESE TO CLOUD STORAGE"
"Names only. Contents are never read."
foreach ($p in "$env:USERPROFILE\.ssh", "$env:USERPROFILE\.aws") {
    if (Test-Path $p) {
        "`n  $p"
        Get-ChildItem $p -File -Force | ForEach-Object { "      $($_.Name)" }
    }
}
"`n  Credential-shaped files elsewhere:"
Get-ChildItem $env:USERPROFILE -Recurse -File -Include "*.pem","*.key","*.pfx","*.p12",".env" `
    -Force -Depth 4 -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch $skip } |
  Select-Object -First 20 | ForEach-Object { "      $($_.FullName)" }

Section "END"
