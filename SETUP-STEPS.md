# Week 00 — Personal Laptop Setup Steps

> Personal laptop only (full admin). Follow in order. Do not skip steps.

**Restart legend used in this file:**
- 🔴 **WINDOWS REBOOT** — shut down and restart the whole PC before continuing
- 🟡 **WSL RESTART** — run `wsl --shutdown` in PowerShell, then reopen WSL
- 🟢 **NEW TERMINAL** — close the current terminal window and open a fresh one
- 🔵 **SHELL RELOAD** — run `exec $SHELL -l` in the same terminal (no window close needed)

---

## Step 1 — Shell & base tools (PowerShell Admin)

```powershell
winget --version
winget install --id Microsoft.PowerShell        --source winget
winget install --id Microsoft.WindowsTerminal   --source winget
winget install --id Git.Git                     --silent
winget install --id GitHub.cli                  --silent
winget install --id Microsoft.VisualStudioCode  --silent
winget install --id 7zip.7zip                   --silent
```

> 🟢 **NEW TERMINAL** — Close this window. Open **Windows Terminal** and make sure it is running **PowerShell 7** (not Windows PowerShell 5.1). Check the tab says `pwsh` or the prompt shows `PS C:\>` with version 7+. All steps from here use this terminal.

---

## Step 2 — WSL2 (PowerShell 7, Admin)

```powershell
wsl --install
```

> 🔴 **WINDOWS REBOOT REQUIRED** — `wsl --install` will ask you to restart. Do it now. After the reboot, Ubuntu will launch automatically and ask you to create a **Linux username and password** (separate from your Windows login). Set them, remember the password — you will need it for every `sudo` command.

After reboot and Ubuntu first-run setup, continue in PowerShell:

```powershell
wsl --set-default-version 2
wsl --install --distribution Ubuntu-24.04
wsl --update
wsl --status
# Expected: Default Distribution: Ubuntu-24.04   Default Version: 2
```

---

## Step 3 — Configure WSL2

**Inside Ubuntu (open from Windows Terminal → Ubuntu tab):**

```bash
sudo nano /etc/wsl.conf
```

Paste this exactly (replace `<your-linux-username>` with the username you set above):

```
[boot]
systemd=true

[interop]
enabled=true
appendWindowsPath=true

[automount]
enabled=true
options="metadata,umask=0022,fmask=0011"

[user]
default=<your-linux-username>

[network]
generateHosts=true
generateResolvConf=true
```

Save: `Ctrl+O` → Enter → `Ctrl+X`

**On Windows — create `C:\Users\<you>\.wslconfig`** (use Notepad or VS Code):

```
[wsl2]
memory=8GB
processors=4
swap=4GB
localhostForwarding=true
nestedVirtualization=true
vmIdleTimeout=60000
```

> 🟡 **WSL RESTART** — Run this in PowerShell, then reopen Ubuntu:

```powershell
wsl --shutdown
```

Then open a new Ubuntu terminal and verify:

```bash
systemctl --version    # should work (confirms systemd is running)
```

---

## Step 4 — First Ubuntu setup (inside WSL)

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y build-essential curl git unzip ca-certificates \
                        pkg-config libssl-dev zip
mkdir -p ~/code && cd ~/code
df -hT ~/code | tail -1    # must show ext4, not 9p
```

No restart needed.

---

## Step 5 — VS Code WSL extension (PowerShell)

```powershell
code --install-extension ms-vscode-remote.remote-wsl
```

**Verify from inside WSL:**

```bash
cd ~/code
code .
# Bottom-left corner of VS Code must show: WSL: Ubuntu-24.04
# If it shows anything else, close VS Code and reopen with `code .` from inside WSL
```

No restart needed.

---

## Step 6 — Git config & SSH key (inside WSL)

```bash
git config --global user.name  "Your Name"
git config --global user.email "your-github-email@example.com"
git config --global init.defaultBranch main
git config --global pull.rebase true
git config --global fetch.prune true
git config --global core.editor "code --wait"
git config --global core.autocrlf input
git config --global rerere.enabled true

