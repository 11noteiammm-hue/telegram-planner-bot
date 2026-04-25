# Деплой бота на Render.com

## Шаг 1: Подготовка GitHub репозитория

1. Создай аккаунт на [GitHub](https://github.com) (если нет)
2. Создай новый репозиторий (например, `telegram-planner-bot`)
3. Загрузи туда все файлы из папки `C:\scripts\telegram_planner_bot\` **КРОМЕ**:
   - `.env` (не загружай! там токен)
   - `bot_database.db`
   - `__pycache__`

### Как загрузить через GitHub Desktop (проще):

1. Скачай [GitHub Desktop](https://desktop.github.com/)
2. Войди в аккаунт
3. File → Add Local Repository → выбери `C:\scripts\telegram_planner_bot\`
4. Commit и Push

### Или через командную строку:

```bash
cd C:\scripts\telegram_planner_bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/твой_username/telegram-planner-bot.git
git push -u origin main
```

## Шаг 2: Создание сервиса на Render

1. Зайди на [Render.com](https://render.com)
2. Зарегистрируйся (можно через GitHub)
3. Нажми **"New +"** → **"Web Service"**
4. Подключи свой GitHub репозиторий
5. Выбери репозиторий `telegram-planner-bot`

## Шаг 3: Настройка сервиса

Заполни поля:

- **Name**: `telegram-planner-bot` (любое имя)
- **Region**: выбери ближайший (Europe)
- **Branch**: `main`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python bot.py`
- **Instance Type**: **Free** (важно!)

## Шаг 4: Добавление переменных окружения

В разделе **Environment Variables** добавь:

1. Нажми **"Add Environment Variable"**
2. Добавь:
   - Key: `BOT_TOKEN`
   - Value: `8605031704:AAEz7fkUoDzXaupf-BGeu4eGh0quAHVA1a4`

3. Добавь еще одну:
   - Key: `ADMIN_ID`
   - Value: `1150957269`

4. Если нужен прокси, добавь:
   - Key: `PROXY_URL`
   - Value: `твой_прокси` (или оставь пустым)

## Шаг 5: Деплой

1. Нажми **"Create Web Service"**
2. Render начнет деплой (займет 2-5 минут)
3. Дождись статуса **"Live"** (зеленый)
4. Готово! Бот работает 24/7

## Важно о бесплатном тарифе Render:

⚠️ **Ограничения:**
- Бесплатный сервис "засыпает" после 15 минут неактивности
- При новом запросе "просыпается" (занимает ~30 секунд)
- 750 часов работы в месяц (достаточно для одного бота)

💡 **Решение проблемы "засыпания":**
Можно настроить пинг каждые 10 минут через сервис [cron-job.org](https://cron-job.org) на URL твоего Render сервиса.

## Проверка работы

1. Открой Telegram
2. Найди бота `@casofp_bot`
3. Отправь `/start`
4. Если отвечает - всё работает!

## Логи и мониторинг

- В панели Render → твой сервис → вкладка **"Logs"**
- Там видны все логи бота в реальном времени

## Обновление бота

Когда изменишь код:
1. Загрузи изменения в GitHub (commit + push)
2. Render автоматически задеплоит новую версию

## Альтернатива (если Render не подходит)

Если нужен бот без "засыпания", рассмотри:
- **Railway.app** - $5 бесплатно каждый месяц
- **VPS сервер** - от 150₽/месяц (Timeweb, Beget)
