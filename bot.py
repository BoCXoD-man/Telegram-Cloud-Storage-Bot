"""
Telegram-бот для просмотра содержимого Google Drive и Yandex Disk.

Бот принимает ссылки на облачные хранилища, определяет сервис,
получает список доступных файлов через соответствующий API
и отправляет результат пользователю в Telegram.
"""

import html
import os
import re
import time

import requests
import telebot
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


load_dotenv()



BOT_TOKEN = os.getenv("BOT_TOKEN")
YANDEX_TOKEN = os.getenv("YANDEX_TOKEN", "")
SERVICE_ACCOUNT_FILE = os.getenv(
    "SERVICE_ACCOUNT_FILE",
    "service_account.json",
)

GOOGLE_DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
]

TELEGRAM_MESSAGE_LIMIT = 4096
REQUEST_TIMEOUT = 15

if not BOT_TOKEN:
    raise RuntimeError(
        "Не задан BOT_TOKEN. Добавьте его в файл .env."
    )

bot = telebot.TeleBot(BOT_TOKEN)

drive_service = None
google_active = False


def initialize_google_drive():
    """Инициализирует Google Drive API при наличии credentials-файла."""
    global drive_service, google_active

    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(
            f"ПРЕДУПРЕЖДЕНИЕ: не найден файл "
            f"{SERVICE_ACCOUNT_FILE}. "
            "Google Drive работать не будет."
        )
        return

    try:
        credentials = (
            service_account.Credentials
            .from_service_account_file(
                SERVICE_ACCOUNT_FILE,
                scopes=GOOGLE_DRIVE_SCOPES,
            )
        )

        drive_service = build(
            "drive",
            "v3",
            credentials=credentials,
        )
        google_active = True

        print("Google Drive сервис подключен.")

    except Exception as error:
        print(f"Ошибка подключения Google Drive: {error}")


def extract_google_folder_id(url):
    """Извлекает ID папки Google Drive из URL."""
    folder_pattern = r"drive\.google\.com/drive/folders/([a-zA-Z0-9_-]+)"
    folder_match = re.search(folder_pattern, url)

    if folder_match:
        return folder_match.group(1)

    id_pattern = r"[?&]id=([a-zA-Z0-9_-]+)"
    id_match = re.search(id_pattern, url)

    if id_match:
        return id_match.group(1)

    return None


def send_long_message(chat_id, text):
    """Разбивает длинный текст на сообщения допустимого размера Telegram."""
    if len(text) <= TELEGRAM_MESSAGE_LIMIT:
        bot.send_message(chat_id, text)
        return

    while text:
        if len(text) <= TELEGRAM_MESSAGE_LIMIT:
            part = text
            text = ""
        else:
            split_index = text.rfind(
                "\n",
                0,
                TELEGRAM_MESSAGE_LIMIT,
            )

            if split_index <= 0:
                split_index = TELEGRAM_MESSAGE_LIMIT

            part = text[:split_index]
            text = text[split_index:].lstrip("\n")

        bot.send_message(chat_id, part)
        time.sleep(0.5)


def get_google_drive_files(folder_id):
    """Возвращает список файлов и папок внутри Google Drive."""
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        fields="files(name, mimeType)",
        pageSize=100,
        orderBy="name",
    ).execute()

    return results.get("files", [])


def format_google_drive_files(items):
    """Формирует текст со списком объектов Google Drive."""
    lines = [
        f"📂 Файлы Google Drive ({len(items)} шт.):",
        "",
    ]

    for index, item in enumerate(items, start=1):
        icon = (
            "📁"
            if item["mimeType"] == "application/vnd.google-apps.folder"
            else "📄"
        )

        name = html.unescape(item.get("name", "Без названия"))
        lines.append(f"{index}. {icon} {name}")

    return "\n".join(lines)


