#Заполнение кнопки Бюджет

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

@dp.callback_query_handler(lambda c: c.data == 'order_price')
async def ask_price(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(menu_message_id=callback_query.message.message_id)  # Сохраняем ID меню
    await bot.answer_callback_query(callback_query.id)
    sent_message = await bot.send_message(callback_query.from_user.id, 'Введите ориентировочный бюджет для подбора решал:')
    await state.update_data(ask_message_id=sent_message.message_id)  # Сохраняем ID сообщения "Введите предмет"
    await OrderForm.Price.set()


@dp.message_handler(state=OrderForm.Price)
async def set_price(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Инициализируем данные для пользователя, если они еще не были инициализированы
    if user_id not in orders_data:
        orders_data[user_id] = {
        "subject": None,
        "description": None,
        "files": [],  # Убедимся, что это список
        "deadline": None,
        "check_time": None,
        "price": None
    }

    user_data = await state.get_data()
    ask_message_id = user_data.get('ask_message_id')

    new_price = message.text
    current_price = orders_data[user_id]['price']

    if new_price == current_price:
        await bot.delete_message(chat_id=user_id, message_id=ask_message_id)
        await bot.delete_message(chat_id=user_id, message_id=message.message_id)
        await state.finish()
        return

    user_data = await state.get_data()
    menu_message_id = user_data.get('menu_message_id')
    ask_message_id = user_data.get('ask_message_id')

    await state.update_data(price=message.text)
    print(user_id," выбрал бюджет: ",message.text) #Отладка

    # Обновляем данные и редактируем старое сообщение
    orders_data[user_id]['price'] = message.text
    keyboard = generate_order_menu(user_id)
    
    await bot.edit_message_text(chat_id=user_id, message_id=menu_message_id, text="Теперь мы знаем, на какой бюджет вы рассчитываете.", reply_markup=keyboard)

    # Удаление сообщений
    await bot.delete_message(chat_id=user_id, message_id=ask_message_id)
    await bot.delete_message(chat_id=user_id, message_id=message.message_id)
    
    await state.finish()

