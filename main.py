import os
import uuid
import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# НАСТРОЙКИ
BOT_TOKEN = "8299061655:AAE8I3f_wtaEwc9K3RpkeHgYswgTMr7kSfg"  # <- замените на ваш токен
DATA_DIR = "data"
SCORES_FILE = os.path.join(DATA_DIR, "scores.txt")  # простой текстовый файл
os.makedirs(DATA_DIR, exist_ok=True)

bot = telebot.TeleBot(BOT_TOKEN)

# НАСТРОЙКИ ИГРЫ
MAX_QUESTIONS = 20
WIN_THRESHOLD = 15

# ВОПРОСЫ
QUESTIONS = [
    # НЕ СЕРЬЁЗНЫЕ (low)
    {"id":1, "text":"Использование велосипеда вместо машины для коротких поездок", "class":"low"},
    {"id":2, "text":"Переход на электромобиль", "class":"low"},
    {"id":3, "text":"Использование многоразовой бутылки вместо одноразовых", "class":"low"},
    {"id":4, "text":"Использование тканевых сумок вместо пакетов", "class":"low"},
    {"id":5, "text":"Раздельный сбор отходов дома", "class":"low"},
    {"id":6, "text":"Отказ от одноразовых пластиковых стаканчиков", "class":"low"},
    {"id":7, "text":"Экономия электроэнергии (выключение света, LED-лампы)", "class":"low"},
    {"id":8, "text":"Пешие прогулки вместо коротких поездок на авто", "class":"low"},
    {"id":9, "text":"Закрывать кран во время чистки зубов, чтобы экономить воду", "class":"low"},
    {"id":10, "text":"Покупка техники с низким энергопотреблением", "class":"low"},

    # СЕРЬЁЗНЫЕ (high)
    {"id":11, "text":"Заводы, выбрасывающие тонны CO₂ в атмосферу", "class":"high"},
    {"id":12, "text":"ТЭС (тепловые электростанции) на угле", "class":"high"},
    {"id":13, "text":"Вырубка тропических лесов под плантации", "class":"high"},
    {"id":14, "text":"Крупные нефтеперерабатывающие заводы", "class":"high"},
    {"id":15, "text":"Автомобили с двигателем внутреннего сгорания (массовое использование)", "class":"high"},
    {"id":16, "text":"Сжигание мусора на свалках без фильтрации", "class":"high"},
    {"id":17, "text":"Производство цемента в больших масштабах", "class":"high"},
    {"id":18, "text":"Крупные авиаперевозки и авиапромышленность", "class":"high"},
    {"id":19, "text":"Химические предприятия без очистных сооружений", "class":"high"},
    {"id":20, "text":"Массовая добыча угля и нефти", "class":"high"},
]

# ПРОСТОЕ ХРАНЕНИЕ ОЧКОВ (текстовый файл)
# Формат: user_id|name|points|attempts
def load_scores_simple():
    scores = {}
    if not os.path.exists(SCORES_FILE):
        return scores
    with open(SCORES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) != 4:
                continue
            uid, name, points_s, attempts_s = parts
            try:
                scores[uid] = {"name": name, "points": int(points_s), "attempts": int(attempts_s)}
            except:
                continue
    return scores

def save_scores_simple(scores):
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        for uid, rec in scores.items():
            line = f"{uid}|{rec.get('name','')}|{rec.get('points',0)}|{rec.get('attempts',0)}\n"
            f.write(line)

# СЕССИИ (token -> session dict)
# session: {"uid": str(user_id), "points": int, "answered": int, "q": question}
SESSIONS = {}

# УТИЛИТЫ
def pick_question():
    return random.choice(QUESTIONS)

def make_keyboard(token):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Низкий", callback_data=f"{token}:low"),
               InlineKeyboardButton("Высокий", callback_data=f"{token}:high"))
    return markup

