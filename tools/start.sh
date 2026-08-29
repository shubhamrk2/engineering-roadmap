#!/usr/bin/env bash
set -euo pipefail

BADGEDESK_DIR="$HOME/code/badgedesk"
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
RESET="\033[0m"

ok()   { echo -e "${GREEN}  [OK]${RESET} $1"; }
warn() { echo -e "${YELLOW}  [!!]${RESET} $1"; }
fail() { echo -e "${RED}  [XX]${RESET} $1"; }
info() { echo -e "${CYAN}  -->${RESET} $1"; }

echo ""
echo -e "${BOLD}==============================${RESET}"
echo -e "${BOLD}  BadgeDesk — startup${RESET}"
echo -e "${BOLD}==============================${RESET}"
echo ""

# ── 1. Docker daemon ─────────────────────────────────────────────────────────
info "Waiting for Docker daemon..."
TRIES=0
until docker info >/dev/null 2>&1; do
    TRIES=$((TRIES + 1))
    if [ "$TRIES" -ge 30 ]; then
        fail "Docker daemon not ready after 60 s."
        echo ""
        echo "  Make sure Docker Desktop is open and fully loaded on Windows."
        echo "  Then re-run this script."
        exit 1
    fi
    sleep 2
done
ok "Docker daemon is up"

# ── 2. Compose services ───────────────────────────────────────────────────────
if [ ! -d "$BADGEDESK_DIR" ]; then
    fail "Directory not found: $BADGEDESK_DIR"
    echo "  Clone the repo first:  git clone git@github.com:shubhamrk2/badgedesk.git ~/code/badgedesk"
    exit 1
fi

cd "$BADGEDESK_DIR"

if [ ! -f "docker-compose.yml" ]; then
    fail "docker-compose.yml not found in $BADGEDESK_DIR"
    exit 1
fi

info "Starting Compose services..."
docker compose up -d

# ── 3. Wait for health checks ─────────────────────────────────────────────────
info "Waiting for services to become healthy (up to 60 s)..."
SERVICES=("postgres" "redis" "mongo")
DEADLINE=$((SECONDS + 60))

for SERVICE in "${SERVICES[@]}"; do
    while true; do
        STATUS=$(docker compose ps --format "{{.Service}} {{.Health}}" 2>/dev/null \
                 | grep "^$SERVICE " | awk '{print $2}' || true)
        if [ "$STATUS" = "healthy" ]; then
            ok "$SERVICE is healthy"
            break
        fi
        if [ "$SECONDS" -ge "$DEADLINE" ]; then
            warn "$SERVICE health check timed out — check logs: docker compose logs $SERVICE"
            break
        fi
        sleep 3
    done
done

# Kafka has no health check defined — just confirm it's running
KAFKA_STATE=$(docker compose ps --format "{{.Service}} {{.State}}" 2>/dev/null \
              | grep "^kafka " | awk '{print $2}' || true)
if [ "$KAFKA_STATE" = "running" ]; then
    ok "kafka is running"
else
    warn "kafka state: ${KAFKA_STATE:-unknown}"
fi

KAFKA_UI_STATE=$(docker compose ps --format "{{.Service}} {{.State}}" 2>/dev/null \
                 | grep "^kafka-ui " | awk '{print $2}' || true)
if [ "$KAFKA_UI_STATE" = "running" ]; then
    ok "kafka-ui is running  →  http://localhost:8080"
else
    warn "kafka-ui state: ${KAFKA_UI_STATE:-unknown}"
fi

# ── 4. SSH agent ──────────────────────────────────────────────────────────────
echo ""
info "Checking SSH agent..."
if ! ssh-add -l >/dev/null 2>&1; then
    warn "No keys loaded — starting agent and adding key"
    eval "$(ssh-agent -s)" >/dev/null
    ssh-add ~/.ssh/id_ed25519 2>/dev/null && ok "SSH key loaded" || warn "Could not load ~/.ssh/id_ed25519 — add it manually"
else
    ok "SSH agent running with key loaded"
fi

# ── 5. Quick connectivity check ───────────────────────────────────────────────
echo ""
info "Smoke tests..."

docker compose exec -T postgres psql -U badgedesk -d badgedesk -c "SELECT 1;" \
    >/dev/null 2>&1 && ok "Postgres answers" || warn "Postgres not responding yet"

docker compose exec -T redis redis-cli ping \
    2>/dev/null | grep -q "PONG" && ok "Redis answers" || warn "Redis not responding yet"

docker compose exec -T mongo mongosh --quiet \
    -u badgedesk -p badgedesk --authenticationDatabase admin \
    --eval "db.adminCommand('ping').ok" 2>/dev/null | grep -q "1" \
    && ok "Mongo answers" || warn "Mongo not responding yet"

# ── 6. Summary ────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}==============================${RESET}"
echo -e "${BOLD}  All services started${RESET}"
echo -e "${BOLD}==============================${RESET}"
echo ""
docker compose ps --format "table {{.Service}}\t{{.State}}\t{{.Health}}\t{{.Ports}}"
echo ""
echo -e "  Kafka UI  →  ${CYAN}http://localhost:8080${RESET}"
echo ""
