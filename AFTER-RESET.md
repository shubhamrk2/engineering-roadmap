# Clean Install and Recovery — Full Walkthrough

> Personal laptop: ASUS, AMD Ryzen 7000, NVIDIA RTX 2050 (4 GB), Samsung NVMe 512 GB.
> Every screen, every option, every download link.
>
> **Phase 0 → 3** is the reset. **Phase 4 → 9** is getting back to normal.
> Budget one full day. Most of it is unattended downloading.

---

# PHASE 0 — Before you touch Reset

## 0.1 Write down your machine model

You need this to download the right drivers, and **after the reset you won't be able to
look it up from the machine**. Do it now.

```powershell
Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model
Get-CimInstance Win32_BIOS          | Select-Object SerialNumber, SMBIOSBIOSVersion
(Get-CimInstance Win32_BaseBoard).Product
Get-CimInstance Win32_Processor     | Select-Object Name
Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion
```

Write the output on paper or your phone. You want:

- [ ] Model — e.g. `ASUS TUF Gaming F15 FX507ZC4`
- [ ] Serial number
- [ ] CPU — e.g. `AMD Ryzen 7 7435HS`
- [ ] GPU — `NVIDIA GeForce RTX 2050`

## 0.2 Backup checklist — tick every box

- [ ] Videos uploaded to TeraBox
- [ ] Audition projects uploaded (`Documents\Adobe\Audition`, `OneDrive\Documents\Adobe`)
- [ ] Call recordings uploaded (`C:\S23\Recordings`)
- [ ] `C:\Development\` uploaded
- [ ] **Downloaded three random files back from TeraBox and opened them** — a video,
      an audio project, a document
- [ ] Photos confirmed present on the phone
- [ ] WSL SSH key copied out, or accepted that you'll generate a new one
- [ ] `git push` done in every repo — `cd ~/code/badgedesk && git status`
- [ ] Chrome signed in and synced (bookmarks, passwords)
- [ ] Browser passwords exported as a second copy:
      `chrome://password-manager/settings` → Export passwords → save to TeraBox
- [ ] WiFi password known — you'll need to type it on first boot
- [ ] Microsoft account email **and password** known — not just the PIN

> **The PIN will not work after the reset.** It is tied to this Windows install.
> You need the actual Microsoft account password. Verify it now at
> account.microsoft.com in a private browser window.

## 0.3 Physical prep

- [ ] **Charger plugged in.** Do not attempt this on battery.
- [ ] Unplug every USB device, SD card, external drive — especially relevant given your
      Disk 1 errors
- [ ] Stable WiFi (the reset downloads ~5 GB)
- [ ] Set aside 2 uninterrupted hours

---

# PHASE 1 — The reset, screen by screen

## 1.1 Open Recovery

```
Settings  →  System  →  Recovery
```

Under **Recovery options**, find **Reset this PC** → click the **Reset PC** button.

A blue dialog opens.

## 1.2 Screen: "Choose an option"

| Option | Choose? |
|---|---|
| **Keep my files** — removes apps and settings, keeps personal files | ❌ No |
| **Remove everything** — removes apps, settings and personal files | ✅ **YES** |

Click **Remove everything**.

## 1.3 Screen: "How would you like to reinstall Windows?"

| Option | Choose? |
|---|---|
| **Cloud download** — downloads a fresh Windows image (~5 GB) | ✅ **YES** |
| **Local reinstall** — rebuilds from the recovery partition on this disk | ❌ No |

Click **Cloud download**.

> **Why cloud download:** the local recovery partition holds the image your laptop
> shipped with — potentially years old, and possibly carrying the same corruption you're
> trying to escape. Cloud download fetches current Windows from Microsoft. On your
> 100 Mbps line it's about 7 minutes. This is the whole reason a USB stick isn't needed.

## 1.4 Screen: "Additional settings"

You'll see a summary like:

```
Current settings:
  • Clean data? No
  • Delete files from all drives? No
  • Download and reinstall Windows

     Change settings
```

Click **Change settings**.

## 1.5 Screen: "Choose settings"

Three toggles:

