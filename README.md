# Вк и Tg боты для викторины на Python

## Как загрузить вопросы

Файлы с вопросами хранятся в Базе данных Redis как строка с json:
```
[
{
  "id": <id вопроса в данном файле>,
  "question": <текст вопроса>,
   "answer": <текст ответа>
},
...
]
```

Например:

```
[
{
  "id": 1,
  "question": "Зимой и летом одним цветом",
  "answer": "Ёлка"
}
]
```
* Кирилица в Redis кодируется, так что на деле не все так красиво


Можно воспользоваться скриптом **dump_to_redis.py**, и загрузить вопросы из [архива](https://dvmn.org/media/modules_dist/quiz-questions.zip) в базу данных

Для этого нужно выполнить команду

```
python3 dump_to_json.py --file_path <Путь до txt файла>
```

Или

```
python3 dump_to_json.py --dir_path <Папка с txt файлами>
```


## Как запустить ботов на Пк
* Скачать репозиторий с кодом

* Скачайте python3.8

* Создать .env файл с содержанием:
```
TG_API=<Токен тг бота>
VK_API_KEY=<Токен вк бота>
REDIS_HOST=<Хост бд Redis>
REDIS_PORT=<Порт бд Redis>
REDIS_DB_NUM=<Номер бд Redis>
```
Настройки бд на Redis - опциональны, по дефолту 0-ая бд на локалхосте(127.0.0.1:6379)


* Скачать зависимости командой:
```
pip3 install -r requirements.txt
```

* Запустить ботов командами
```
python3 tg_bot.py
```
И
```
python3 vk_bot.py
```
Также в репозитории лежит Procfile для деплоя на Хероку
