import re
import os
import argparse
from pathlib import Path
import json


def normalize_questions(questions_text):
    question_reg_selector = r"Вопрос \d*:\n([\s\S]*?)\n\nОтвет:"
    answer_reg_selector = r"Ответ:\n(.*)\n"

    questions = re.findall(question_reg_selector, questions_text)
    answers = re.findall(answer_reg_selector, questions_text)
    questions_blocks = [
        {"id": number, "question": question.replace("\n", " "), "answer": answer}
        for number, question, answer in zip(
            range(1, len(questions)), questions, answers
        )
    ]
    return questions_blocks


def save_dict_as_json(dict_):
    with open("data.json", "w") as fp:
        json.dump(dict_, fp, ensure_ascii=False, indent=4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_path", help="text-file dir")
    file_path = parser.parse_args().file_path
    Path("questions-json").mkdir(parents=True, exist_ok=True)
    with open(file_path, encoding="KOI8-R") as f:
        answers_by_questions = normalize_questions(f.read())
        save_dict_as_json(answers_by_questions)


if __name__ == "__main__":
    main()
