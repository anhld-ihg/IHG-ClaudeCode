#!/bin/bash
# Cai dat Telegram Bot cho IHG tren VPS
# Cach dung:
#   export TELEGRAM_BOT_TOKEN=<token>
#   bash install-vps.sh
set -e

BOT_DIR="$HOME/telegram-bot"
WS_DIR="$HOME/IHG-ClaudeCode"
REPO="https://github.com/anhld-ihg/IHG-ClaudeCode.git"

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
  echo "LOI: Chua dat TELEGRAM_BOT_TOKEN."
  echo "Hay chay: export TELEGRAM_BOT_TOKEN=<token cua ban> roi chay lai script nay."
  exit 1
fi

echo "[1/7] Tao thu muc bot..."
mkdir -p "$BOT_DIR"

echo "[2/7] Clone / cap nhat kho tri thuc IHG..."
if [ -d "$WS_DIR/.git" ]; then
  git -C "$WS_DIR" pull --ff-only 2>&1 | tail -2 || echo "CANH BAO: pull that bai, dung ban clone hien tai"
else
  git clone --depth 1 "$REPO" "$WS_DIR" 2>&1 | tail -2
fi

echo "[3/7] Copy bot.js tu repo..."
cp "$WS_DIR/telegram-bot/bot.js" "$BOT_DIR/bot.js"

echo "[4/7] Tao file .env..."
cat > "$BOT_DIR/.env" << ENVEOF
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
CLAUDE_WORKDIR=$WS_DIR
ENVEOF
chmod 600 "$BOT_DIR/.env"

echo "[5/7] Cai dat npm packages..."
cd "$BOT_DIR"
[ -f package.json ] || npm init -y > /dev/null 2>&1
npm install node-telegram-bot-api dotenv --no-audit --no-fund 2>&1 | tail -3

echo "[6/7] Tao systemd service..."
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/telegram-bot.service" << SVCEOF
[Unit]
Description=IHG Telegram Bot (Claude Code)
After=network-online.target

[Service]
Type=simple
WorkingDirectory=$BOT_DIR
ExecStart=/usr/bin/node $BOT_DIR/bot.js
Restart=always
RestartSec=10
Environment=NODE_ENV=production
StandardOutput=append:$BOT_DIR/bot.log
StandardError=append:$BOT_DIR/bot.log

[Install]
WantedBy=default.target
SVCEOF

systemctl --user daemon-reload
systemctl --user enable telegram-bot.service 2>&1 | tail -1
systemctl --user restart telegram-bot.service

echo "[7/7] Kiem tra trang thai..."
sleep 5
systemctl --user status telegram-bot.service --no-pager -l 2>&1 | head -15

echo ""
echo "=== HOAN TAT ==="
echo "Theo doi log : journalctl --user -u telegram-bot -f"
echo "Khoi dong lai: systemctl --user restart telegram-bot"
echo "Dung bot     : systemctl --user stop telegram-bot"
