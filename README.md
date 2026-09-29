# ИИ-диетолог — Telegram-бот

Считает калории и БЖУ по фото еды, рассчитывает персональный план и ведёт дневник
питания и веса. Русский и английский интерфейс выбирается по языку Telegram.

## Что умеет (версия 0.1)
- Анкета: пол, возраст, рост, вес, цель, активность → норма ккал и БЖУ (Миффлин — Сан Жеор).
- Фото еды → блюда, вес порций, калории и БЖУ, короткий совет. Подпись к фото
  («макароны 200 г») повышает точность.
- Кнопки «Порция меньше / больше / Удалить» — пересчёт без повторного запроса к ИИ.
- /today — итоги дня против нормы, /weight — взвешивание и динамика.
- Бесплатный лимит фото (FREE_PHOTOS), дальше — экран подписки (оплата — следующий этап).

## Запуск
```bash
pip install -r requirements.txt
cp .env.example .env   # заполнить BOT_TOKEN и ANTHROPIC_API_KEY
set -a; . ./.env; set +a
python -m dietbot
```

## Тесты
```bash
pip install pytest pytest-asyncio
python -m pytest -q
```

## Размещение на сервере
Нужен сервер **вне России** (например, локация Нидерланды или Германия):
API Anthropic не принимает запросы с российских IP, а Telegram в России замедляют.

```bash
git clone -b claude/opus-5-5-github-check-69dpf2 https://github.com/golarrdo-cmyk/OPUS.git /tmp/opus
sudo bash /tmp/opus/deploy/install.sh     # первый запуск создаст /opt/dietbot/.env
sudo nano /opt/dietbot/.env                # вписать BOT_TOKEN и ANTHROPIC_API_KEY
sudo bash /opt/dietbot/deploy/install.sh  # установит и запустит службу
journalctl -u dietbot -f                   # живые логи
```
Повторный запуск `install.sh` обновляет бота до последней версии.