def get_yandex_public_resource(url):
    """Получает информацию о публичном ресурсе Yandex Disk."""
    api_url = (
        "https://cloud-api.yandex.net/v1/disk/public/resources"
    )

    params = {
        "public_key": url,
        "limit": 100,
    }

    headers = {}

    if YANDEX_TOKEN:
        headers["Authorization"] = f"OAuth {YANDEX_TOKEN}"

    response = requests.get(
        api_url,
        params=params,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    return response.json()


def format_yandex_resource(data):
    """Формирует текст с информацией о ресурсе Yandex Disk."""
    embedded = data.get("_embedded")

    if not embedded:
        name = data.get("name", "Без названия")
        return f"📄 Это одиночный файл:\n{name}"

    items = embedded.get("items", [])
    total = embedded.get("total", len(items))

    if not items:
        return "📂 В папке Яндекс.Диска пусто."

    lines = [
        f"📂 Файлы Яндекс.Диск "
        f"(показано {len(items)} из {total}):",
        "",
    ]

    for index, item in enumerate(items, start=1):
        icon = "📁" if item.get("type") == "dir" else "📄"
        name = item.get("name", "Без названия")
        lines.append(f"{index}. {icon} {name}")

    return "\n".join(lines)


def handle_google_drive_link(message):
    """Обрабатывает сообщение со ссылкой на Google Drive."""
    if not google_active:
        bot.reply_to(
            message,
            "Работа с Google Drive не настроена: "
            "не найден или не загрузился файл авторизации.",
        )
        return

    folder_id = extract_google_folder_id(message.text)

    if not folder_id:
        bot.reply_to(
            message,
            "Не удалось определить ID папки Google Drive "
            "в переданной ссылке.",
        )
        return

    wait_message = bot.reply_to(
        message,
        "🔍 Google Drive: проверяю доступ и список файлов...",
    )

    try:
        items = get_google_drive_files(folder_id)

        if not items:
            bot.edit_message_text(
                "📂 В папке Google Drive пусто.",
                chat_id=message.chat.id,
                message_id=wait_message.message_id,
            )
            return

        result = format_google_drive_files(items)

        bot.delete_message(
            chat_id=message.chat.id,
            message_id=wait_message.message_id,
        )

        send_long_message(message.chat.id, result)

    except HttpError as error:
        print(f"Google Drive API error: {error}")

        bot.edit_message_text(
            "⛔ Не удалось получить доступ к папке Google Drive.\n\n"
            "Проверьте, что папка доступна сервисному аккаунту.",
            chat_id=message.chat.id,
            message_id=wait_message.message_id,
        )

    except Exception as error:
        print(f"Google Drive error: {error}")

        bot.edit_message_text(
            "❌ При работе с Google Drive произошла ошибка.",
            chat_id=message.chat.id,
            message_id=wait_message.message_id,
        )


def handle_yandex_disk_link(message):
    """Обрабатывает публичную ссылку на Yandex Disk."""
    url = message.text.strip()

    wait_message = bot.reply_to(
        message,
        "🔍 Yandex Disk: получаю информацию о публичной ссылке...",
    )

    try:
        data = get_yandex_public_resource(url)
        result = format_yandex_resource(data)

        bot.delete_message(
            chat_id=message.chat.id,
            message_id=wait_message.message_id,
        )

        send_long_message(message.chat.id, result)

    except requests.HTTPError as error:
        status_code = error.response.status_code

        print(f"Yandex Disk API error: {status_code}")

        if status_code == 404:
            error_message = "⛔ Ссылка не найдена или неверна."
        elif status_code == 403:
            error_message = (
                "⛔ Нет доступа к ресурсу. "
                "Возможно, ссылка больше не является публичной."
            )
        else:
            error_message = (
                f"❌ Ошибка API Яндекс.Диска: "
                f"код {status_code}."
            )

        bot.edit_message_text(
            error_message,
            chat_id=message.chat.id,
            message_id=wait_message.message_id,
        )

    except requests.RequestException as error:
        print(f"Yandex Disk request error: {error}")

        bot.edit_message_text(
            "❌ Не удалось подключиться к API Яндекс.Диска.",
            chat_id=message.chat.id,
            message_id=wait_message.message_id,
        )

    except Exception as error:
        print(f"Yandex Disk error: {error}")

        bot.edit_message_text(
            "❌ При работе с Яндекс.Диском произошла ошибка.",
            chat_id=message.chat.id,
            message_id=wait_message.message_id,
        )


@bot.message_handler(commands=["start"])
def send_welcome(message):
    """Отправляет пользователю инструкцию по использованию бота."""
    bot.reply_to(
        message,
        "Привет! 👋\n\n"
        "Пришли мне ссылку на:\n"
        "1. 📂 Папку Google Drive\n"
        "2. 📂 Публичный ресурс Yandex Disk\n\n"
        "Я проверю доступ и выведу список файлов.",
    )


@bot.message_handler(
    func=lambda message: (
        bool(message.text)
        and "drive.google.com" in message.text
    )
)
def google_drive_handler(message):
    """Передаёт ссылку Google Drive обработчику."""
    handle_google_drive_link(message)


@bot.message_handler(
    func=lambda message: (
        bool(message.text)
        and any(
            domain in message.text
            for domain in (
                "disk.yandex.ru",
                "yadi.sk",
                "disk.yandex.com",
                "yandex.ru",
                "yandex.com",
            )
        )
    )
)
def yandex_disk_handler(message):
    """Передаёт ссылку Yandex Disk обработчику."""
    handle_yandex_disk_link(message)


if __name__ == "__main__":
    initialize_google_drive()

    print("Бот запущен. Ожидание сообщений...")

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30,
    )

