#!/usr/bin/env bash
# Установка или обновление бота на Ubuntu/Debian. Запускать от root:
#   bash deploy/install.sh
# Бот живёт в /opt/dietbot под отдельным пользователем и не трогает
# другие сайты и боты на сервере.
set -euo pipefail

REPO_URL="https://github.com/golarrdo-cmyk/OPUS.git"
BRANCH="${BRANCH:-claude/opus-5-5-github-check-69dpf2}"
DIR=/opt/dietbot

apt-get update -qq && apt-get install -y -qq git python3 python3-venv >/dev/null
id dietbot >/dev/null 2>&1 || useradd --system --home "$DIR" --shell /usr/sbin/nologin dietbot

if [ -d "$DIR/.git" ]; then
    git -C "$DIR" fetch -q origin "$BRANCH" && git -C "$DIR" checkout -q -B "$BRANCH" "origin/$BRANCH"
else
    git clone -q -b "$BRANCH" "$REPO_URL" "$DIR"
fi

python3 -m venv "$DIR/.venv"
"$DIR/.venv/bin/pip" install -q -r "$DIR/requirements.txt"

if [ ! -f "$DIR/.env" ]; then
    cp "$DIR/.env.example" "$DIR/.env"
    sed -i "s|^DB_PATH=.*|DB_PATH=$DIR/dietbot.sqlite3|" "$DIR/.env"
    echo "Заполните BOT_TOKEN и ANTHROPIC_API_KEY в $DIR/.env и запустите скрипт ещё раз."
    chown -R dietbot:dietbot "$DIR"; chmod 600 "$DIR/.env"
    exit 0
fi

chown -R dietbot:dietbot "$DIR"; chmod 600 "$DIR/.env"
cp "$DIR/deploy/dietbot.service" /etc/systemd/system/dietbot.service
systemctl daemon-reload
systemctl enable -q dietbot
systemctl restart dietbot
sleep 3
systemctl --no-pager --lines=15 status dietbot
