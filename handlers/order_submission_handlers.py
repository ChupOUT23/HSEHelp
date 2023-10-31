import json
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

async def delete_order_from_db(order_id):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute(
            "DELETE FROM orders WHERE order_id = ?",
            (order_id,)
        )
        await db.commit()

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
            columns = ["user_id", "manager_message_order", "assistance_message_order", "manager_chat_file_id", "assistance_chat_file_id"]
            order_dict = dict(zip(columns, order_data))
            order_dict["manager_chat_file_id"] = json.loads(order_dict["manager_chat_file_id"])
            order_dict["assistance_chat_file_id"] = json.loads(order_dict["assistance_chat_file_id"])
            return order_dict
        return None

def generate_manager_order_menu(order_id):
    markup = InlineKeyboardMarkup()
    item1 = InlineKeyboardButton("Удалить", callback_data=f"delete_without_reason_{order_id}")
    markup.add(item1)
    return markup

def generate_response_menu(order_id):
    markup = InlineKeyboardMarkup()
    item1 = InlineKeyboardButton("Откликнуться", callback_data=f"respond_{order_id}")
    markup.add(item1)
    return markup

def generate_delete_confirmation_menu(order_id):
    markup = InlineKeyboardMarkup()
    item1 = InlineKeyboardButton("БП", callback_data=f"delete_b_p_confirm_{order_id}")
    item2 = InlineKeyboardButton("Причина", callback_data=f"delete_with_reason_{order_id}")
    item3 = InlineKeyboardButton("Назад", callback_data=f"back_to_order_{order_id}")
    markup.add(item1, item2, item3)
    return markup

async def update_order_in_db(order_id, manager_message_order, assistance_message_order, manager_chat_file_ids, assistance_chat_file_ids):
    manager_chat_file_id_str = json.dumps(manager_chat_file_ids)
    assistance_chat_file_id_str = json.dumps(assistance_chat_file_ids)
    
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
            (manager_message_order, assistance_message_order, manager_chat_file_id_str, assistance_chat_file_id_str, order_id)
        )
        await db.commit()

@dp.callback_query_handler(lambda c: c.data.startswith('back_to_order_'))
async def back_to_order(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[-1])
    await callback_query.message.edit_reply_markup(reply_markup=generate_manager_order_menu(order_id))

@dp.callback_query_handler(lambda c: c.data.startswith('delete_without_reason_'))
async def delete_without_reason(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[-1])
    await callback_query.message.edit_reply_markup(reply_markup=generate_delete_confirmation_menu(order_id))

@dp.callback_query_handler(lambda c: c.data.startswith('delete_b_p_confirm_'))
async def delete_without_reason_confirm(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[-1])
    order_data = await get_order_from_db(order_id)
    await bot.send_message(order_data["user_id"], f"Ваш заказ с ID #{str(order_id).zfill(6)} признали некорректным, он удален без объяснения причины.")
    await bot.delete_message(MANAGERS_CHAT_ID, order_data["manager_message_order"])
    await bot.delete_message(RESHALI_CHAT_ID, order_data["assistance_message_order"])
    for file_id in order_data["manager_chat_file_id"]:
        await bot.delete_message(MANAGERS_CHAT_ID, file_id)
    for file_id in order_data["assistance_chat_file_id"]:
        await bot.delete_message(RESHALI_CHAT_ID, file_id)

    # Удаляем меню с кнопкой "Откликнуться" в чате исполнителей
    last_assistance_file_id = order_data["assistance_chat_file_id"][-1]
    await bot.delete_message(RESHALI_CHAT_ID, last_assistance_file_id + 1)

    # Удаляем меню с кнопками в чате менеджеров
    last_manager_file_id = order_data["manager_chat_file_id"][-1]
    await bot.delete_message(MANAGERS_CHAT_ID, last_manager_file_id + 1)

    
    await delete_order_from_db(order_id)

