import os
import random
import re
import json


def get_random_question(redis_db):
    last_id = redis_db.get("question:last")
    question_id = random.randrange(1, int(last_id))
    question_block = redis_db.get(f"question:{question_id}")
    return json.loads(question_block)


def get_question_by_id(redis_db, question_id):
    question_id = f"question:{int(question_id)}"
    question_block = redis_db.get(question_id)
    return json.loads(question_block)


def check_answer(user_answer, right_answer):
    # Requires revision
    right_answers = []
    try:
        right_answers.append(re.findall(r"(.*?)[\.\(\!,]", right_answer)[0].strip())
    except IndexError:
        pass

    right_answers.append(right_answer)

    return user_answer in right_answers
