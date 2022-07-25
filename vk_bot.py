import random
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from dotenv import load_dotenv
import os
import json
import redis
from tg_bot import get_question_by_id, check_answer, get_random_question

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
REDIS_DB_NUM = os.environ.get("REDIS_DB_NUM", 0)

redis_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_NUM)

QUESTION, ANSWER, RETRY_QUESTION = range(3)


def greeting(vk_api, user_id):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Новый вопрос", color=VkKeyboardColor.POSITIVE)

    vk_api.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message="Привет, я бот для викторины",
    )


def send_random_question(vk_api, user_id):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Мой счет", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Сдаюсь", color=VkKeyboardColor.NEGATIVE)

    question_block, file_name = get_random_question()
    vk_api.messages.send(
        user_id=user_id,
        message=question_block["question"],
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
    )
    return f'{file_name}:{question_block["id"]}'


def send_score(vk_api, user_id, keyboard):
    # keyboard = VkKeyboard(one_time=True)
    # keyboard.add_button("Новый вопрос", color=VkKeyboardColor.POSITIVE)
    # keyboard.add_line()
    # keyboard.add_button("Мой счет", color=VkKeyboardColor.PRIMARY)
    score = int(redis_db.get(f"{user_id}:vkscore"))
    vk_api.messages.send(
        user_id=user_id,
        message=f"Вы ответили правильно на {score} вопросов",
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
    )


def give_up(vk_api, user_id):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Новый вопрос", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("Мой счет", color=VkKeyboardColor.PRIMARY)

    answer = get_question_by_id(redis_db.get(f"{user_id}:vklast"))["answer"]
    vk_api.messages.send(
        user_id=user_id,
        message=f"Вы сдались ☹️ правильный ответ был:\n {answer}",
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
    )


def accept_answer(vk_api, user_id):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Новый вопрос", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("Мой счет", color=VkKeyboardColor.PRIMARY)

    vk_api.messages.send(
        user_id=user_id,
        message=f"Правильный ответ!",
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
    )


def decline_answer(vk_api, user_id):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Попробовать еще раз", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("Мой счет", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Сдаюсь", color=VkKeyboardColor.NEGATIVE)

    vk_api.messages.send(
        user_id=user_id,
        message=f"Неправильный ответ",
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
    )


def retry_question(vk_api, user_id):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Мой счет", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Сдаюсь", color=VkKeyboardColor.NEGATIVE)

    question_block = get_question_by_id(redis_db.get(f"{user_id}:vklast"))

    vk_api.messages.send(
        user_id=user_id,
        message=question_block["question"],
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
    )


def reply(event, vk_api):
    user_id = event.user_id
    bot_state = redis_db.get(f"{user_id}:vkstate")
    if not bot_state:
        greeting(vk_api, user_id)

        redis_db.set(f"{user_id}:vkstate", QUESTION)
        redis_db.set(f"{user_id}:vkscore", 0)
        return

    if int(bot_state) == QUESTION:
        if event.text == "Новый вопрос":
            db_id = send_random_question(vk_api, user_id)
            redis_db.set(f"{user_id}:vklast", db_id)
            redis_db.set(f"{user_id}:vkstate", ANSWER)

        elif event.text == "Мой счет":
            keyboard = VkKeyboard(one_time=True)
            keyboard.add_button("Новый вопрос", color=VkKeyboardColor.POSITIVE)
            keyboard.add_line()
            keyboard.add_button("Мой счет", color=VkKeyboardColor.PRIMARY)

            send_score(vk_api, user_id, keyboard)

        return

    if int(bot_state) == ANSWER:
        if event.text == "Мой счет":
            keyboard = VkKeyboard(one_time=True)
            keyboard.add_button("Мой счет", color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button("Сдаюсь", color=VkKeyboardColor.NEGATIVE)

            send_score(vk_api, user_id, keyboard)

        elif event.text == "Сдаюсь":
            give_up(vk_api, user_id)
            redis_db.set(f"{user_id}:vkstate", QUESTION)

        else:
            answer = get_question_by_id(redis_db.get(f"{user_id}:vklast"))["answer"]
            result = check_answer(event.text, answer)

            if result:
                accept_answer(vk_api, user_id)
                redis_db.set(f"{user_id}:vkstate", QUESTION)
                redis_db.incr(f"{user_id}:vkscore")

            else:
                decline_answer(vk_api, user_id)
                redis_db.set(f"{user_id}:vkstate", RETRY_QUESTION)
        return

    if int(bot_state) == RETRY_QUESTION:
        if event.text == "Попробовать еще раз":
            retry_question(vk_api, user_id)
            redis_db.set(f"{user_id}:vkstate", ANSWER)

        elif event.text == "Мой счет":
            keyboard = VkKeyboard(one_time=True)
            keyboard.add_button("Попробовать еще раз", color=VkKeyboardColor.POSITIVE)
            keyboard.add_line()
            keyboard.add_button("Мой счет", color=VkKeyboardColor.PRIMARY)
            keyboard.add_line()
            keyboard.add_button("Сдаюсь", color=VkKeyboardColor.NEGATIVE)

            send_score(vk_api, user_id, keyboard)

        elif event.text == "Сдаюсь":
            give_up(vk_api, user_id)
            redis_db.set(f"{user_id}:vkstate", QUESTION)


def main():
    load_dotenv()
    vk_session = VkApi(token=os.environ["VK_API_KEY"])
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            reply(event, vk_api)


if __name__ == "__main__":
    main()
