import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

from config import BOT_TOKEN, ADMIN_ID, ADMIN_USERNAME, DB_CONFIG
from db import Database

router = Router()
db = Database(DB_CONFIG)

STATUSES = {
    "office": "Офис",
    "remote": "Удалёнка",
    "vacation": "Отпуск",
    "sick": "Больничный"
}

# Клавиатура в Телеграмм

def simple_kb(*buttons):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b)] for b in buttons],
        resize_keyboard=True
    )

employee_kb = simple_kb("Отметить статус", "Мой статус")
admin_kb = simple_kb("Все статусы", "Процент в офисе", "Фильтр по статусу")
status_kb = simple_kb(*STATUSES.values(), "Назад")

# Первичный запуск

def is_admin(msg: Message) -> bool:
    return msg.from_user.id == ADMIN_ID or msg.from_user.username == ADMIN_USERNAME

def get_status_code(title: str):
    for code, name in STATUSES.items():
        if name == title:
            return code
    return None

def get_status_title(code: str):
    return STATUSES.get(code, code)

@router.message(Command("start"))
async def start(msg: Message):
    if is_admin(msg):
        await msg.answer("Добро пожаловать, администратор", reply_markup=admin_kb)
    else:
        await msg.answer("Привет! Выберите действие:", reply_markup=employee_kb)

# Функции сотрудника

@router.message(lambda msg: msg.text == "Отметить статус")
async def choose_status(msg: Message):
    await msg.answer("Выберите рабочий статус:", reply_markup=status_kb)

@router.message(lambda msg: msg.text in STATUSES.values())
async def set_status(msg: Message):
    code = get_status_code(msg.text)
    await db.set_status(msg.from_user.id, code)
    await msg.answer(
        f"Статус «{msg.text}» записан\n{datetime.now().date()}",
        reply_markup=employee_kb
    )

@router.message(lambda msg: msg.text == "Мой статус")
async def my_status(msg: Message):
    data = await db.get_user_today_status(msg.from_user.id)
    if data:
        await msg.answer(f"Ваш текущий статус: {get_status_title(data['status'])}")
    else:
        await msg.answer("Сегодня статус ещё не отмечен.")

@router.message(lambda msg: msg.text == "Назад")
async def back(msg: Message):
    await start(msg)

# Функции администратора

@router.message(lambda msg: msg.text == "Все статусы")
async def all_statuses(msg: Message):
    if not is_admin(msg):
        return await msg.answer("Нет доступа.")
    data = await db.get_today_statuses()
    text = "\n".join(f"{r['name']}: {get_status_title(r['status'])}" for r in data)
    await msg.answer(text or "Сегодня данных нет.")

@router.message(lambda msg: msg.text == "Процент в офисе")
async def office_percent(msg: Message):
    if not is_admin(msg):
        return await msg.answer("Нет доступа.")
    office, total, perc = await db.get_office_percent()
    await msg.answer(f"В офисе: {office}/{total} ({perc}%)")

@router.message(lambda msg: msg.text == "Фильтр по статусу")
async def filter_menu(msg: Message):
    if not is_admin(msg):
        return await msg.answer("Нет доступа.")
    await msg.answer("Выберите статус:", reply_markup=status_kb)

# Запуск бота

async def start_bot():
    await db.connect()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())
