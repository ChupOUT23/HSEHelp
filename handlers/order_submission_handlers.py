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
    item1 = InlineKeyboardButton("Удалить (БП)", callback_data=f"delete_without_reason_{order_id}")
    item2 = InlineKeyboardButton("Удалить (Причина)", callback_data=f"delete_reason_{order_id}")
    markup.add(item1, item2)
    return markup

# Обработчик кнопки "Удалить (Причина)"
@dp.callback_query_handler(lambda c: c.data.startswith('delete_reason_'))
async def process_delete_with_reason(callback_query: CallbackQuery):
    order_id = callback_query.data.split("_")[1]
    
    # Запрос причины удаления у менеджера
    await bot.send_message(callback_query.from_user.id, "Пожалуйста, укажите причину удаления заказа.")
    
    # Удаление заказа из базы данных
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute("DELETE FROM orders WHERE order_id=?", (order_id,))
        await db.commit()
    
    # Удаление сообщения с кнопками "Удалить (БП)" и "Удалить (Причина)"
    try:
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    except exceptions.MessageToDeleteNotFound:
        pass
    
    # Уведомление пользователю о удалении с указанием причины
    user_id = orders_data.get(order_id, {}).get("user_id")
    if user_id:
        await bot.send_message(user_id, f"Ваш заказ с номером {order_id} был удален с указанием причины. Причина: {callback_query.message.text}")
    
    # Уведомление менеджеру о удалении заказа
    await bot.send_message(MANAGERS_CHAT_ID, f"Заказ с номером {order_id} был удален с указанием причины. Причина: {callback_query.message.text}")

# Обработчик кнопки "Удалить (БП)"
@dp.callback_query_handler(lambda c: c.data.startswith('delete_without_reason_'))
async def process_delete_without_reason(callback_query: CallbackQuery):
    order_id = callback_query.data.split("_")[1]
    
    # Удаление заказа из базы данных
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute("DELETE FROM orders WHERE order_id=?", (order_id,))
        await db.commit()
    
    # Удаление сообщения с кнопками "Удалить (БП)" и "Удалить (Причина)"
    try:
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    except exceptions.MessageToDeleteNotFound:
        pass
    
    # Уведомление пользователю о удалении без указания причины
    user_id = orders_data.get(order_id, {}).get("user_id")
    if user_id:
        await bot.send_message(user_id, f"Ваш заказ с номером {order_id} был удален без объяснения причины.")
    
    # Уведомление менеджеру о удалении заказа
    await bot.send_message(MANAGERS_CHAT_ID, f"Заказ с номером {order_id} был удален без объяснения причины.")


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

    # Отправка заказа в чат менеджеров
    order_text = f"""
#Order{order_id}
@{callback_query.from_user.username}
Предмет: {orders_data[user_id]["subject"]}
Описание: {orders_data[user_id]["description"]}
Дедлайн: {orders_data[user_id]["deadline"]}
Время проверки: {orders_data[user_id]["check_time"]}
Рекомендованная цена: {orders_data[user_id]["price"]}
    """
    await bot.send_message(MANAGERS_CHAT_ID, order_text, reply_markup=generate_manager_order_menu(order_id))

    # Отправка заказа в чат исполнителей без указания цены
    order_text_without_price = f"""
#Order{order_id}
@{callback_query.from_user.username}
Предмет: {orders_data[user_id]["subject"]}
Описание: {orders_data[user_id]["description"]}
Дедлайн: {orders_data[user_id]["deadline"]}
Время проверки: {orders_data[user_id]["check_time"]}
    """
    await bot.send_message(RESHALI_CHAT_ID, order_text_without_price)


# Отправляем прикрепленные файлы

    for file_id in orders_data[user_id]['files']:
        await bot.send_document(MANAGERS_CHAT_ID, file_id)
        await bot.send_document(RESHALI_CHAT_ID, file_id)

    await state.finish()
    await bot.send_message(user_id, "Ваш заказ был успешно отправлен!\n\n Вы можете следить за статусом ваших заказов во вкладке Мои заказы")