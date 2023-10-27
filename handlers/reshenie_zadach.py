from aiogram import types
from bot import dp, bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.user import get_post_registration_keyboard
from db.database import get_user_balance

@dp.callback_query_handler(lambda c: c.data == 'task_solution')
async def order_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Инициализируем данные для пользователя, если они еще не были инициализированы
    if user_id not in orders_data:
        orders_data[user_id] = {
            "subject": None,
            "description": None,
            "files": None,
            "deadline": None,
            "check_time": None,
            "price": None
        }

    keyboard = generate_order_menu(user_id)
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, 
                                text="Предпросмотр заказа будет обновляться по мере его заполнения!\n\nОтправить заказ можно только после заполнения всех полей.", reply_markup=keyboard)

# Временное хранилище для данных о заказе
orders_data = {}

def generate_order_menu(user_id: int) -> InlineKeyboardMarkup:
    user_data = orders_data.get(user_id, {})
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Предмет
    subject_text = f"Предмет: {user_data['subject']}" if user_data.get("subject") else "Предмет"
    subject_status = "✅" if user_data.get("subject") else "❌"
    keyboard.add(InlineKeyboardButton(f"{subject_status} {subject_text}", callback_data="order_subject"))
    
    # Описание
    description_text = f"Описание: {user_data['description']}" if user_data.get("description") else "Описание"
    description_status = "✅" if user_data.get("description") else "❌"
    keyboard.add(InlineKeyboardButton(f"{description_status} {description_text}", callback_data="order_description"))

    # Файлы
    files_text = "Файлы: 📎" if user_data.get("files") else "Файлы"
    files_status = "✅" if user_data.get("files") else "❌"
    keyboard.add(InlineKeyboardButton(f"{files_status} {files_text}", callback_data="order_files"))
    
    # Дедлайн
    deadline_text = f"Дедлайн: {user_data['deadline']}" if user_data.get("deadline") else "Дедлайн"
    deadline_status = "✅" if user_data.get("deadline") else "❌"
    keyboard.add(InlineKeyboardButton(f"{deadline_status} {deadline_text}", callback_data="order_deadline"))

    # Время проверки
    check_time_text = f"Время проверки: {user_data['check_time']} дней" if user_data.get("check_time") else "Время проверки"
    check_time_status = "✅" if user_data.get("check_time") else "❌"
    keyboard.add(InlineKeyboardButton(f"{check_time_status} {check_time_text}", callback_data="order_check_time"))

    # Деньги
    price_text = f"Бюджет: {user_data['price']} руб." if user_data.get("price") else "Бюджет"
    price_status = "✅" if user_data.get("price") else "❌"
    keyboard.add(InlineKeyboardButton(f"{price_status} {price_text}", callback_data="order_price"))
    
    
    keyboard.add(InlineKeyboardButton("Отправить заказ", callback_data="order_complite"))
    keyboard.add(InlineKeyboardButton("🗑 Отменить заказ", callback_data="order_cancel"))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="order_back"))
    
    return keyboard



@dp.callback_query_handler(lambda c: c.data == 'order_back')
async def order_back_to_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    order_keyboard = generate_order_selection_menu()
    
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, 
                                text="📄 Выбери тип работы! \n\n"
                         "• Решение задач — отправь нам задание, и мы поможем его решить. Файлы можно прикрепить позже.\n\n"
                         "• Помощь на экзамене — нужна помощь во время экзамена? Прикрепи примеры заданий или программу. Мы найдем решателей, готовых помочь.\n\n"
                         "• Прямо сейчас — если ты уже начал работу и нужна помощь сейчас. Прикрепи работу, и мы оперативно ответим!", reply_markup=order_keyboard)

def generate_order_selection_menu() -> InlineKeyboardMarkup:
    order_keyboard = InlineKeyboardMarkup()
    order_keyboard.add(InlineKeyboardButton("Решение задач", callback_data="task_solution"))
    order_keyboard.add(InlineKeyboardButton("Помощь на экзамене", callback_data="exam_help"))
    order_keyboard.add(InlineKeyboardButton("Прямо сейчас", callback_data="right_now"))
    order_keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_main_order"))
    
    return order_keyboard


@dp.callback_query_handler(lambda c: c.data == 'order_cancel')
async def order_cancel(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    cancel_keyboard = InlineKeyboardMarkup(row_width=2)
    cancel_keyboard.add(InlineKeyboardButton("Да, отменить", callback_data="confirm_cancel"))
    cancel_keyboard.add(InlineKeyboardButton("Нет, продолжу оформление", callback_data="continue_order"))

    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id,
                                text="Вы точно хотите отменить заказ и вернуться в главное меню?", reply_markup=cancel_keyboard)

@dp.callback_query_handler(lambda c: c.data == 'confirm_cancel')
async def confirm_cancel(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Удаляем данные о заказе для этого пользователя
    if user_id in orders_data:
        del orders_data[user_id]
    
    current_balance = await get_user_balance(user_id)
    post_registration_keyboard = get_post_registration_keyboard(current_balance)
    
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id,
                                text="🚀 Добро пожаловать в лучший помощник для студентов!\n\nЗдесь вы можете быстро и надежно получить помощь с учебными задачами. Выберите действие и погрузитесь в мир знаний с нами!", reply_markup=post_registration_keyboard)


@dp.callback_query_handler(lambda c: c.data == 'continue_order')
async def continue_order(callback_query: types.CallbackQuery):
    await order_menu(callback_query)