| Toggle | Set to | Why |
|---|---|---|
| **Clean data?** | **No** | "Yes" overwrites every sector to defeat file recovery. It adds **several hours** and is only for a machine you're selling or giving away. You're keeping this laptop. |
| **Delete files from all drives?** | **No** | You only have C:. Irrelevant either way. |
| **Download Windows?** | **Yes** | Confirms cloud download from 1.3. |

Click **Confirm**, then **Next** on the settings summary.

## 1.6 Screen: "Ready to reset this PC"

It lists what's about to happen:

```
Resetting will:
  • Remove all personal files and user accounts from this PC
  • Remove any apps and programs that didn't come with this PC
  • Remove any changes made to settings
  • Install a fresh copy of Windows
```

There may be a **View apps that will be removed** link — worth one glance to confirm
nothing surprising is on there.

Click **Reset**.

## 1.7 What happens next — do not interrupt

1. Screen goes blue: **"Preparing to reset"** — a few minutes
2. Machine reboots on its own
3. **"Downloading Windows"** — percentage counter, ~7 min on 100 Mbps
4. **"Resetting this PC"** — 0% to 100%, this is the long one, 30–60 min
5. Reboots again
6. **"Installing Windows"** — spinning dots, several reboots, 15–30 min
7. Lands on the language/region screen

**Total: 60–100 minutes.** The screen may sit at one percentage for ten minutes — that's
normal. **Do not power off. Do not close the lid.**

---

# PHASE 2 — First boot (OOBE), screen by screen

Each screen below appears in roughly this order. Exact wording varies slightly by
Windows build.

| # | Screen | What to do |
|---|---|---|
| 1 | "Is this the right country or region?" | **India** → Yes |
| 2 | "Is this the right keyboard layout?" | **English (India)** or **US** → Yes |
| 3 | "Want to add a second keyboard layout?" | **Skip** |
| 4 | "Let's connect you to a network" | Pick your WiFi, enter password → Next |
| 5 | "Checking for updates" | Automatic. May reboot once. Wait. |
| 6 | License agreement | **Accept** |
| 7 | "Let's name your device" | Type something like `SHUBHAM-PC`, or **Skip for now** |
| 8 | "How would you like to set up this device?" | **Set up for personal use** |
| 9 | "Let's add your Microsoft account" | Sign in with your email |
| 10 | Password | **Your account password, not the old PIN** |
| 11 | "Create a PIN" | Click **Create PIN**, set a new one |
| 12 | "Restore from a PC backup?" | ⚠️ **Set up as new PC** — do NOT restore, it brings back the clutter |
| 13 | **Privacy settings** | See below — turn them all off |
| 14 | "Customize your experience" | **Skip** — don't tick any category |
| 15 | "Link your phone" | **Skip** — add it later from Settings if you want |
| 16 | "Back up your files with OneDrive" | **Only save files to this PC** |
| 17 | "Microsoft 365 free trial" | **Decline** / No thanks |
| 18 | "Game Pass" | **Skip** |
| 19 | Copilot / Recall prompt | **Skip** or Not now |

## Screen 13 in detail — privacy toggles

Set every one of these to **Off**:

- [ ] Location — **Off**
- [ ] Find my device — **Off** (turn on later if you want it)
- [ ] Send diagnostic data — **Required only** (this one is a choice, not a toggle)
- [ ] Improve inking and typing — **Off**
- [ ] Tailored experiences — **Off**
- [ ] Advertising ID — **Off**

Click **Accept**.

> These aren't just privacy — several of them run background telemetry services that
> contributed to the `svchost` load on your old install.

After the last screen you'll see "This might take a few minutes" and then the desktop.

---

# PHASE 3 — Immediately after first desktop (15 min)

## 3.1 Confirm you're on a clean install

```powershell
winver                                  # note the build number
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" |
  ForEach-Object { "{0} free {1:N1} GB of {2:N1} GB" -f $_.DeviceID,
    ($_.FreeSpace/1GB), ($_.Size/1GB) }
```

You should have **380+ GB free of 447**. If it's much less, the old data wasn't removed.

## 3.2 Turn off startup apps before installing anything

```
Settings  →  Apps  →  Startup
```

Turn **Off** everything except Windows Security. Do this now, before you install anything,
so nothing sneaks in later.

## 3.3 Check the Disk 1 errors are gone

```powershell
Get-Disk | Format-Table Number,FriendlyName,BusType,Size,OperationalStatus,HealthStatus -AutoSize
```

