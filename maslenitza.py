# -*- coding: utf-8 -*-
# maslenitsa_bot.py

import datetime
import time
import sys

# Если библиотека в подпапке
# sys.path.insert(0, './py3kicq')

from pycq import pycq

# ────────────────────────────────────────────────
# НАСТРОЙКИ
# ────────────────────────────────────────────────

UIN         = 100001           # UIN бота
PASSWORD    = "thepassw"

ADMIN_UIN   = 100003           # ← ТОЛЬКО этот номер может выключить бота командой !logout

START_DATE  = datetime.date(2026, 2, 16)
END_DATE    = datetime.date(2026, 2, 22)

DAYS_INFO = [
    "Понедельник — Встреча\nПекут первые блины, встречают Масленицу, строят горки",
    "Вторник — Заигрыши\nКатания на санях, игры, флирт, смотрины",
    "Среда — Лакомка\nТеща угощает зятя блинами",
    "Четверг — Разгуляй\nШирокие гулянья, кулачные бои, веселье",
    "Пятница — Тёщины вечерки\nЗять угощает тещу блинами у себя",
    "Суббота — Золовкины посиделки\nНевестка зовёт золовок",
    "Воскресенье — Прощёное\nПросят прощения, сжигают чучело"
]

# Сообщение для ночной рассылки (можно изменить)
NIGHT_MESSAGE = "С наступившим днём Масленицы! 🥞🔥 Сегодня {day_name}. Приятного праздника!"

# ────────────────────────────────────────────────

bot = pycq()
print(f"Запуск бота {UIN}...")

bot.connect()
bot.login(UIN, PASSWORD, 0, 1)
bot.change_status(32)  # онлайн

print("Бот онлайн")

# Переменные для рассылки в полночь
last_midnight = None
roster = []                # список контактов (будем пытаться загрузить)

# Пытаемся получить список контактов один раз после логина
# Внимание: в разных версиях py3kicq метод может называться по-разному!
# Попробуй эти варианты по очереди (раскомментируй нужный)
try:
    # Вариант 1
    roster = bot.get_buddy_list() or []
except AttributeError:
    pass

try:
    # Вариант 2 (часто встречается)
    roster = bot.buddylist or []
except AttributeError:
    pass

try:
    # Вариант 3
    roster = bot.get_roster() or []
except AttributeError:
    pass

if roster:
    print(f"Загружено {len(roster)} контактов")
else:
    print("Не удалось получить список контактов → ночная рассылка отключена")

while True:
    try:
        packets = bot.main(6)

        if not packets:
            # Проверяем полночь даже если нет сообщений
            now = datetime.datetime.now()
            if now.hour == 0 and now.minute <= 5 and (last_midnight is None or now.date() > last_midnight):
                last_midnight = now.date()

                if roster:
                    day_idx = (now.date() - START_DATE).days
                    if 0 <= day_idx <= 6:
                        day_name = DAYS_INFO[day_idx].split(" — ")[0]
                        msg = NIGHT_MESSAGE.format(day_name=day_name)
                    else:
                        msg = "С наступившим! Масленица уже близко или уже прошла 🥞"

                    print(f"Ночная рассылка ({len(roster)} чел): {msg[:60]}...")

                    sent_ok = 0
                    for contact_uin in roster:
                        try:
                            bot.send_message_server(contact_uin, msg)
                            sent_ok += 1
                            time.sleep(0.4)  # задержка, чтобы не забанили за спам
                        except Exception as e:
                            print(f"Ошибка отправки {contact_uin}: {e}")

                    print(f"Рассылка завершена, отправлено: {sent_ok}/{len(roster)}")

            time.sleep(1)
            continue

        for p in packets:
            if not isinstance(p, dict):
                continue

            sender = p.get('uin') or p.get('from') or p.get('sender')
            text   = p.get('message_text') or p.get('text') or p.get('msg') or p.get('body')

            if not sender or not text:
                continue

            text = str(text).strip()
            print(f"[{sender}] {text}")

            low_text = text.lower().strip()

            # Только админ может выключить бота
            if low_text in ('!logout', '!выход', '!exit', '!логоут') and sender == ADMIN_UIN:
                try:
                    bot.send_message_server(sender, "Бот выключается... До свидания!")
                except:
                    pass
                print("ADMIN logout → завершение")
                bot.logout()
                time.sleep(1)
                sys.exit(0)

            # Обычный ответ на любое сообщение
            today = datetime.date.today()

            if today < START_DATE:
                left = (START_DATE - today).days
                reply = f"До Масленицы осталось {left} дней"
                if left <= 0:
                    reply = "Масленица начинается сегодня!"
            elif today > END_DATE:
                reply = "Масленица 2026 уже прошла"
            else:
                idx = (today - START_DATE).days
                if 0 <= idx <= 6:
                    reply = DAYS_INFO[idx]
                else:
                    reply = "Что-то пошло не так с датой..."

            try:
                bot.send_message_server(sender, reply)
            except Exception as e:
                print(f"Ошибка отправки ответа {sender}: {e}")

            time.sleep(0.12)

    except KeyboardInterrupt:
        print("Ctrl+C → выход")
        bot.logout()
        sys.exit(0)
    except Exception as e:
        print(f"Ошибка в главном цикле: {e}")
        time.sleep(5)

