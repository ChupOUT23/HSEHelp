#Заполнение кнопки Файлы

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

processed_media_groups = set()

@dp.callback_query_handler(lambda c: c.data == 'order_files')
async def ask_files(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id

    files_exist = orders_data.get(user_id, {}).get('files', [])

    if not files_exist:
        await send_file_request(callback_query, state)
    else:
        await offer_file_options(callback_query, state)

async def send_file_request(callback_query, state):
    user_id = callback_query.from_user.id

    if user_id not in orders_data:
        orders_data[user_id] = {
            "subject": None,
            "description": None,
            "files": [],
            "deadline": None,
            "check_time": None,
            "price": None
        }

    await state.update_data(menu_message_id=callback_query.message.message_id)
    await bot.answer_callback_query(callback_query.id)
    
    finish_keyboard = InlineKeyboardMarkup()
    finish_keyboard.add(InlineKeyboardButton("Завершить", callback_data="finish_files"))
    sent_message = await bot.send_message(user_id, 'Пожалуйста, отправьте необходимые файлы или нажмите кнопку "Завершить", чтобы завершить ввод файлов:', reply_markup=finish_keyboard)
    
    messages_to_delete = [sent_message.message_id]
    await state.update_data(messages_to_delete=messages_to_delete)
    
    await OrderForm.Files.set()

@dp.callback_query_handler(lambda c: c.data == 'clear_files')
async def clear_files(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    orders_data[user_id]['files'] = []

    keyboard = generate_order_menu(user_id)  # Обновляем меню с учетом того, что файлы были удалены
    await bot.edit_message_text(
        chat_id=user_id,
        message_id=callback_query.message.message_id,
        text="Ваши файлы были удалены. Выберите следующий пункт:",
        reply_markup=keyboard
    )

    await bot.answer_callback_query(callback_query.id, "Ваши файлы были удалены. Вы можете прикрепить новые файлы.")

@dp.callback_query_handler(lambda c: c.data == 'add_more_files')
async def add_more_files(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id)
    finish_keyboard = InlineKeyboardMarkup()
    finish_keyboard.add(InlineKeyboardButton("Завершить", callback_data="finish_files"))
    await bot.send_message(user_id, 'Пожалуйста, отправьте дополнительные файлы.', reply_markup=finish_keyboard)
    await OrderForm.Files.set()

@dp.callback_query_handler(lambda c: c.data == 'view_files')
async def view_and_leave_files(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    files = orders_data.get(user_id, {}).get('files', [])

    if not files:
        await bot.answer_callback_query(callback_query.id, "У вас нет прикрепленных файлов.")
        return

    file_keyboard = InlineKeyboardMarkup(row_width=1)
    
    for index, file_id in enumerate(files):
        file_button_text = f"Файл {index + 1}"
        file_keyboard.add(InlineKeyboardButton(file_button_text, callback_data=f"view_file_{index}"))
    
    file_keyboard.add(
        InlineKeyboardButton("Добавить ещё файлы", callback_data="add_more_files"),
        InlineKeyboardButton("Очистить все файлы", callback_data="clear_files"),
        InlineKeyboardButton("Назад", callback_data="back_from_files")  # Добавляем кнопку "Назад"
    )

    await bot.send_message(user_id, "Ваши прикрепленные файлы:", reply_markup=file_keyboard)

@dp.callback_query_handler(lambda c: c.data == 'back_from_files')
async def back_from_files_view(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    keyboard = generate_order_menu(user_id)
    await bot.edit_message_text(
        chat_id=user_id,
        message_id=callback_query.message.message_id,
        text="Выберите следующий пункт:",
        reply_markup=keyboard
    )
    await bot.answer_callback_query(callback_query.id, "Файлы оставлены без изменений.")


@dp.callback_query_handler(lambda c: c.data.startswith('view_file_'))
async def view_specific_file(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    file_index = int(callback_query.data.split('_')[-1])
    file_id = orders_data.get(user_id, {}).get('files', [])[file_index]

    file_options_keyboard = InlineKeyboardMarkup(row_width=1)
    file_options_keyboard.add(
        InlineKeyboardButton("Удалить этот файл", callback_data=f"delete_file_{file_index}"),
        InlineKeyboardButton("Оставить без изменений", callback_data="leave_file")
    )

    await bot.send_message(user_id, f"Что вы хотите сделать с файлом {file_index + 1}?", reply_markup=file_options_keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('delete_file_'))
async def delete_specific_file(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    file_index = int(callback_query.data.split('_')[-1])

    if user_id in orders_data and 'files' in orders_data[user_id]:
        del orders_data[user_id]['files'][file_index]

    await bot.answer_callback_query(callback_query.id, "Файл был удален.")
    await view_and_leave_files(callback_query)  # Повторно показываем список файлов

async def offer_file_options(callback_query, state):
    user_id = callback_query.from_user.id

    options_keyboard = InlineKeyboardMarkup(row_width=1)
    options_keyboard.add(
        InlineKeyboardButton("Добавить ещё файлы", callback_data="add_more_files"),
        InlineKeyboardButton("Очистить файлы", callback_data="clear_files"),
        InlineKeyboardButton("Редактировать прикрепленные файлы", callback_data="view_files")
    )

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, "Вы уже прикрепили некоторые файлы. Что бы вы хотели сделать?", reply_markup=options_keyboard)

@dp.message_handler(content_types=['document'], state=OrderForm.Files)
async def handle_docs(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # Проверим, инициализирован ли orders_data[user_id]
    if user_id not in orders_data:
        orders_data[user_id] = {
            "subject": None,
            "description": None,
            "files": [],
            "deadline": None,
            "check_time": None,
            "price": None
        }

    # Теперь убедимся, что 'files' инициализирован как список
    if not isinstance(orders_data[user_id].get('files'), list):
        orders_data[user_id]['files'] = []

    orders_data[user_id]['files'].append(message.document.file_id)

    # Если это часть медиа-группы и эта группа еще не была обработана, отправьте подтверждение
    media_group_id = message.media_group_id
    if media_group_id and media_group_id not in processed_media_groups:
        processed_media_groups.add(media_group_id)
        # Добавляем кнопку "Завершить" каждый раз, когда пользователь отправляет файл
        finish_keyboard = InlineKeyboardMarkup()
        finish_keyboard.add(InlineKeyboardButton("Завершить", callback_data="finish_files"))
        await bot.send_message(user_id, f"Файлы сохранены. Можете отправить еще файлы или нажмите кнопку 'Завершить'.", reply_markup=finish_keyboard)
    elif not media_group_id:
        # Если это отдельный файл (не часть группы), просто отправьте подтверждение
        finish_keyboard = InlineKeyboardMarkup()
        finish_keyboard.add(InlineKeyboardButton("Завершить", callback_data="finish_files"))
        await bot.send_message(user_id, f"Файл {message.document.file_name} сохранен. Можете отправить еще файлы или нажмите кнопку 'Завершить'.")

@dp.callback_query_handler(lambda c: c.data == 'finish_files', state=OrderForm.Files)
async def finish_files(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id

    user_data = await state.get_data()
    messages_to_delete = user_data.get('messages_to_delete', [])
    menu_message_id = user_data.get('menu_message_id')

    new_text = "Ваши файлы сохранены! Выберите следующий пункт:"
    keyboard = generate_order_menu(user_id)
    
    try:
        # Пытаемся получить текущий текст сообщения
        current_message = await bot.get_message(chat_id=user_id, message_id=menu_message_id)
        current_text = current_message.text
        
        # Проверяем, изменился ли текст
        if current_text != new_text:
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=menu_message_id,
                text=new_text,
                reply_markup=keyboard
            )
    except exceptions.MessageToEditNotFound:
        await bot.send_message(user_id, new_text, reply_markup=keyboard)
    except Exception as e:
        print(f"Ошибка: {e}")
        await bot.send_message(user_id, new_text, reply_markup=keyboard)

    for msg_id in messages_to_delete:
        if msg_id != menu_message_id:
            try:
                await bot.delete_message(chat_id=user_id, message_id=msg_id)
            except Exception as e:
                print(f"Ошибка удаления сообщения {msg_id}: {e}")

    await state.finish()