DELETE_REASONS = {}

@dp.callback_query_handler(lambda c: c.data.startswith('delete_with_reason_'))
async def delete_with_reason(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[-1])
    sent_message = await bot.send_message(MANAGERS_CHAT_ID, "Пожалуйста, напишите причину удаления заказа:")
    
    DELETE_REASONS[callback_query.from_user.id] = {
        "order_id": order_id,
        "sent_message_id": sent_message.message_id,
        "callback_message_id": callback_query.message.message_id
    }

@dp.message_handler(lambda message: message.chat.id == MANAGERS_CHAT_ID)
async def receive_delete_reason(message: types.Message):

    user_data = DELETE_REASONS.get(message.from_user.id)
    if not user_data:
        return
    order_id = user_data["order_id"]
    
    order_data = await get_order_from_db(order_id)
    await bot.send_message(order_data["user_id"], f"Ваш заказ с ID #{str(order_id).zfill(6)} был удален по причине: {message.text}")
    await bot.delete_message(MANAGERS_CHAT_ID, order_data["manager_message_order"])
    await bot.delete_message(RESHALI_CHAT_ID, order_data["assistance_message_order"])
    for file_id in order_data["manager_chat_file_id"]:
        await bot.delete_message(MANAGERS_CHAT_ID, file_id)
    for file_id in order_data["assistance_chat_file_id"]:
        await bot.delete_message(RESHALI_CHAT_ID, file_id)
    await bot.delete_message(MANAGERS_CHAT_ID, user_data["sent_message_id"])
    await bot.delete_message(MANAGERS_CHAT_ID, message.message_id)

    # Удаляем меню с кнопкой "Откликнуться" в чате исполнителей
    last_assistance_file_id = order_data["assistance_chat_file_id"][-1]
    await bot.delete_message(RESHALI_CHAT_ID, last_assistance_file_id + 1)

    # Удаляем меню с кнопками в чате менеджеров
    last_manager_file_id = order_data["manager_chat_file_id"][-1]
    await bot.delete_message(MANAGERS_CHAT_ID, last_manager_file_id + 1)

    await delete_order_from_db(order_id)
    del DELETE_REASONS[message.from_user.id]


@dp.callback_query_handler(lambda c: c.data == 'order_complite', state="*")
async def process_order(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_data = await state.get_data()
    
    if user_id not in orders_data:
        await bot.send_message(user_id, "Ошибка при обработке заказа. Пожалуйста, попробуйте еще раз.")
        return

    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute(
            "INSERT INTO orders (user_id, subject, description, deadline, check_time, price) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, orders_data[user_id]["subject"], orders_data[user_id]["description"], orders_data[user_id]["deadline"], orders_data[user_id]["check_time"], orders_data[user_id]["price"])
        )
        await db.commit()

        order_id = str(cursor.lastrowid).zfill(6)

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

    manager_chat_file_ids = []
    assistance_chat_file_ids = []
    for file_id in orders_data[user_id]['files']:
        manager_file = await bot.send_document(MANAGERS_CHAT_ID, file_id)
        manager_chat_file_ids.append(manager_file.message_id)

        assistance_file = await bot.send_document(RESHALI_CHAT_ID, file_id)
        assistance_chat_file_ids.append(assistance_file.message_id)

    await bot.send_message(MANAGERS_CHAT_ID, "Управление заказом:", reply_markup=generate_manager_order_menu(order_id))
    await bot.send_message(RESHALI_CHAT_ID, "Нажмите кнопку ниже, чтобы откликнуться на заказ", reply_markup=generate_response_menu(order_id))

    await update_order_in_db(order_id, manager_message_order, assistance_message_order, manager_chat_file_ids, assistance_chat_file_ids)
    await state.finish()
    await bot.send_message(user_id, "Ваш заказ был успешно отправлен!\n\n Вы можете следить за статусом ваших заказов во вкладке Мои заказы")