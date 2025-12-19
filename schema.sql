-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tg_id BIGINT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT CHECK (role IN ('worker', 'manager')) DEFAULT 'worker'
);

-- Таблица статусов
CREATE TABLE IF NOT EXISTS statuses (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    status TEXT CHECK (status IN ('office', 'remote', 'sick', 'vacation')),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, date)
);