You should now see **only Disk 0** (the Samsung NVMe) with nothing plugged in. If a
**Disk 1** still appears with nothing connected, that's your card reader — and it's the
thing that was throwing 40 I/O errors. Note it and see 8.1.

---

# PHASE 4 — Windows Update (45–60 min)

**Do this before drivers.** Windows Update supplies many drivers itself and will
overwrite manually-installed ones if you do it the other way round.

```
Settings  →  Windows Update  →  Check for updates
```

- [ ] Install everything offered
- [ ] **Restart** when prompted
- [ ] Check for updates **again**
- [ ] Repeat until it reports "You're up to date" **twice in a row** — usually 2–3 rounds
- [ ] Then: **Advanced options → Optional updates → Driver updates** → tick all → Download & install
- [ ] Restart

Verify:

```powershell
Get-PnpDevice | Where-Object Status -ne 'OK' |
  Format-Table FriendlyName, Status, Class -AutoSize
```

Note what's still missing — the next phase fixes it.

---

# PHASE 5 — Drivers, with exact download paths (60 min)

**Install in this order.** Chipset first is not optional on a Ryzen machine.

## 5.1 ASUS drivers — easiest route first

### Option A — MyASUS (recommended)

1. Open **Microsoft Store**
2. Search **MyASUS** → **Install**
3. Open MyASUS → **Customer Support** → **Live Update**
4. It auto-detects your model and lists every driver and BIOS update
5. Install everything under **Driver & Utility**
6. Restart

This is the least error-prone path — no model numbers to type, no wrong downloads.

### Option B — manual, from the ASUS site

1. Go to **https://www.asus.com/support/**
2. Enter your model from step 0.1 in the search box
3. Choose **Driver & Utility** → **Driver & Tools**
4. Select **Windows 11 64-bit**
5. Download and install in this order, restarting after chipset:

| Category | Typical file name | Notes |
|---|---|---|
| **Chipset** | `AMD_Chipset_Driver_Win11.exe` | **Install first** |
| Card Reader | `Realtek_CardReader_Win11.exe` | Relevant to your Disk 1 errors |
| Audio | `Realtek_Audio_Driver_Win11.exe` | |
| Touchpad | `ASUS_Precision_Touchpad_Win11.exe` | |
| WiFi / Bluetooth | `MediaTek_WiFi_Win11.exe` or `Intel_WiFi_Win11.exe` | Skip if already working |
| ATK Package | `ASUS_ATKPackage.exe` | Function keys, brightness keys |

> **Armoury Crate — skip it.** It was five processes and a heavy background service on
> your old install. Only install it if you specifically need custom fan curves. MyASUS
> covers the basics far more cheaply.

## 5.2 AMD chipset — if ASUS didn't provide it

The ASUS-packaged chipset driver is preferred on a laptop because it includes
vendor-specific power tuning. Use AMD's only if ASUS has none.

1. **https://www.amd.com/en/support/download/drivers.html**
2. Choose **Processors** → **Processors with Radeon Graphics** →
   pick your Ryzen 7000 series → **Submit**
3. Select **Windows 11 - 64-Bit Edition**
4. Under **Chipset**, download — file is named like
   `amd_chipset_software_7.xx.xx.xxx.exe` (~50 MB)
5. Run it → **Install** → Restart

Verify afterwards:

```powershell
Get-CimInstance Win32_PnPSignedDriver |
  Where-Object { $_.DeviceName -like "*AMD*" -and $_.DeviceName -like "*chipset*" } |
  Select-Object DeviceName, DriverVersion
```

Also confirm your power plan didn't revert:

```powershell
powercfg /getactivescheme      # should be Balanced or Performance, not Power saver
```

## 5.3 NVIDIA — RTX 2050

1. **https://www.nvidia.com/en-us/drivers/**
2. Fill the form exactly:

| Field | Value |
|---|---|
| Product Type | **GeForce** |
| Product Series | **GeForce RTX 20 Series (Notebooks)** |
| Product | **GeForce RTX 2050** |
| Operating System | **Windows 11** |
| Download Type | **Studio Driver (SD)** |
| Language | English (US) |

