import re
import os
import argparse
from pathlib import Path
import json
from pprint import pprint


def normalize_questions(questions_text, start_id):
    question_reg_selector = r"Вопрос \d*:\n([\s\S]*?)\n\nОтвет:"
    answer_reg_selector = r"Ответ:\n(.*)\n"

    questions = re.findall(question_reg_selector, questions_text)
    answers = re.findall(answer_reg_selector, questions_text)
    questions_blocks = [
        {"id": number, "question": question.replace("\n", " "), "answer": answer}
        for number, question, answer in zip(
            range(start_id, len(questions)), questions, answers
        )
    ]
    return questions_blocks, len(questions)


def save_dict_as_json(dict_):
    file_name = f"q_{len(os.listdir('questions-json'))}.json"

    with open(os.path.join('questions-json', file_name), "w") as fp:
        json.dump(dict_, fp, ensure_ascii=False, indent=4)


def main():
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
    last_id = 1
    for file in files:
        with open(file, encoding="KOI8-R") as f:
            answers_by_questions, last_id = normalize_questions(f.read(), last_id)
            full_answers_by_questions.extend(answers_by_questions)

    save_dict_as_json(full_answers_by_questions)


if __name__ == "__main__":
    main()
