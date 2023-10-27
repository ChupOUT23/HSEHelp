import datetime
import time
import aiosqlite
from aiogram.utils import exceptions
from aiogram import types
from bot import dp, bot
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from handlers.reshenie_zadach import orders_data, generate_order_menu
from handlers.order_process import OrderForm
from config import MANAGERS_CHAT_ID, RESHALI_CHAT_ID
from db.models import DATABASE

def generate_manager_order_menu(order_id):
    markup = InlineKeyboardMarkup()
    item = InlineKeyboardButton("Удалить", callback_data=f"delete_{order_id}")
    markup.add(item)
    return markup

@dp.message_handler(commands=['test'])
async def create_test_order(message: types.Message):
    # Здесь создаем тестовые данные для заказа
    test_order_data = {
        "subject": "Тестовый предмет",
        "description": "Тестовое описание заказа",
        "deadline": "01.01.2024",
        "check_time": "12:00",
        "price": "1000"
    }

    # Сохранение заказа в базе данных
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute(
            "INSERT INTO orders (user_id, subject, description, deadline, check_time, price) VALUES (?, ?, ?, ?, ?, ?)",
            (message.from_user.id, test_order_data["subject"], test_order_data["description"], test_order_data["deadline"], test_order_data["check_time"], test_order_data["price"])
        )
        await db.commit()

        order_id = str(cursor.lastrowid).zfill(6)

    # Отправка заказа в чат менеджеров
    order_text = f"""
#Order{order_id}
@{message.from_user.username}
Предмет: {test_order_data["subject"]}
Описание: {test_order_data["description"]}
Дедлайн: {test_order_data["deadline"]}
Время проверки: {test_order_data["check_time"]}
Рекомендованная цена: {test_order_data["price"]}
    """
    await bot.send_message(MANAGERS_CHAT_ID, order_text, reply_markup=generate_manager_order_menu(order_id))

    # Отправка заказа в чат исполнителей без указания цены
    order_text_without_price = f"""
#Order{order_id}
@{message.from_user.username}
Предмет: {test_order_data["subject"]}
Описание: {test_order_data["description"]}
Дедлайн: {test_order_data["deadline"]}
Время проверки: {test_order_data["check_time"]}
    """
    await bot.send_message(RESHALI_CHAT_ID, order_text_without_price)
    
    await message.answer("Тестовый заказ успешно создан.")