3. **Search** → **Download**
4. File is named like:
   `5xx.xx-notebook-win11-win10-64bit-international-nsd-whql.exe` (~600 MB)

> **Studio vs Game Ready:** Studio drivers ship less often and are tested for stability
> rather than day-one game support. On a machine you use for development and CUDA
> (Ollama), Studio is the better choice.

### Installing it properly

1. Run the `.exe`
2. Extract path → **OK** (extracts to `C:\NVIDIA\...`, cleaned up afterwards)
3. **"NVIDIA Graphics Driver"** — **not** "Graphics Driver and GeForce Experience"
4. **Agree and Continue**
5. Choose **Custom (Advanced)** → **Next**
6. Component list — untick everything except:
   - ✅ **Graphics Driver**
   - ✅ **PhysX System Software**
   - ❌ GeForce Experience
   - ❌ USB-C driver (unless you use a Thunderbolt display)
7. ✅ **Tick "Perform a clean installation"**
8. **Next** — screen will flicker several times
9. Restart

Verify:

```powershell
nvidia-smi
```

You want: driver version listed, `NVIDIA GeForce RTX 2050`, and **~0–200 MiB used** at
idle on a clean desktop. Your old install idled at 681 MiB because of the GeForce
Experience overlay.

## 5.4 Optional — Samsung NVMe

Only worth it if you want firmware updates or health monitoring.

**https://semiconductor.samsung.com/consumer-storage/support/tools/** → **Samsung Magician**

Install, open, check **Drive Health** and **Firmware**. Then close it — don't let it
autostart.

## 5.5 Final driver verification

```powershell
Get-PnpDevice | Where-Object Status -ne 'OK' |
  Format-Table FriendlyName, Status, Class -AutoSize
```

**Empty output = every device has a working driver.** If anything remains, note the
`FriendlyName` and search it on the ASUS support page.

---

# PHASE 6 — System tuning (15 min)

## 6.1 Page file — your old one was 18 GB with a 3 GB peak

1. Press `Win + R` → type `sysdm.cpl` → Enter
2. **Advanced** tab → under Performance click **Settings**
3. **Advanced** tab → under Virtual memory click **Change**
4. **Untick** "Automatically manage paging file size for all drives"
5. Select **C:** → choose **Custom size**
6. Initial size: **8192** · Maximum size: **8192**
7. **Set** → **OK** → **OK** → Restart

Reclaims about 10 GB permanently.

## 6.2 Hibernation — optional, reclaims ~6 GB

```powershell
# Run PowerShell AS ADMINISTRATOR
powercfg /h off
```

> This also disables **Fast Startup**. On a laptop, hibernate is genuinely useful — only
> do this if you want the 6 GB more than you want hibernate.

## 6.3 Storage Sense — stops Downloads reaching 38 GB again

```
Settings  →  System  →  Storage  →  Storage Sense  →  On
```

Then click into it:

