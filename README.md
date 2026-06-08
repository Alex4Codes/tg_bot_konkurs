# 🏆 Telegram Contest Bot (Subscription Checker)

Асинхронный Telegram-бот для автоматической проверки подписки пользователей на канал и регистрации участия в конкурсах. 


## ✨ Особенности

- ⚡ **Молниеносная работа:** Использование современного менеджера пакетов и окружений [`uv`](https://github.com/astral-sh/uv).
- 🔄 **Асинхронность:** Построен на актуальной версии **aiogram 3.x**.
- 💾 **Надежное хранение:** Данные участников сохраняются в асинхронную базу данных **SQLite** (`aiosqlite`), что гарантирует сохранность при перезагрузках.
- 🛡️ **Строгая конфигурация:** Валидация переменных окружения через **Pydantic Settings** (бот не запустится с ошибочными настройками).
- 📝 **Продакшен-логирование:** Двойной вывод логов (в консоль и в файл `bot.log`) с уровнями INFO/ERROR.
- 🐳 **Готовность к деплою:** Включены конфигурации для запуска через Systemd или Docker.

---

## ⚠️ Критически важное требование

Для работы проверки подписки **бот обязательно должен быть добавлен в ваш канал в качестве администратора**. 
Достаточно выдать ему право *"Просматривать участников канала"* (или просто сделать админом без права публикации постов). Без этого Telegram API вернет ошибку.

---

## 🛠️ Предварительные требования

1. Установленный [Python 3.10+](https://www.python.org/).
2. Установленный инструмент [`uv`](https://docs.astral.sh/uv/getting-started/installation/):
   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows (через PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Или через pip
   pip install uv
   ```
## Systemd (Рекомендуется для VPS/VDS)
   Настрока сервиса
   ```bash
   [Unit]
   Description=Telegram Contest Bot
   After=network.target
   
   [Service]
   WorkingDirectory=/path/to/your/contest_bot
   # Укажите абсолютный путь к uv (узнать можно командой: which uv)
   ExecStart=/home/your_user/.cargo/bin/uv run python src/main.py
   Restart=always
   RestartSec=3
   User=your_user
   
   [Install]
   WantedBy=multi-user.target
   ```
   Запуск сервиса
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable contest-bot
   sudo systemctl start contest-bot
   ```
