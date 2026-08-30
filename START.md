# After Reboot — Starting Everything

> Run through this every time you restart your personal laptop.
> Steps 1–2 are manual (Windows). Step 3 onwards is handled by the script.

---

## Step 1 — Start Docker Desktop (Windows, manual)

1. Open **Docker Desktop** from the Start menu or taskbar
2. Wait until the whale icon in the taskbar **stops animating** and turns solid
3. If it prompts to update, click **Skip** — update separately when you have time

> Docker Desktop must be fully running before you open WSL, otherwise `docker` commands will hang.

**Optional — make it start automatically on login:**
- Docker Desktop → Settings → General → tick **"Start Docker Desktop when you sign in"**
- This skips Step 1 entirely on future reboots

---

## Step 2 — Open WSL (Windows, manual)

Open **Windows Terminal** → click the dropdown arrow → select **Ubuntu**

Or run in PowerShell:

```powershell
wsl -d Ubuntu-24.04
```

You are now inside Linux. All remaining steps happen here.

---

## Step 3 — Run the startup script (WSL, one command)

```bash
~/code/badgedesk/tools/start.sh
```

That's it. The script does everything else:
- Waits for Docker daemon to be ready
- Starts all five Compose services (Postgres, Redis, Mongo, Kafka, Kafka UI)
- Waits for health checks to pass
- Checks SSH agent is running and your key is loaded
- Prints a final status summary

---

## What the script starts

| Service | Port | What it's for |
|---|---|---|
| postgres | 5432 | Main database — employees, badges, access requests |
| redis | 6379 | Session cache, rate limits, locks |
| mongo | 7017 | Audit event documents |
| kafka | 9092 | Event streaming between services |
| kafka-ui | 8080 | Browser UI to inspect Kafka topics |

Open **http://localhost:8080** to confirm Kafka UI is up.

---

## Optional — Start the engineering roadmap site

If you want to browse the roadmap locally:

```bash
cd /mnt/c/Users/<your-windows-username>/OneDrive\ -\ Accenture/Documents/engineering-roadmap
python3 -m http.server 8082
```

Then open **http://localhost:8082**

> Using port 8082 to avoid clashing with Kafka UI on 8080.

---

## Optional — Start Ollama (local LLM, Sheet 12)

Ollama installs as a Windows service and starts automatically on login. Nothing to do.

Verify it is up:

```bash
curl http://localhost:11434/api/tags
ollama list
```

From **inside WSL**, `localhost` is the WSL VM, not Windows. Reach the host instead:

```bash
export OLLAMA_HOST="http://$(ip route show default | awk '{print $3}'):11434"
curl $OLLAMA_HOST/api/tags
```

Confirm a model is actually on the GPU — run a prompt, then in another terminal:

```bash
ollama ps
# PROCESSOR column must read 100% GPU. Anything else means it fell back to CPU.
```

> **AUTOMATIC1111 has been removed.** On a 4 GB card it holds most of the VRAM and forces
> Ollama onto the CPU. Removal steps are in `assets/images/README.md`.

---

## Stopping everything cleanly

When you are done for the day (before shutdown, not mandatory):

```bash
cd ~/code/badgedesk
docker compose down      # stops containers, keeps data volumes
```

Or to fully wipe the data and start fresh next time:

```bash
docker compose down -v   # stops containers AND deletes volumes
```

---

## Troubleshooting

**`docker: error during connect`**
→ Docker Desktop is not running yet. Go back to Step 1 and wait for it to finish loading.

**`bind: address already in use` on port 5432 or 6379**
→ A previous Compose session did not shut down cleanly. Run:
```bash
docker compose down
docker compose up -d
```

**SSH agent not loading key / GitHub asks for password**
→ Run manually:
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
ssh -T git@github.com
```

**WSL clock drift (certificate errors after sleep)**
```bash
sudo hwclock -s
```

**Kafka UI not loading at localhost:8080**
→ Kafka takes ~30 seconds after `up -d`. Wait and refresh. Check with:
```bash
docker compose ps
docker compose logs kafka --tail 20
```
