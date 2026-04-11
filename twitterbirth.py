# -*- coding: utf-8 -*-
# ================================================
# Бот на базе py3kicq (один файл) + Twitbirth
# Теперь КАЖДЫЙ пользователь сам указывает свои email:password от Twitbirth
# Команда: !set твой@email.ru:твойпароль
# После этого любое сообщение боту → постится от его аккаунта
# ================================================

from pycq import *
import urllib.request
import urllib.parse
import base64
import time

# ====================== НАСТРОЙКИ ICQ ======================
_main_uin = 111111          # ←←← ИЗМЕНИ НА UIN БОТА
_main_password = "pereguda" # ←←← ИЗМЕНИ НА ПАРОЛЬ БОТА

# Второй UIN для теста (можно 0)
_test_uin = 0
# ======================================================

# Словарь для хранения учётных данных каждого пользователя
# Ключ — UIN отправителя, значение — dict с email и password
user_credentials = {}  # {uin: {"email": "...", "password": "..."}}


def post_to_twitbirth(status: str, email: str, password: str) -> bool:
    """Постит статус через Twitbirth API (с Basic Auth)"""
    if not status.strip() or not email or not password:
        return False

    url = "http://twitbirth.downgrade-net.ru/api.php?update.json"
    data = urllib.parse.urlencode({"status": status}).encode("utf-8")

    # Basic Auth
    auth_str = f"{email}:{password}"
    auth_bytes = base64.b64encode(auth_str.encode("utf-8")).decode("ascii")

    headers = {
        "Authorization": f"Basic {auth_bytes}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "py3kicq-twitbirth-bot",
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            resp_text = response.read().decode("utf-8", errors="ignore")
            print(f"[+] Успешно запостили для {email}: {resp_text[:150]}...")
            return True
    except Exception as e:
        print(f"[-] Ошибка постинга для {email}: {e}")
        return False


# ====================== ЗАПУСК ======================
c = pycq()
c.connect()
c.login(_main_uin, _main_password, 0, 1)
c.change_status(32)  # Free for Chat

if _test_uin:
    c.set_test_uin(_test_uin)

print(f"✅ Бот запущен! UIN: {_main_uin}")
print("   Каждый пользователь может сам задать свои данные Twitbirth командой:")
print("   !set email:password")
print("   После этого любое сообщение → пост в Twitbirth от его аккаунта")
print("   !help — список команд")

while True:
    p = c.main(10)

    if not (p and isinstance(p, list) and len(p) > 0 and isinstance(p[0], dict)):
        continue

    if 'uin' not in p[0] or 'message_text' not in p[0]:
        continue

    sender_uin = p[0]['uin']
    message_text = p[0]['message_text'].replace('\ufffd', '').strip()

    # ====================== ОБРАБОТКА КОМАНД ======================
    lower_msg = message_text.lower().strip()

    if lower_msg in ('!help', '!помощь', '!команды'):
        help_text = (
            "📌 Команды бота:\n"
            "!set email:password  — задать свои данные Twitbirth\n"
            "!status              — проверить, авторизован ли ты\n"
            "!unset               — удалить свои данные\n"
            "!help                — эта справка\n"
            "Любое другое сообщение — сразу постится в Twitbirth"
        )
        c.send_message_server(sender_uin, help_text)
        continue

    elif lower_msg.startswith('!set '):
        try:
            creds_part = message_text[5:].strip()          # берём оригинальный регистр
            if ':' not in creds_part:
                raise ValueError
            email, pw = [x.strip() for x in creds_part.split(':', 1)]
            if not email or not pw:
                raise ValueError

            user_credentials[sender_uin] = {"email": email, "password": pw}
            c.send_message_server(sender_uin, f"✅ Данные сохранены!\nАккаунт: {email}\nТеперь шлите сообщения — они будут поститься автоматически.")
        except:
            c.send_message_server(sender_uin, "❌ Неверный формат!\nИспользуй: !set твой@email.ru:твойпароль")
        continue

    elif lower_msg == '!status' or lower_msg == '!статус':
        if sender_uin in user_credentials:
            email = user_credentials[sender_uin]["email"]
            c.send_message_server(sender_uin, f"✅ Ты авторизован как {email} в Twitbirth")
        else:
            c.send_message_server(sender_uin, "❌ Данные Twitbirth не заданы.\nИспользуй !set email:password")
        continue

    elif lower_msg == '!unset':
        if sender_uin in user_credentials:
            del user_credentials[sender_uin]
            c.send_message_server(sender_uin, "🗑️ Данные удалены.")
        else:
            c.send_message_server(sender_uin, "❌ У тебя и так ничего не сохранено.")
        continue

    # ====================== ОБЫЧНЫЙ ПОСТ ======================
    if sender_uin not in user_credentials:
        c.send_message_server(sender_uin, "❌ Сначала укажи свои данные Twitbirth командой:\n!set email:password")
        continue

    creds = user_credentials[sender_uin]
    if post_to_twitbirth(message_text, creds["email"], creds["password"]):
        c.send_message_server(sender_uin, "✅ Пост успешно опубликован в Twitbirth!")
    else:
        c.send_message_server(sender_uin, "❌ Не удалось опубликовать. Проверь лог бота.")

    time.sleep(0.1)