def format_question_text(q, points, qnum):
    # qnum = текущий номер вопроса (1..MAX_QUESTIONS)
    return (
        f"Вопрос {qnum}/{MAX_QUESTIONS}:\n\n{q['text']}\n\n(Выберите «Низкий» или «Высокий».)\n\n"
        f"Ваши очки в этой игре: {points}"
    )

# КОМАНДЫ
@bot.message_handler(commands=["start"])
def cmd_start(message):
    text = (
        "Привет! Я простая викторина про углеродный след.\n\n"
        "Команды:\n"
        "/quiz — начать новую игру (максимум 20 вопросов)\n\n"
        "После ответа бот сразу даёт следующий вопрос до тех пор, пока не будет отвечено 20 вопросов.\n"
        "После 20 вопросов вы получите итог: Победа (>=15) или Проигрыш (<15)."
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=["quiz"])
def cmd_quiz(message):
    # создаём новую игровую сессию для пользователя
    uid = str(message.from_user.id)
    initial_q = pick_question()
    token = uuid.uuid4().hex
    session = {"uid": uid, "points": 0, "answered": 0, "q": initial_q}
    SESSIONS[token] = session

    # показываем первый вопрос (номер 1)
    text = format_question_text(initial_q, session["points"], session["answered"] + 1)
    bot.send_message(message.chat.id, text, reply_markup=make_keyboard(token))

# команда /score удалена по требованию (не используется)

# ОБРАБОТКА ОТВЕТОВ (кнопки)
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data or ""
    parts = data.split(":", 1)
    if len(parts) != 2:
        bot.answer_callback_query(call.id, "Ошибка данных.")
        return

    token, choice = parts
    session = SESSIONS.pop(token, None)
    if not session:
        bot.answer_callback_query(call.id, "Сессия устарела или неверный токен. Нажмите /quiz для новой игры.")
        return

    uid = str(call.from_user.id)
    if session.get("uid") != uid:
        bot.answer_callback_query(call.id, "Это не ваша сессия. Нажмите /quiz, чтобы начать свою игру.")
        return

    # обновляем счётчик ответов в текущей игре
    session["answered"] = session.get("answered", 0) + 1

    # проверяем ответ игрока
    user_choice = "low" if choice == "low" else "high"
    if user_choice == session["q"]["class"]:
        session["points"] = session.get("points", 0) + 1

    # также обновляем простое глобальное хранилище очков (опционально)
    scores = load_scores_simple()
    rec = scores.get(uid, {"name": call.from_user.full_name, "points":0, "attempts":0})
    rec["attempts"] = rec.get("attempts", 0) + 1
    if user_choice == session["q"]["class"]:
        rec["points"] = rec.get("points", 0) + 1
    scores[uid] = rec
    save_scores_simple(scores)

    # Если уже отвечено MAX_QUESTIONS — заканчиваем игру и показываем результат
    if session["answered"] >= MAX_QUESTIONS:
        pts = session.get("points", 0)
        result = "Победа" if pts >= WIN_THRESHOLD else "Проигрыш"
        final_text = (
            f"Игра окончена!\n\nВы набрали {pts} из {MAX_QUESTIONS} возможных.\nРезультат: {result}"
        )
        try:
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text=final_text)
        except Exception:
            bot.send_message(call.message.chat.id, final_text)

        bot.answer_callback_query(call.id)
        return

    # Иначе — готовим следующий вопрос и создаём новый токен/сессию
    next_q = pick_question()
    next_token = uuid.uuid4().hex
    next_session = {"uid": uid, "points": session["points"], "answered": session["answered"], "q": next_q}
    SESSIONS[next_token] = next_session

    text = format_question_text(next_q, next_session["points"], next_session["answered"] + 1)

    try:
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=text,
                              reply_markup=make_keyboard(next_token))
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=make_keyboard(next_token))

    bot.answer_callback_query(call.id)

# СТАРТ
if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)
