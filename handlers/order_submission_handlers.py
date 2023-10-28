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

# Function to delete the order from the database based on the provided order_id
async def delete_order_from_db(order_id):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute(
            """
            DELETE FROM orders WHERE order_id = ?
            """,
            (order_id,)
        )
        await db.commit()

# Function to fetch the order data from the database based on the provided order_id
async def get_order_from_db(order_id):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute(
            """
            SELECT user_id, manager_message_order, assistance_message_order, 
                   manager_chat_file_id, assistance_chat_file_id 
            FROM orders WHERE order_id = ?
            """,
            (order_id,)
        )
        order_data = await cursor.fetchone()
        if order_data:
            # If order data is found, convert it to a dictionary
            columns = ["user_id", "manager_message_order", "assistance_message_order", "manager_chat_file_id", "assistance_chat_file_id"]
            return dict(zip(columns, order_data))
        return None  # Return None if no order data is found


def generate_manager_order_menu(order_id):
    markup = InlineKeyboardMarkup()
    item1 = InlineKeyboardButton("Удалить", callback_data=f"delete_without_reason_{order_id}")
    markup.add(item1)
    return markup

def generate_delete_confirmation_menu(order_id):
    markup = InlineKeyboardMarkup()
    item1 = InlineKeyboardButton("БП", callback_data=f"delete_b_p_confirm_{order_id}")
    item2 = InlineKeyboardButton("Причина", callback_data=f"delete_with_reason_{order_id}")
    item3 = InlineKeyboardButton("Назад", callback_data=f"back_to_order_{order_id}")
    
    markup.add(item1, item2, item3)
    return markup

# Function to update the order in the database with the provided message IDs
async def update_order_in_db(order_id, manager_message_order, assistance_message_order, manager_chat_file_id, assistance_chat_file_id):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute(
            """
            UPDATE orders 
            SET manager_message_order = ?, 
                assistance_message_order = ?, 
                manager_chat_file_id = ?, 
                assistance_chat_file_id = ? 
            WHERE order_id = ?
            """,
            (manager_message_order, assistance_message_order, manager_chat_file_id, assistance_chat_file_id, order_id)
        )
        await db.commit()

# Callback handler for the "Back" button
@dp.callback_query_handler(lambda c: c.data.startswith('back_to_order_'))
async def back_to_order(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[-1])
    await callback_query.message.edit_reply_markup(reply_markup=generate_manager_order_menu(order_id))

# Callback handler for the initial "Delete" button
@dp.callback_query_handler(lambda c: c.data.startswith('delete_without_reason_'))
async def delete_without_reason(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[-1])
    await callback_query.message.edit_reply_markup(reply_markup=generate_delete_confirmation_menu(order_id))

# Updated callback handler for the "Delete (Without Reason)" button
@dp.callback_query_handler(lambda c: c.data.startswith('delete_b_p_confirm_'))
async def delete_without_reason_confirm(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[-1])
    
    # Fetch the order data from the database
    order_data = await get_order_from_db(order_id)
    print(order_data)
    # Send a message to the user who created the order
    await bot.send_message(order_data["user_id"], f"Ваш заказ с ID #{str(order_id).zfill(6)} признали некорректным, он удален без объяснения причины.")
    
    # Delete the corresponding messages from the managers and assistants chats
    await bot.delete_message(MANAGERS_CHAT_ID, order_data["manager_message_order"])
    await bot.delete_message(RESHALI_CHAT_ID, order_data["assistance_message_order"])
    
    # Delete the file messages from the chats
    await bot.delete_message(MANAGERS_CHAT_ID, order_data["manager_chat_file_id"])
    await bot.delete_message(RESHALI_CHAT_ID, order_data["assistance_chat_file_id"])

    # Delete the callback query message
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    # Delete the order from the database
    await delete_order_from_db(order_id)

# Для хранения временной информации о причине удаления
DELETE_REASONS = {}

