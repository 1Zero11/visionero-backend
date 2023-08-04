# visionero-backend

+ Запустить бд postgres. Я запускаю через docker
`docker run -d --name manager-postgres -p 5432:5432 -e POSTGRES_DB=run -e POSTGRES_USER=run -e POSTGRES_PASSWORD=password postgres`

+ Запустить бэк
+ Запустить фронт https://github.com/1Zero11/visionero-front

Команда для сборки `python -m nuitka --follow-imports --onefile main.py`