- Delete temporary files: **On**
- Run Storage Sense: **Every week**
- Delete files in Recycle Bin after: **30 days**
- Delete files in Downloads if unopened for: **Never**
  *(set to 60 days only if you're confident — it deletes without asking)*

---

# PHASE 7 — Restore your data

## 7.1 TeraBox

1. **https://www.terabox.com/** → Download → Windows desktop app
2. Install, sign in
3. Download your backup into a staging folder: `C:\_restore`

> Use the desktop app, **not** the browser. Browser downloads of 100 GB fail silently
> with no resume.

## 7.2 Verify before you move anything

- [ ] Play a video all the way through — not just the first second
- [ ] Open an Audition project
- [ ] Play a call recording
- [ ] Open a document

Only then move files into place:

| From `C:\_restore` | To |
|---|---|
| Videos | `C:\Users\<you>\Videos` |
| Audition projects | `C:\Users\<you>\Documents\Adobe\Audition` |
| Call recordings | `C:\Users\<you>\Documents\Recordings` |
| Development | `C:\Development` |

## 7.3 Browsers

1. Install Chrome (Phase 8)
2. Sign in → sync restores bookmarks, passwords, extensions, history
3. Nothing to copy by hand

## 7.4 Photos — fix this properly

Your photos survived only because they happened to be on the phone. On the phone:
**Google Photos → Settings → Backup → On**. Then a laptop wipe is never frightening again.

---

# PHASE 8 — Applications (30 min)

```powershell
winget install --id Google.Chrome           --silent
winget install --id 7zip.7zip               --silent
winget install --id VideoLAN.VLC            --silent
winget install --id Notepad++.Notepad++     --silent
winget install --id Microsoft.PowerToys     --silent
```

Then whatever else you use day to day.

## Deliberately not reinstalling

| Skip | Why |
|---|---|
| **AUTOMATIC1111 / Stable Diffusion** | 7.9 GB, and it starves Ollama on a 4 GB card |
| **Office and Audition from those Downloads zips** | Check what your Microsoft account already includes; LibreOffice is free |
| **Armoury Crate** | Five processes for fan curves you probably don't adjust |
| **GeForce Experience** | Was idling 344 MB across five processes |
| **AnyDesk at startup** | Install if you need it, but untick autostart |
| **Torrent clients** | Not on the machine you also do dev work on |

---

# PHASE 9 — Dev environment

```powershell
winget install --id Git.Git --silent
```

Close and reopen the terminal, then:

```powershell
mkdir C:\Development
cd C:\Development
git clone https://github.com/shubhamrk2/engineering-roadmap.git
cd engineering-roadmap
notepad SETUP-STEPS.md
```

Follow **`SETUP-STEPS.md`** end to end — 21 steps with every reboot point marked.

## Two deliberate changes from last time

**`.wslconfig` — 6 GB, not 8.** Your WSL peaked at 215 MB of actual usage, so 8 GB was
reserving headroom you never touched:

```
[wsl2]
memory=6GB
processors=4
swap=2GB
localhostForwarding=true
nestedVirtualization=true
vmIdleTimeout=60000
```

**Docker Desktop — untick "Start Docker Desktop when you sign in."** It hung twice in
14 days on the old install. Launch it from `START.md` when you need it.

## Ollama — sized for your 4 GB card

```bash
ollama pull qwen2.5:3b
ollama pull qwen2.5-coder:3b
ollama pull nomic-embed-text
```

Then:

```powershell
[Environment]::SetEnvironmentVariable("OLLAMA_MAX_LOADED_MODELS", "1", "User")
[Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL",      "1", "User")
```

See `ai.html#zerocost` for why these sizes and not the 7B/8B models.

---

# PHASE 10 — Watch for the disk errors

## 10.1 After a few days of normal use

```powershell
Get-WinEvent -FilterHashtable @{LogName='System'; Id=154} -MaxEvents 20 -ErrorAction SilentlyContinue |
  Format-Table TimeCreated, Message -Wrap
```

**Nothing returned** → it was software. You're done.

**Errors return** → it's hardware, and the reset was never going to fix it:

1. Identify which device:
   ```powershell
   Get-Disk | Format-Table Number,FriendlyName,BusType,OperationalStatus,HealthStatus -AutoSize
   Get-PnpDevice -Class DiskDrive | Format-Table FriendlyName, Status, InstanceId -AutoSize
   ```
2. If it's the **SD card reader**:
   `Device Manager → Memory technology devices` (or Disk drives) → right-click →
   **Disable device**. Costs you nothing unless you use SD cards.
3. If it's the **internal NVMe** → back up immediately and get it serviced under warranty.

## 10.2 Baseline the healthy machine

```powershell
cd C:\Development\engineering-roadmap
powershell -ExecutionPolicy Bypass -File .\tools\why-slow.ps1 > fresh-baseline.txt
```

On a healthy fresh install expect:

- C: **60%+ free**
- Commit charge **well under** 15.8 GB
- **No Event 154**
- Startup list **under 5 items**
- `Get-PnpDevice` all OK

**Keep `fresh-baseline.txt`.** In six months when it feels slow, diff against this rather
than guessing.

---

# Habits that stop this recurring

| Habit | Why it matters here |
|---|---|
| Empty **Downloads** monthly | Yours reached 38 GB, mostly films already watched |
| `docker system prune -a` monthly | Was holding 6.8 GB |
| Keep C: **above 15% free** | Below that Windows genuinely stalls |
| Check **Startup apps** after every install | Most installers add themselves silently |
| Phone media in **Google Photos** | So the next wipe is boring |
| Run `why-slow.ps1` when it feels slow | It found the disk errors that guessing missed |