ssh-keygen -t ed25519 -C "personal-laptop-2026-08" -f ~/.ssh/id_ed25519
# Enter a passphrase when asked (recommended)

eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
```

**Add the key to GitHub:** github.com → Settings → SSH and GPG keys → New SSH key → paste the output above

```bash
ssh -T git@github.com
# Expected: Hi <username>! You've successfully authenticated...

printf '%s\n' 'eval "$(ssh-agent -s)" >/dev/null' 'ssh-add -q ~/.ssh/id_ed25519 2>/dev/null' >> ~/.bashrc
```

No restart needed.

---

## Step 7 — Node via fnm (inside WSL)

```bash
curl -fsSL https://fnm.vercel.app/install | bash
```

> 🔵 **SHELL RELOAD** — run this before continuing:

```bash
exec $SHELL -l
```

```bash
fnm install 22.11.0
fnm default 22.11.0
fnm use 22.11.0
node -v        # v22.11.0
npm -v         # 10.9.0

echo 'eval "$(fnm env --use-on-cd)"' >> ~/.bashrc

corepack enable
corepack prepare pnpm@9.12.3 --activate
pnpm -v        # 9.12.3
```

---

## Step 8 — Python 3.12 + uv (inside WSL)

```bash
sudo apt-get install -y python3.12 python3.12-venv python3-pip
python3.12 -V

curl -LsSf https://astral.sh/uv/install.sh | sh
```

> 🔵 **SHELL RELOAD** — run this before continuing:

```bash
exec $SHELL -l
uv --version
```

---

## Step 9 — Java 21 via SDKMAN (inside WSL)

```bash
sudo apt-get install -y zip unzip
curl -s "https://get.sdkman.io" | bash
```

> 🔵 **SHELL RELOAD** — SDKMAN writes to `.bashrc` and needs the shell sourced:

```bash
source "$HOME/.sdkman/bin/sdkman-init.sh"
sdk version
```

```bash
sdk install java 21.0.5-tem
sdk install maven 3.9.9
sdk install gradle 8.10.2

java -version
mvn -v | head -2
```

---

## Step 10 — Docker Desktop (PowerShell Admin)

```powershell
winget install --id Docker.DockerDesktop --silent
```

> 🔴 **WINDOWS REBOOT MAY BE REQUIRED** — Docker Desktop often prompts for a restart to finish enabling the WSL2 backend. If it asks, reboot now. If it does not ask, continue.

After reboot (or if no reboot was needed), open Docker Desktop and configure:

- Settings → General → "Use the WSL 2 based engine" ✓
- Settings → Resources → WSL Integration → "Enable integration with my default WSL distro" ✓
- Settings → Resources → WSL Integration → Ubuntu-24.04 ✓
- Click **Apply & Restart** inside Docker Desktop

> 🟡 **WSL RESTART** — After clicking Apply & Restart in Docker Desktop, also run in PowerShell:

```powershell
wsl --shutdown
```

Then open Ubuntu and verify:

```bash
docker version
docker run --rm hello-world
docker compose version
```

---

## Step 11 — AWS CLI v2 with SSO (inside WSL)

```bash
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
unzip -q awscliv2.zip && sudo ./aws/install && rm -rf aws awscliv2.zip
aws --version

aws configure sso
# SSO session name: badgedesk
# SSO start URL: <your Identity Center URL>
# SSO region: ap-south-1
# CLI default region: ap-south-1
# CLI profile name: badgedesk-admin

aws sso login --profile badgedesk-admin
aws sts get-caller-identity --profile badgedesk-admin

export AWS_PROFILE=badgedesk-admin
```

No restart needed.

---

## Step 12 — Azure CLI (inside WSL)

```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az version --output table
az login
az account show --output table

