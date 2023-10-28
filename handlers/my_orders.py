from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
from bot import dp, bot
from db.models import DATABASE
from handlers.user import get_post_registration_keyboard
from db.database import get_user_balance

@dp.callback_query_handler(lambda c: c.data == 'my_orders')
async def show_my_orders(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Получаем заказы пользователя из базы данных
    orders = await get_orders_by_user(user_id)
    
    # Если у пользователя нет заказов
    if not orders:
        await bot.edit_message_text("У вас пока нет заказов.", chat_id=user_id, message_id=callback_query.message.message_id)
        return
    
    keyboard = InlineKeyboardMarkup()
    
    # Добавляем заказы в меню
    for order in orders:
        order_id = order["order_id"]
        subject = order["subject"]
        deadline = order["deadline"]
        price = order["price"]

        button_text = f"#{order_id} | 📕{subject} | ⏰{deadline}"
        keyboard.add(InlineKeyboardButton(button_text, callback_data=f"order_details_{order['order_id']}"))
    
    # Добавляем кнопку "Назад"
    keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_main_menu"))
    
    await bot.edit_message_text("Ваши заказы:", chat_id=user_id, message_id=callback_query.message.message_id, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'back_to_main_menu')
async def back_to_main_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    current_balance = await get_user_balance(user_id)
    post_registration_keyboard = get_post_registration_keyboard(current_balance)
    await bot.edit_message_text("🚀 Добро пожаловать в лучший помощник для студентов!\n\nВыберите действие:", chat_id=user_id, message_id=callback_query.message.message_id, reply_markup=post_registration_keyboard)


async def get_orders_by_user(user_id: int) -> list:
    orders = []
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute(
            """
            SELECT order_id, subject, deadline, price 
            FROM orders 
            WHERE user_id = ?
            """,
            (user_id,)
        )
        rows = await cursor.fetchall()
        columns = ["order_id", "subject", "deadline", "price"]
        
        for row in rows:
            orders.append(dict(zip(columns, row)))

    return orders

@dp.callback_query_handler(lambda c: c.data.startswith('order_details_'))
async def order_details(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[-1])
    
    # Получаем детали заказа из базы данных
    order_data = await get_order_from_db(order_id)

    # Формируем текст для вывода деталей заказа
    details_text = f"""
Order ID: #{str(order_id).zfill(6)}
Предмет: {order_data["subject"]}
Описание: {order_data["description"]}
Дедлайн: {order_data["deadline"]}
Бюджет: {order_data["price"]}
    """

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Связаться с исполнителем", callback_data=f"connect_to_assistant{order_id}"))
    keyboard.add(InlineKeyboardButton("Назад к списку заказов", callback_data="my_orders"))
    
    await bot.edit_message_text(details_text, chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=keyboard)

async def get_order_from_db(order_id: int) -> dict:
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute(
            """
            SELECT user_id, subject, description, deadline, price 
            FROM orders 
            WHERE order_id = ?
            """,
            (order_id,)
        )
        order_data = await cursor.fetchone()
        
        if order_data:
            columns = ["user_id", "subject", "description", "deadline", "price"]
            return dict(zip(columns, order_data))
        
        return None


