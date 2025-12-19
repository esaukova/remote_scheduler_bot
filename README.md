# Remote Job Bot

Telegram бот для отметки статусов сотрудников.

[@remote_job_schedule_bot](https://t.me/remote_job_schedule_bot)

```bash
# 1. Клонировать проект
git clone https://github.com/esaukova/remote_scheduler_bot
cd remotejobbot

# 2. Настроить переменные окружения
echo "ADMIN_ID=ваш_id" >> .env
echo "ADMIN_USERNAME=ваш_username" >> .env

# 3. Запустить
docker-compose up