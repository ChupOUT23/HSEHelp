# Заполнение кнопки Дедлайн

import datetime
import re
import asyncio
import os
from aiogram.utils import exceptions
from aiogram import types
from bot import dp, bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from handlers.reshenie_zadach import orders_data, generate_order_menu
from handlers.order_process import OrderForm

@dp.callback_query_handler(lambda c: c.data == 'order_deadline')
async def ask_deadline(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id

    # Проверяем, были ли данные о заказе и инициализируем их, если нет
    if user_id not in orders_data:
        orders_data[user_id] = {
            "subject": None,
            "description": None,
            "files": [],  # Убедимся, что это список
            "deadline": None,
            "check_time": None,
            "price": None
        }

    # Сохраняем ID меню
    await state.update_data(menu_message_id=callback_query.message.message_id)
    await bot.answer_callback_query(callback_query.id)
    sent_message = await bot.send_message(user_id, 'Введите дедлайн (например, 23.02 23:59):')
    
    # Сохраняем только ID отправленного сообщения (не включая сообщение меню)
    messages_to_delete = [sent_message.message_id]
    await state.update_data(messages_to_delete=messages_to_delete)
    await OrderForm.Deadline.set()

@dp.message_handler(state=OrderForm.Deadline)
async def set_deadline(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    user_data = await state.get_data()
    messages_to_delete = user_data.get('messages_to_delete', [])
    menu_message_id = user_data.get('menu_message_id')
    ask_message_id = user_data.get('ask_message_id')  # извлекаем ID сообщения

    # Добавляем ID сообщения с дедлайном в список сообщений для удаления
    messages_to_delete.append(message.message_id)

    new_deadline = message.text

    # Если новый дедлайн такой же, как и старый, просто вернемся без внесения изменений
    if new_deadline == orders_data[user_id].get('deadline'):
        return
    # Проверяем формат введенного дедлайна с помощью регулярного выражения
    if not re.match(r'\d{2}\.\d{2} \d{2}:\d{2}', new_deadline):
        error_msg = await bot.send_message(user_id, 'Неверный формат дедлайна. Введите дедлайн в формате ДД.ММ ЧЧ:ММ.')
        messages_to_delete.append(error_msg.message_id)
        await state.update_data(messages_to_delete=messages_to_delete)
        return

    # Сохраняем дедлайн
    orders_data[user_id]['deadline'] = new_deadline
    
    # Обновляем меню
    keyboard = generate_order_menu(user_id)
    await bot.edit_message_text(
        chat_id=user_id,
        message_id=menu_message_id,
        text="Ваш дедлайн обновлен! Выберите следующий пункт:",
        reply_markup=keyboard
    )

    # Удаляем все сообщения из списка, кроме обновленного сообщения с меню
    for msg_id in messages_to_delete:
        if msg_id != menu_message_id:
            try:
                await bot.delete_message(chat_id=user_id, message_id=msg_id)
            except Exception as e:
                print(f"Ошибка удаления сообщения {msg_id}: {e}")
    
    await state.finish()