az group create --name rg-badgedesk-dev --location centralindia
az configure --defaults group=rg-badgedesk-dev location=centralindia
```

No restart needed.

---

## Step 13 — Terraform via tfenv (inside WSL)

```bash
git clone --depth 1 https://github.com/tfutils/tfenv.git ~/.tfenv
echo 'export PATH="$HOME/.tfenv/bin:$PATH"' >> ~/.bashrc
```

> 🔵 **SHELL RELOAD:**

```bash
exec $SHELL -l

tfenv install 1.9.8
tfenv use 1.9.8
terraform version    # Terraform v1.9.8
```

---

## Step 14 — kubectl and kind (inside WSL)

```bash
curl -fsSLO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && rm kubectl
kubectl version --client

curl -fsSLo ./kind https://kind.sigs.k8s.io/dl/v0.24.0/kind-linux-amd64
sudo install -o root -g root -m 0755 kind /usr/local/bin/kind && rm kind

kind create cluster --name badgedesk
kubectl cluster-info --context kind-badgedesk
kubectl get nodes
```

No restart needed.

---

## Step 15 — Database clients (inside WSL)

```bash
sudo apt-get install -y curl gnupg lsb-release
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
  | sudo gpg --dearmor -o /usr/share/keyrings/pgdg.gpg
echo "deb [signed-by=/usr/share/keyrings/pgdg.gpg] \
http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
  | sudo tee /etc/apt/sources.list.d/pgdg.list >/dev/null
sudo apt-get update
sudo apt-get install -y postgresql-client-16 redis-tools

psql --version
redis-cli --version

curl -fsSL https://pgp.mongodb.com/server-7.0.asc \
  | sudo gpg --dearmor -o /usr/share/keyrings/mongodb-7.gpg
echo "deb [signed-by=/usr/share/keyrings/mongodb-7.gpg] \
https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/7.0 multiverse" \
  | sudo tee /etc/apt/sources.list.d/mongodb-7.list >/dev/null
sudo apt-get update && sudo apt-get install -y mongodb-mongosh
```

**MongoDB Compass (optional GUI) — PowerShell:**

```powershell
winget install MongoDB.Compass.Full
```

No restart needed.

---

## Step 16 — VS Code extensions (inside WSL)

```bash
for ext in \
  ms-python.python ms-python.vscode-pylance charliermarsh.ruff \
  dbaeumer.vscode-eslint esbenp.prettier-vscode \
  bradlc.vscode-tailwindcss \
  ms-azuretools.vscode-docker ms-kubernetes-tools.vscode-kubernetes-tools \
  hashicorp.terraform \
  humao.rest-client ckolkman.vscode-postgres \
  ms-vscode-remote.remote-wsl eamodio.gitlens \
  redhat.vscode-yaml graphql.vscode-graphql
do
  code --install-extension "$ext"
done
```

No restart needed.

---

## Step 17 — Clone badgedesk repo (inside WSL)

```bash
cd ~/code
git clone git@github.com:shubhamrk2/badgedesk.git
cd badgedesk
cp .env.example .env
```

No restart needed.

---

## Step 18 — Bring up the local platform (inside WSL)

Create `docker-compose.yml` in `~/code/badgedesk/` with the full Compose file from setup.html §4, then:

```bash
docker compose up -d
docker compose ps       # all five services should show healthy
docker compose exec postgres psql -U badgedesk -d badgedesk -c "select version();"
docker compose exec redis redis-cli ping                    # PONG
docker compose exec mongo mongosh --quiet -u badgedesk -p badgedesk \
  --authenticationDatabase admin --eval "db.adminCommand('ping')"
