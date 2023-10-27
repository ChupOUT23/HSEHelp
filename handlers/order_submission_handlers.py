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
from aiogram.dispatcher.filters.state import State, StatesGroup

# ... Ваши импорты ...

class DeleteOrderState(StatesGroup):
    waiting_for_reason = State()

def generate_manager_order_menu(order_id):
    markup = InlineKeyboardMarkup()
    item = InlineKeyboardButton("Удалить", callback_data=f"delete_{order_id}")
    markup.add(item)
    return markup

@dp.callback_query_handler(lambda c: c.data.startswith('delete_'))
async def ask_for_delete_reason(callback_query: CallbackQuery):
    order_id = callback_query.data.split("_")[1]
    markup = InlineKeyboardMarkup()
    item1 = InlineKeyboardButton("Без причины", callback_data=f"delete_without_reason_{order_id}")
    item2 = InlineKeyboardButton("Указать причину", callback_data=f"delete_with_reason_{order_id}")
    markup.add(item1, item2)
    await bot.edit_message_text("Выберите причину удаления:", callback_query.from_user.id, callback_query.message.message_id, reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith('delete_without_reason_'))
async def process_delete_without_reason(callback_query: CallbackQuery):
    order_id = callback_query.data.split("_")[1]
    user_id = orders_data.get(order_id, {}).get("user_id")
    if user_id:
        await bot.send_message(user_id, f"Ваш заказ с номером {order_id} был удален без указания причины.")
    await delete_order_from_chats_and_database(order_id)

@dp.callback_query_handler(lambda c: c.data.startswith('delete_with_reason_'))
async def ask_for_reason(callback_query: CallbackQuery, state: FSMContext):
    order_id = callback_query.data.split("_")[1]
    await DeleteOrderState.waiting_for_reason.set()
    await state.update_data(order_id=order_id)
    await bot.send_message(callback_query.message.chat.id, "Пожалуйста, напишите причину удаления заказа в этом чате.")

@dp.message_handler(state=DeleteOrderState.waiting_for_reason, content_types=types.ContentTypes.TEXT)
async def process_delete_with_reason(message: types.Message, state: FSMContext):
    reason = message.text
    user_data = await state.get_data()
    order_id = user_data.get('order_id')

    user_id = orders_data.get(order_id, {}).get("user_id")
    if user_id:
        await bot.send_message(user_id, f"Ваш заказ с номером {order_id} был удален. Причина: {reason}")

    await delete_order_from_chats_and_database(order_id)
    await state.finish()

async def delete_order_from_chats_and_database(order_id):
    manager_message_id = orders_data.get(order_id, {}).get("manager_message_id")
    assistance_message_id = orders_data.get(order_id, {}).get("assistance_message_id")

    try:
        if manager_message_id:
            await bot.delete_message(MANAGERS_CHAT_ID, manager_message_id)
        if assistance_message_id:
            await bot.delete_message(RESHALI_CHAT_ID, assistance_message_id)
    except exceptions.MessageToDeleteNotFound:
        pass

    # Удаление заказа из базы данных
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute("DELETE FROM orders WHERE order_id=?", (order_id,))
        await db.commit()

@dp.callback_query_handler(lambda c: c.data == 'order_complite', state="*")
async def process_order(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_data = await state.get_data()
    
    # Добавлено логирование:
    print(f"Current user_id: {user_id}")
    print(f"Orders data: {orders_data}")
    
    if user_id not in orders_data:
        await bot.send_message(user_id, "Ошибка при обработке заказа. Пожалуйста, попробуйте еще раз.")
        return

    # Сохранение заказа в базе данных
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute(
            "INSERT INTO orders (user_id, subject, description, deadline, check_time, price) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, orders_data[user_id]["subject"], orders_data[user_id]["description"], orders_data[user_id]["deadline"], orders_data[user_id]["check_time"], orders_data[user_id]["price"])
        )
        await db.commit()

        order_id = str(cursor.lastrowid).zfill(6)

    # Отправка заказа в чат менеджеров и сохранение message_id
    order_text = f"""
#Order{order_id}
@{callback_query.from_user.username}
Предмет: {orders_data[user_id]["subject"]}
Описание: {orders_data[user_id]["description"]}
Дедлайн: {orders_data[user_id]["deadline"]}
Время проверки: {orders_data[user_id]["check_time"]}
Рекомендованная цена: {orders_data[user_id]["price"]}
    """
    manager_message = await bot.send_message(MANAGERS_CHAT_ID, order_text, reply_markup=generate_manager_order_menu(order_id))

    # Отправка заказа в чат исполнителей без указания цены и сохранение message_id
    order_text_without_price = f"""
#Order{order_id}
@{callback_query.from_user.username}
Предмет: {orders_data[user_id]["subject"]}
Описание: {orders_data[user_id]["description"]}
Дедлайн: {orders_data[user_id]["deadline"]}
Время проверки: {orders_data[user_id]["check_time"]}
    """
    assistance_message = await bot.send_message(RESHALI_CHAT_ID, order_text_without_price)

    # Обновляем orders_data с message_id
    orders_data[order_id]["manager_message_id"] = manager_message.message_id
    orders_data[order_id]["assistance_message_id"] = assistance_message.message_id

    # Отправляем прикрепленные файлы
    for file_id in orders_data[user_id]['files']:
        await bot.send_document(MANAGERS_CHAT_ID, file_id)
        await bot.send_document(RESHALI_CHAT_ID, file_id)

    await state.finish()
    await bot.send_message(user_id, "Ваш заказ был успешно отправлен!\n\n Вы можете следить за статусом ваших заказов во вкладке Мои заказы")

