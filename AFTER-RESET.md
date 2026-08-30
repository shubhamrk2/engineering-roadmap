# After the Reset — Getting Back to Normal

> Personal laptop (ASUS, Ryzen 7000, RTX 2050, Samsung NVMe).
> Do these in order. Phases 1–4 are Windows; Phase 6 hands off to `SETUP-STEPS.md`.
> Total: about a day, most of it unattended downloads.

---

## Phase 1 — First boot (20 min)

Windows walks you through setup (OOBE).

- [ ] **Region:** India · **Keyboard:** English (India) or US
- [ ] **Network:** connect to WiFi — needed for updates
- [ ] **Account:** sign in with your **Microsoft account**
      (keeps Phone Link, OneDrive and settings sync working — you already use all three)
- [ ] **PIN:** set one
- [ ] **Privacy toggles:** turn everything **Off** — location, diagnostics, tailored ads,
      advertising ID. None of it helps you and some of it runs background services.
- [ ] **Skip** every "customise your experience" and OneDrive backup prompt for now
- [ ] **Skip** Microsoft 365 trial

> Do **not** restore anything yet. Get Windows healthy first.

---

## Phase 2 — Updates and drivers (60–90 min)

**Order matters here.** Chipset before GPU, always.

### 2.1 Windows Update — run it to exhaustion

```
Settings → Windows Update → Check for updates
```

- [ ] Install everything, reboot, **check again**
- [ ] Repeat until it says you're up to date twice in a row (usually 2–3 rounds)
- [ ] **Advanced options → Optional updates → Driver updates** → install all

### 2.2 AMD chipset driver — do this before the GPU

The single most important driver on a Ryzen laptop. It controls power management and
core parking; without it the machine feels sluggish under load.

- [ ] Download from **amd.com/support** → your Ryzen 7000 series → Chipset
- [ ] Install, reboot

### 2.3 NVIDIA driver

- [ ] **nvidia.com/drivers** → RTX 2050 → **Game Ready** or **Studio** (Studio is more stable)
- [ ] Choose **Custom install → Clean installation**
- [ ] Untick **GeForce Experience** unless you actually want the overlay —
      it was running five processes and 344 MB on your old install

### 2.4 ASUS drivers

- [ ] **asus.com/support** → enter your model → Driver & Tools
- [ ] Install: audio (Realtek), touchpad, card reader, WiFi/Bluetooth if not already covered
- [ ] **Armoury Crate — skip it unless you need fan curves.** It was one of your heaviest
      background processes. MyASUS from the Store is lighter if you want fan control.

### 2.5 Verify

```powershell
Get-PnpDevice | Where-Object Status -ne 'OK' |
  Format-Table FriendlyName, Status, Class -AutoSize
```

Empty output means every device has a working driver.

```powershell
nvidia-smi          # GPU detected, ~0 MiB used at idle
winver              # confirm the build
```

---

## Phase 3 — Fix what caused the problem (10 min)

### 3.1 The Disk 1 I/O errors

Your old install logged **40 hardware I/O failures on Disk 1** in 14 days. A reset does not
fix hardware. Check whether it came back:

```powershell
Get-Disk | Format-Table Number,FriendlyName,BusType,Size,OperationalStatus,HealthStatus -AutoSize

Get-WinEvent -FilterHashtable @{LogName='System'; Id=154} -MaxEvents 10 -ErrorAction SilentlyContinue |
  Format-Table TimeCreated, Message -Wrap
```

- **No Event 154 after a few days of use** → it was software, you're clear
- **Errors return** → it is the hardware. If Disk 1 is the SD card reader:
  `Device Manager → Disk drives / Memory technology devices → right-click → Disable`
- **If Disk 1 is an internal drive** → get it serviced. Do not ignore this.

### 3.2 Page file — your old one was 18 GB with a 3 GB peak

```
System Properties → Advanced → Performance Settings → Advanced
  → Virtual memory → Change → uncheck "Automatically manage"
  → Custom size: Initial 8192  Maximum 8192 → Set → OK
```

