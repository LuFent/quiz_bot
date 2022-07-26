import re
import os
import argparse
from pathlib import Path
import json
import redis
from dotenv import load_dotenv


def normalize_questions(questions_text, start_id):
    question_reg_selector = r"Вопрос \d*:\n([\s\S]*?)\n\nОтвет:"
    answer_reg_selector = r"Ответ:\n(.*)\n"

    questions = re.findall(question_reg_selector, questions_text)
    answers = re.findall(answer_reg_selector, questions_text)
    questions_blocks = [
        {
            "id": number + start_id,
            "question": question.replace("\n", " "),
            "answer": answer,
        }
        for number, question, answer in zip(range(len(questions)), questions, answers)
    ]
    return questions_blocks


def save_dict_to_redis(dicts, redis_db):
    for question_block in dicts:
        block_name = f'question:{question_block["id"]}'
        redis_db.set(block_name, json.dumps(question_block, ensure_ascii=False))

    redis_db.set("question:last", dicts[-1]["id"])


def main():
    load_dotenv()

    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
    REDIS_DB_NUM = os.environ.get("REDIS_DB_NUM", 0)

    redis_db = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_NUM, decode_responses=True
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--file_path", help="text-file dir")
    parser.add_argument("--dir_path", help="text-file dir")
    file_path = parser.parse_args().file_path
    dir_path = parser.parse_args().dir_path
    files = []
    if dir_path:
        dir_path = [os.path.join(dir_path, file) for file in os.listdir(dir_path)]
        files.extend(dir_path)
    if file_path:
        files.append(os.listdir(dir_path))

    Path("questions-json").mkdir(parents=True, exist_ok=True)
    full_answers_by_questions = []
    last_id = redis_db.get("question:last")
    if not last_id:
        last_id = 1

    for file in files:
        with open(file, encoding="KOI8-R") as f:
            answers_by_questions = normalize_questions(f.read(), last_id)
            full_answers_by_questions.extend(answers_by_questions)
            last_id = answers_by_questions[-1]["id"] + 1

    save_dict_to_redis(full_answers_by_questions, redis_db)


if __name__ == "__main__":
    main()
