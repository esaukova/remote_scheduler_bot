import asyncpg
from datetime import date
from pathlib import Path

class Database:
    def __init__(self, config):
        self.config = config
        self.pool = None

    # Подключение к БД
    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                **self.config,
                command_timeout=60
            )
            await self.init_schema()
            print("Подключено к PostgreSQL")
        except Exception as e:
            print(f"Ошибка подключения к PostgreSQL: {e}")
            raise

    # Инициализация структуры из schema.sql
    async def init_schema(self):
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            print("Файл schema.sql не найден, пропускаю инициализацию.")
            return

        sql = schema_path.read_text(encoding="utf-8")
        async with self.pool.acquire() as conn:
            await conn.execute(sql)
        print("Таблицы успешно инициализированы (schema.sql).")

    # Добавление пользователя
    async def add_user(self, tg_id, name, role='worker'):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (tg_id, name, role)
                VALUES ($1, $2, $3)
                ON CONFLICT (tg_id) DO NOTHING
            """, tg_id, name, role)

    # Получение пользователя
    async def get_user(self, tg_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM users WHERE tg_id=$1", tg_id)

    # Запись статуса (с обновлением при повторе)
    async def set_status(self, tg_id, status):
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow("SELECT id FROM users WHERE tg_id=$1", tg_id)
            if not user:
                return False
            await conn.execute("""
                INSERT INTO statuses (user_id, date, status)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, date) DO UPDATE SET status=$3
            """, user["id"], date.today(), status)
            return True

    # Получение статуса пользователя за сегодня
    async def get_user_today_status(self, tg_id):
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow("SELECT id FROM users WHERE tg_id=$1", tg_id)
            if not user:
                return None
            status = await conn.fetchrow("""
                SELECT status FROM statuses
                WHERE user_id=$1 AND date=CURRENT_DATE
            """, user["id"])
            return status  # будет None, если нет записи, иначе {'status': 'office'}

    # Получение всех статусов за сегодня
    async def get_today_statuses(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("""
                SELECT u.name, s.status
                FROM statuses s
                JOIN users u ON s.user_id = u.id
                WHERE s.date = CURRENT_DATE
                ORDER BY u.name
            """)

    # Фильтрация по статусу (например, /filter remote)
    async def filter_by_status(self, status):
        async with self.pool.acquire() as conn:
            return await conn.fetch("""
                SELECT u.name
                FROM statuses s
                JOIN users u ON s.user_id = u.id
                WHERE s.date = CURRENT_DATE AND s.status=$1
            """, status)

    # Подсчёт процента присутствующих в офисе
    async def get_office_percent(self):
        async with self.pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM statuses WHERE date=CURRENT_DATE")
            office = await conn.fetchval("""
                SELECT COUNT(*) FROM statuses
                WHERE date=CURRENT_DATE AND status='office'
            """)
            percent = round(office / total * 100, 1) if total else 0.0
            return (office, total, percent)