Reclaims ~10 GB permanently.

### 3.3 Hibernation — optional

```powershell
# Run as Administrator. Reclaims ~6 GB, but disables Fast Startup and hibernate.
# On a laptop hibernate is genuinely useful — only do this if you want the space.
powercfg /h off
```

### 3.4 Keep startup lean from day one

```
Settings → Apps → Startup
```

Turn **Off** everything except your antivirus. Specifically leave off: Teams, Phone Link,
Edge auto-launch, TeraBox, AnyDesk, torrent clients, Docker Desktop. Start them manually.
This is what quietly ate your old install.

---

## Phase 4 — Restore your data (varies)

- [ ] Install **TeraBox desktop app** — not the browser, it has no resume
- [ ] Download your backup to a staging folder first, e.g. `C:\_restore`
- [ ] **Open a few files before deleting the cloud copy** — a video, a document, a recording
- [ ] Then move into place:
      - Videos → `C:\Users\<you>\Videos`
      - Audition projects → `Documents\Adobe\Audition`
      - `Development` → `C:\Development`
- [ ] Photos: your phone has them. Consider **Google Photos backup** on the phone so you
      never depend on a laptop copy again.

### Browsers

- [ ] Chrome → sign in → sync restores bookmarks, passwords, extensions
- [ ] Nothing to copy manually

---

## Phase 5 — Personal apps (30 min)

```powershell
winget install --id Google.Chrome
winget install --id 7zip.7zip
winget install --id VideoLAN.VLC
winget install --id Notepad++.Notepad++
```

Then whatever else you actually use.

**Do not reinstall:**
- **Stable Diffusion / AUTOMATIC1111** — 7.9 GB, and it starves Ollama on a 4 GB card
- **Adobe Audition and Office from those Downloads zips** — if you need Office,
  your Microsoft account may already include it, and LibreOffice is free
- Torrent clients on the machine you also do dev work on

---

## Phase 6 — Dev environment

Follow **`SETUP-STEPS.md`** end to end. It has the reboot points marked.

```powershell
winget install --id Git.Git --silent
mkdir C:\Development
cd C:\Development
git clone https://github.com/shubhamrk2/engineering-roadmap.git
notepad engineering-roadmap\SETUP-STEPS.md
```

### Two changes from last time

**`.wslconfig` — 6 GB, not 8.** Your WSL only ever used 215 MB, and 6 GB leaves Windows
more headroom:

```
[wsl2]
memory=6GB
processors=4
swap=2GB
localhostForwarding=true
nestedVirtualization=true
vmIdleTimeout=60000
```

**Docker Desktop — untick "Start when you sign in."** Launch it from `START.md` when you
need it. It hung twice on your old install.

### Ollama (Sheet 12)

```bash
ollama pull qwen2.5:3b
ollama pull qwen2.5-coder:3b
ollama pull nomic-embed-text
```

Sized for your 4 GB card. See `ai.html#zerocost` for why.

---

## Phase 7 — Habits that stop this recurring

| Habit | Why |
|---|---|
| Empty **Downloads** monthly | Yours reached 38 GB, mostly films you'd watched |
| `docker system prune -a` monthly | Reclaims several GB |
| Keep **C: above 15% free** | Below that Windows genuinely starts to stall |
| Check **Startup apps** after installing anything | Most installers add themselves silently |
| Media on the phone **and** in Google Photos | So a laptop wipe is never scary again |
| Run `tools/why-slow.ps1` if it feels slow | Beats guessing — it found the disk errors |

---

## Final check

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\tools\why-slow.ps1 > fresh.txt
```

On a healthy fresh install you should see:

- C: **60%+ free**
- Commit charge **well under** 15.8 GB
- **No Event 154** disk errors
- Startup list **under 5 items**
- `Get-PnpDevice` status all OK

Keep `fresh.txt`. When the machine feels slow in six months, diff against it.
