import os
import telegram
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    Filters,
    Updater,
    ConversationHandler,
)
from dotenv import load_dotenv
import random
import re
import json
import logging
import redis


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
REDIS_DB_NUM = os.environ.get("REDIS_DB_NUM", 0)

redis_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_NUM)

QUESTION, ANSWER, RETRY_QUESTION = range(3)


def get_random_question():
    file_name = random.choice(os.listdir("questions-json"))

    with open(os.path.join("questions-json", file_name)) as json_file:
        questions = json.load(json_file)
        question_block = random.choice(questions)
        return question_block, file_name


def get_question_by_id(q_id):
    q_id = str(q_id).strip("'b")
    file_name, user_question_id = q_id.split(":")
    with open(os.path.join("questions-json", file_name)) as json_file:
        questions = json.load(json_file)
        question = [q for q in questions if q["id"] == int(user_question_id)][0]
        return question


def check_answer(user_answer, right_answer):
    # Requires revision
    right_answers = []
    try:
        right_answers.append(re.findall(r"(.*?)[\.\(\!,]", right_answer)[0].strip())
    except IndexError:
        pass
    
    right_answers.append(right_answer)
    if user_answer in right_answers:
        return True
    return False


def accept_answer(bot, update):
    right_answer = get_question_by_id(redis_db.get(f"{update.message.chat_id}:tglast"))[
        "answer"
    ]
    result = check_answer(update.message.text, right_answer)

    if result:
        custom_keyboard = [["Новый вопрос"], ["Мой счёт"]]
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        update.message.reply_text(text="Правильный ответ!", reply_markup=reply_markup)
        redis_db.incr(f"{update.message.chat_id}:tgscore")
        return QUESTION

    custom_keyboard = [["Попробовать еще раз", "Сдаться"], ["Мой счёт"]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(text="Неверный ответ(", reply_markup=reply_markup)
    return RETRY_QUESTION


def send_question(bot, update):
    question_block, file_name = get_random_question()
    question = question_block["question"]

    custom_keyboard = [["Сдаться"], ["Мой счёт"]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(text=question, reply_markup=reply_markup)
    redis_db.set(
        f"{update.message.chat_id}:tglast", f'{file_name}:{question_block["id"]}'
    )
    return ANSWER


def retry_question(bot, update):
    question = get_question_by_id(redis_db.get(f"{update.message.chat_id}:tglast"))[
        "question"
    ]
    update.message.reply_text(text=question)
    return ANSWER


def give_up(bot, update):
    answer = get_question_by_id(redis_db.get(f"{update.message.chat_id}:tglast"))[
        "answer"
    ]
    custom_keyboard = [["Новый вопрос"], ["Мой счёт"]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(
        text=f"Вы сдались ☹️ правильный ответ был:\n {answer}",
        reply_markup=reply_markup,
    )
    return QUESTION


def get_score(bot, update):
    score = int(redis_db.get(f"{update.message.chat_id}:tgscore"))
    update.message.reply_text(text=f"Вы ответили правильно на {score} вопросов")


def start(bot, update):
    custom_keyboard = [["Новый вопрос"], ["Мой счёт"]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(
        text="Привет, я бот для викторин!", reply_markup=reply_markup
    )
    redis_db.set(f"{update.message.chat_id}:tgscore", 0)
    return QUESTION


def main():
    load_dotenv()
    TG_API_TOKEN = os.environ["TG_API"]
    updater = Updater(TG_API_TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUESTION: [
                MessageHandler(Filters.regex(r"Новый вопрос"), send_question),
                MessageHandler(Filters.regex(r"Мой счёт"), get_score),
            ],
            RETRY_QUESTION: [
                MessageHandler(Filters.regex(r"Попробовать еще раз"), retry_question),
                MessageHandler(Filters.regex(r"Мой счёт"), get_score),
            ],
            ANSWER: [
                MessageHandler(Filters.regex(r"Сдаться"), give_up),
                MessageHandler(Filters.regex(r"Мой счёт"), get_score),
                MessageHandler(Filters.text, accept_answer),
            ],
        },
        fallbacks=[],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