@dp.callback_query_handler(lambda c: c.data.startswith('delete_with_reason_'))
async def delete_with_reason(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[-1])
    DELETE_REASONS[callback_query.from_user.id] = order_id
    sent_message = await bot.send_message(MANAGERS_CHAT_ID, "Пожалуйста, напишите причину удаления заказа:")
    DELETE_REASONS["sent_message_id"] = sent_message.message_id  # Сохраняем ID отправленного сообщения
    DELETE_REASONS["callback_message_id"] = callback_query.message.message_id


@dp.message_handler(lambda message: message.chat.id == MANAGERS_CHAT_ID)
async def receive_delete_reason(message: types.Message):
    print(f"Received reason in managers chat: {message.text}")
    print(f"DELETE_REASONS content: {DELETE_REASONS}")

    # Предполагаем, что менеджер, который инициировал удаление, является тем, кто отвечает причиной
    order_id = DELETE_REASONS.get(message.from_user.id)
    if not order_id:
        return  # Если ID заказа не найден, ничего не делаем

    # Получаем данные заказа из базы данных
    order_data = await get_order_from_db(order_id)
    
    # Отправляем сообщение пользователю, который создал заказ
    await bot.send_message(order_data["user_id"], f"Ваш заказ с ID #{str(order_id).zfill(6)} был удален по причине: {message.text}")
    
    # Удаляем соответствующие сообщения из чатов менеджеров и исполнителей
    await bot.delete_message(MANAGERS_CHAT_ID, order_data["manager_message_order"])
    await bot.delete_message(RESHALI_CHAT_ID, order_data["assistance_message_order"])
    
    # Удаляем файлы из чатов
    await bot.delete_message(MANAGERS_CHAT_ID, order_data["manager_chat_file_id"])
    await bot.delete_message(RESHALI_CHAT_ID, order_data["assistance_chat_file_id"])

    # Удаляем сообщение "Пожалуйста, напишите причину удаления заказа"
    await bot.delete_message(MANAGERS_CHAT_ID, DELETE_REASONS.get("sent_message_id"))
    # Удаляем сообщение с причиной
    await bot.delete_message(MANAGERS_CHAT_ID, message.message_id)
    # Удаляем меню с кнопками
    await bot.delete_message(MANAGERS_CHAT_ID, DELETE_REASONS.get("callback_message_id"))
    # Удаляем заказ из базы данных
    await delete_order_from_db(order_id)
    
    # Удаляем запись из DELETE_REASONS после обработки
    del DELETE_REASONS[message.from_user.id]


@dp.callback_query_handler(lambda c: c.data == 'order_complite', state="*")
async def process_order(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_data = await state.get_data()
 	# Добавлено логирование:
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
    manager_message = await bot.send_message(MANAGERS_CHAT_ID, order_text)
    manager_message_order = manager_message.message_id
    print (manager_message_order)

    # Отправка заказа в чат исполнителей без указания цены
    order_text_without_price = f"""
#Order{order_id}
@{callback_query.from_user.username}
Предмет: {orders_data[user_id]["subject"]}
Описание: {orders_data[user_id]["description"]}
Дедлайн: {orders_data[user_id]["deadline"]}
Время проверки: {orders_data[user_id]["check_time"]}
    """
    assistance_message = await bot.send_message(RESHALI_CHAT_ID, order_text_without_price)
    assistance_message_order = assistance_message.message_id
    print (assistance_message_order)

# Отправляем прикрепленные файлы

    for file_id in orders_data[user_id]['files']:
        manager_file = await bot.send_document(MANAGERS_CHAT_ID, file_id)
        manager_chat_file_id = manager_file.message_id
        print(manager_chat_file_id)

        assistance_file = await bot.send_document(RESHALI_CHAT_ID, file_id)
        assistance_chat_file_id = assistance_file.message_id
        print(assistance_chat_file_id)
    
    await bot.send_message(MANAGERS_CHAT_ID, "Управление заказом:", reply_markup=generate_manager_order_menu(order_id))

    await update_order_in_db(order_id, manager_message_order, assistance_message_order, manager_chat_file_id, assistance_chat_file_id)
    await state.finish()
    await bot.send_message(user_id, "Ваш заказ был успешно отправлен!\n\n Вы можете следить за статусом ваших заказов во вкладке Мои заказы")
