# 🤖 Telegram Cloud Storage Bot

Telegram-бот для работы с файлами, размещёнными в облачных хранилищах.

Бот принимает ссылки на папки **Google Drive** и публичные ресурсы **Yandex Disk**, получает информацию о содержимом и отправляет результат пользователю прямо в Telegram.

Проект создан для реальной коммерческой задачи и демонстрирует интеграцию Telegram Bot API с внешними облачными сервисами.

---

## ✨ Возможности

* 📂 получение списка файлов из папки Google Drive;
* ☁️ работа с публичными ресурсами Yandex Disk;
* 🔗 автоматическое определение типа ссылки;
* 📋 отображение названий и типов файлов;
* ⚠️ обработка ошибок API и недоступных ресурсов;
* 🔐 хранение токенов и настроек в `.env`;
* 🔑 авторизация Google Drive через Service Account;
* ⏱️ таймауты HTTP-запросов;
* 📦 разбиение длинных сообщений Telegram на несколько частей.

---

## 🛠️ Технологии

* **Python**
* **pyTelegramBotAPI**
* **Google Drive API**
* **Yandex Disk REST API**
* **Requests**
* **python-dotenv**
* **Google Service Account**
* **REST API**
* **JSON**

---

## 🏗️ Как это работает

```text
             Telegram
                 │
                 ▼
          ┌─────────────┐
          │ Telegram Bot│
          └──────┬──────┘
                 │
          Определение ссылки
                 │
        ┌────────┴────────┐
        ▼                 ▼
 Google Drive        Yandex Disk
        │                 │
        ▼                 ▼
 Google Drive API    Yandex REST API
        │                 │
        └────────┬────────┘
                 ▼
        Получение ресурсов
                 │
                 ▼
        Формирование ответа
                 │
                 ▼
             Telegram
```

---

## 📁 Структура проекта

```text
telegram-cloud-storage-bot/
│
├── bot.py                  # Основная логика Telegram-бота
├── requirements.txt        # Зависимости проекта
├── .env.example            # Шаблон переменных окружения
├── .gitignore              # Исключения Git
├── README.md               # Документация
│
├── .env                    # Локальные настройки, не публикуется
└── service_account.json    # Credentials Google, не публикуется
```

---

# 🚀 Установка

## 1. Клонирование проекта

```bash
git clone git@github.com:BoCXoD-man/Telegram-Cloud-Storage-Bot.git
cd telegram-cloud-storage-bot
```

## 2. Создание виртуального окружения

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

---

# ⚙️ Настройка

## Telegram Bot

Создайте Telegram-бота через **BotFather** и получите токен.

После этого создайте файл:

```text
.env
```

и добавьте:

```env
BOT_TOKEN=your_telegram_bot_token
YANDEX_TOKEN=
SERVICE_ACCOUNT_FILE=service_account.json
```

---

# ☁️ Google Drive

Для работы с Google Drive используется **Google Service Account**.

### Шаг 1. Создать проект Google Cloud

Создайте проект в Google Cloud Console.

### Шаг 2. Включить Google Drive API

В созданном проекте необходимо включить:

```text
Google Drive API
```

### Шаг 3. Создать Service Account

Создайте Service Account и скачайте JSON-файл с credentials.

Переименуйте файл в:

```text
service_account.json
```

и положите его в корень проекта:

```text
telegram-cloud-storage-bot/
├── bot.py
├── service_account.json
└── ...
```

### Шаг 4. Предоставить доступ к папке

У Service Account есть собственный email.

Предоставьте этому адресу доступ к нужной папке Google Drive.

Например:

```text
Service Account email
        ↓
Доступ к папке Google Drive
        ↓
Google Drive API
        ↓
Telegram Bot
```

Без этого бот сможет авторизоваться в Google Drive, но не сможет прочитать содержимое нужной папки.

---

# ☁️ Yandex Disk

Бот поддерживает публичные ссылки на ресурсы Yandex Disk.

Для публичных ресурсов авторизация обычно не требуется.

При необходимости можно указать OAuth-токен:

```env
YANDEX_TOKEN=your_yandex_token
```

---

# ▶️ Запуск

После настройки выполните:

```bash
python bot.py
```

После запуска бот начинает принимать сообщения в Telegram.

---

# 💬 Использование

Отправьте боту ссылку на папку Google Drive:

```text
https://drive.google.com/drive/folders/...
```

Бот определит ссылку и запросит содержимое папки через Google Drive API.

Пример ответа:

```text
📂 Файлы Google Drive (3 шт.):

1. 📄 Пример результата.png
2. 📄 ТЗ (J) Магазин эзотерики.pdf
3. 📄 Чек-лист.docx
```

Также можно отправлять поддерживаемые публичные ссылки Yandex Disk.

---

# 🛡️ Обработка ошибок

Бот обрабатывает основные проблемы при работе с внешними сервисами:

* отсутствующий Telegram-токен;
* отсутствие файла Google credentials;
* недоступную папку Google Drive;
* отсутствие прав у Service Account;
* некорректные ссылки;
* HTTP-ошибки Yandex API;
* ошибки сетевых запросов;
* пустые папки;
* слишком длинные сообщения Telegram.

Для HTTP-запросов используются таймауты, чтобы бот не зависал бесконечно при проблемах с внешним сервисом.

---

# 🔐 Безопасность

Секретные данные не должны попадать в Git.

В частности:

```text
.env
service_account.json
```

добавлены в `.gitignore`.

**Никогда не публикуйте:**

* Telegram Bot Token;
* Google Service Account credentials;
* Yandex OAuth Token;
* другие секретные ключи.

Для GitHub используется файл:

```text
.env.example
```

с безопасными placeholder-значениями.

---

# 🎯 Что демонстрирует проект

Проект показывает практический опыт работы с:

* Python;
* Telegram Bot API;
* Google Drive API;
* REST API;
* HTTP-запросами;
* OAuth / Service Account;
* переменными окружения;
* обработкой исключений;
* интеграцией нескольких внешних сервисов;
* структурированием небольшого прикладного приложения.

Отдельно проект интересен тем, что был создан для **реальной прикладной задачи**, а не только как учебный пример.

---

# 📌 Статус

**Completed / Commercial Project**

Проект находится в рабочем состоянии и может использоваться как дополнительный пример практического опыта разработки на Python.

---

## 📫 Автор

**Андрей Манаев**

* GitHub: [BoCXoD-man](https://github.com/BoCXoD-man)
* Telegram: [@xBoCXoDx](https://t.me/xBoCXoDx)
