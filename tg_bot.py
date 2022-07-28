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
from quiz_bot_funcs import get_question_by_id, check_answer, get_random_question
from functools import partial


logger = logging.getLogger(__name__)

QUESTION, ANSWER, RETRY_QUESTION = range(3)

def accept_answer(bot, update, redis_db):
    right_answer = get_question_by_id(
        redis_db, redis_db.get(f"{update.message.chat_id}:tglast")
    )["answer"]
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


def send_question(bot, update, redis_db):
    question_block = get_random_question(redis_db)
    question = question_block["question"]

    custom_keyboard = [["Сдаться"], ["Мой счёт"]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(text=question, reply_markup=reply_markup)
    redis_db.set(f"{update.message.chat_id}:tglast", question_block["id"])
    return ANSWER


def retry_question(bot, update, redis_db):
    question = get_question_by_id(
        redis_db, redis_db.get(f"{update.message.chat_id}:tglast")
    )["question"]
    update.message.reply_text(text=question)
    return ANSWER


def give_up(bot, update, redis_db):
    answer = get_question_by_id(
        redis_db, redis_db.get(f"{update.message.chat_id}:tglast")
    )["answer"]
    custom_keyboard = [["Новый вопрос"], ["Мой счёт"]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(
        text=f"Вы сдались ☹️ правильный ответ был:\n {answer}",
        reply_markup=reply_markup,
    )
    return QUESTION


def get_score(bot, update, redis_db):
    score = int(redis_db.get(f"{update.message.chat_id}:tgscore"))
    update.message.reply_text(text=f"Вы ответили правильно на {score} вопросов")


def start(bot, update, redis_db):
    custom_keyboard = [["Новый вопрос"], ["Мой счёт"]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(
        text="Привет, я бот для викторин!", reply_markup=reply_markup
    )
    redis_db.set(f"{update.message.chat_id}:tgscore", 0)
    return QUESTION


def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    load_dotenv()
    TG_API_TOKEN = os.environ["TG_API"]

    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
    REDIS_DB_NUM = os.environ.get("REDIS_DB_NUM", 0)

    redis_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_NUM)

    updater = Updater(TG_API_TOKEN)
    dp = updater.dispatcher


    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", partial(start, redis_db=redis_db))],
        states={
            QUESTION: [
                MessageHandler(Filters.regex(r"Новый вопрос"), partial(send_question, redis_db=redis_db)),
                MessageHandler(Filters.regex(r"Мой счёт"), partial(get_score, redis_db=redis_db)),
            ],
            RETRY_QUESTION: [
                MessageHandler(Filters.regex(r"Попробовать еще раз"), partial(retry_question, redis_db=redis_db)),
                MessageHandler(Filters.regex(r"Мой счёт"), partial(get_score, redis_db=redis_db)),
                MessageHandler(Filters.regex(r"Сдаться"), partial(give_up, redis_db=redis_db)),
            ],
            ANSWER: [
                MessageHandler(Filters.regex(r"Сдаться"), partial(give_up, redis_db=redis_db)),
                MessageHandler(Filters.regex(r"Мой счёт"), partial(get_score, redis_db=redis_db)),
                MessageHandler(Filters.text, partial(accept_answer, redis_db=redis_db)),
            ],
        },
        fallbacks=[],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
