import aiosqlite
from db.models import DATABASE
from bot import bot
from aiogram.dispatcher import Dispatcher
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

dp = Dispatcher(bot)  # Предполагается, что у вас уже есть экземпляр Dispatcher


async def fetch_notification_data(response_id: int):
    
    async with aiosqlite.connect(DATABASE) as db:

        # Извлекаем данные об отклике
        cursor = await db.execute(
            """
            SELECT order_id, user_id, assistant_id, proposed_price, customer_price
            FROM responses
            WHERE response_id = ?
            """, (response_id,)
        )
        response_data = await cursor.fetchone()

        if not response_data:
            return None  # Если отклик не найден
        
        order_id = response_data[0]

        # Извлекаем данные о заказе
        cursor = await db.execute(
            """
            SELECT * 
            FROM orders
            WHERE order_id = ?
            """, (order_id,)
        )
        order_data = await cursor.fetchone()
        if not order_data:
            return None  # Если заказ не найден
        
        customer_chat = await bot.get_chat(response_data[1])
        assistant_chat = await bot.get_chat(response_data[2])
        
        usernames = {
            response_data[1]: customer_chat.username,
            response_data[2]: assistant_chat.username
        }
        return order_data, response_data, usernames



async def send_notification_to_managers(order_id: int, manager_chat_id: int):
    data = await fetch_notification_data(order_id)

    if not data:
        return  # Если не удалось извлечь данные

    order_data, response_data, usernames = data
    customer_username = usernames.get(response_data[1])
    assistant_username = usernames.get(response_data[2])

    potential_revenue = response_data[4] - response_data[3]  # Разность цены заказчика и исполнителя

    notification_text = (
        f"По заказу #Order{str(order_data[0]).zfill(6)} новый отклик!\n"
        f"Заказчик: @{customer_username}\n"
        f"Цена заказчика: {response_data[4]}\n"
        f"Исполнитель: @{assistant_username}\n"
        f"Цена исполнителя: {response_data[3]}\n"
        f"Потенциальная выручка: {potential_revenue}\n\n"
        f"Информация о заказе:\n"
        f"Предмет: {order_data[2]}\n"
        f"Описание: {order_data[3]}\n"
        f"Срок: {order_data[4]}\n"
        f"Время проверки: {order_data[5]}\n"
        f"Цена заказа: {order_data[6]}\n"
    )

    # Создаем инлайн-кнопки
    keyboard = InlineKeyboardMarkup(row_width=2)
    delete_btn = InlineKeyboardButton("Удалить", callback_data=f"delete_response:{response_data[0]}")
    send_btn = InlineKeyboardButton("Отправить", callback_data=f"send_response:{response_data[0]}")
    keyboard.add(delete_btn, send_btn)

    await bot.send_message(manager_chat_id, notification_text)
    await bot.send_message(manager_chat_id, "Управление откликом:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('send_response:'))
async def process_send_response_callback(query: CallbackQuery):
    # Извлекаем response_id из callback data
    _, response_id = query.data.split(':')
    
    # Создаем новые инлайн-кнопки для подтверждения действия
    keyboard = InlineKeyboardMarkup(row_width=2)
    confirm_btn = InlineKeyboardButton("Да", callback_data=f"confirm_send:{response_id}")
    cancel_btn = InlineKeyboardButton("Нет", callback_data=f"cancel_send:{response_id}")
    keyboard.add(confirm_btn, cancel_btn)
    
    # Меняем текущие кнопки на новые
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=keyboard)
    await query.answer("Вы действительно хотите отправить отклик заказчику?")