# Open http://localhost:8080 for Kafka UI
```

No restart needed.

---

## Step 19 — AWS account setup (browser)

1. Create AWS account at aws.amazon.com
2. Enable MFA on root user, then stop using root
3. Billing → Budgets → Create budget → $10/month → alert at 50%, 80%, 100%
4. Billing Preferences → tick "Receive Free Tier alerts"
5. Enable IAM Identity Center → create an administrator user for yourself
6. Pick region `ap-south-1` (Mumbai)
7. Run `aws configure sso` (Step 11 above)

---

## Step 20 — Verification script (PowerShell)

Save this as `tools/check-machine.ps1` in the badgedesk repo, then run it:

```powershell
$checks = [ordered]@{
  'git'       = { git --version }
  'node'      = { node --version }
  'npm'       = { npm --version }
  'python'    = { python --version }
  'java'      = { java -version 2>&1 | Select-Object -First 1 }
  'docker'    = { docker --version }
  'compose'   = { docker compose version }
  'aws'       = { aws --version }
  'az'        = { az version --output tsv 2>$null | Select-Object -First 1 }
  'terraform' = { terraform version | Select-Object -First 1 }
  'kubectl'   = { kubectl version --client=true -o yaml | Select-String gitVersion }
  'wsl'       = { wsl --status }
}

foreach ($name in $checks.Keys) {
  try {
    $out = & $checks[$name] 2>$null
    if ($out) { "{0,-10} OK   {1}" -f $name, ($out -join ' ').Trim() }
    else      { "{0,-10} MISSING" -f $name }
  } catch { "{0,-10} MISSING" -f $name }
}

docker compose ps --format "{{.Service}} {{.Status}}"
```

**Expected output:**

```
git        OK   git version 2.x
node       OK   v22.11.0
npm        OK   10.9.0
python     OK   Python 3.12.x
java       OK   openjdk version "21.0.x"
docker     OK   Docker version 27.x
compose    OK   Docker Compose version v2.x
aws        OK   aws-cli/2.x
az         OK   2.x
terraform  OK   Terraform v1.9.8
kubectl    OK   gitVersion: v1.31.x
wsl        OK   Default Distribution: Ubuntu-24.04  Default Version: 2

postgres   Up (healthy)
redis      Up (healthy)
mongo      Up (healthy)
kafka      Up
kafka-ui   Up
```

---

## Step 21 — Final commit (proves the loop works)

```bash
cd ~/code/badgedesk
git commit --allow-empty -m "chore: week 00 personal laptop ready"
git push
```

---

## Restart summary — all the times you had to stop

| After step | What to do | Why |
|---|---|---|
| Step 1 | 🟢 Open new Windows Terminal (PowerShell 7) | Old terminal was still on PowerShell 5 |
| Step 2 (`wsl --install`) | 🔴 **Full Windows reboot** | WSL2 kernel must be registered at boot |
| Step 3 (wsl.conf) | 🟡 `wsl --shutdown` in PowerShell | New config is only read when VM restarts |
| Step 7 (fnm install) | 🔵 `exec $SHELL -l` | fnm added itself to `.bashrc` |
| Step 8 (uv install) | 🔵 `exec $SHELL -l` | uv added itself to `.bashrc` |
| Step 9 (SDKMAN) | 🔵 `source ~/.sdkman/bin/sdkman-init.sh` | SDKMAN init must be sourced |
| Step 10 (Docker Desktop) | 🔴 **Reboot if prompted** + 🟡 `wsl --shutdown` | Docker needs WSL integration applied |
| Step 13 (tfenv) | 🔵 `exec $SHELL -l` | tfenv PATH added to `.bashrc` |

---

## Sign-off checklist

- [ ] WSL2 installed with systemd enabled, badgedesk repo lives in `~/code` (not `/mnt/c`)
- [ ] `ssh -T git@github.com` greets me by username
- [ ] `node --version` → v22.11.0
- [ ] `python3.12 -V` → Python 3.12.x
- [ ] `java -version` → 21.x
- [ ] `docker run --rm hello-world` succeeds
- [ ] `docker compose up -d` → all five services healthy
- [ ] Connected to Postgres, Redis, Mongo and Kafka UI at http://localhost:8080
- [ ] AWS account with root MFA + $10 budget alarm confirmed by email
- [ ] Azure free account + `az login` works
- [ ] `check-machine.ps1` is all green
- [ ] Empty commit pushed from this machine to badgedesk repo
