#Обработка меню с выбором помощт: Решение задач, Помощь на экзамене, Прямо сейчас

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import dp, bot
from handlers.user import get_post_registration_keyboard
from db.database import get_user_balance

@dp.callback_query_handler(lambda c: c.data == 'new_order')
async def open_order_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Создаем клавиатуру для меню создания нового заказа
    order_keyboard = InlineKeyboardMarkup()
    order_keyboard.add(InlineKeyboardButton("Решение задач", callback_data="task_solution"))
    order_keyboard.add(InlineKeyboardButton("Помощь на экзамене", callback_data="exam_help"))
    order_keyboard.add(InlineKeyboardButton("Прямо сейчас", callback_data="right_now"))
    order_keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_main_order"))
    
    # Описание типов заказов
    order_description = ("📄 Выбери тип работы! \n\n"
                         "• Решение задач — отправь нам задание, и мы поможем его решить. Файлы можно прикрепить позже.\n\n"
                         "• Помощь на экзамене — нужна помощь во время экзамена? Прикрепи примеры заданий или программу. Мы найдем решателей, готовых помочь.\n\n"
                         "• Прямо сейчас — если ты уже начал работу и нужна помощь сейчас. Прикрепи работу, и мы оперативно ответим!")
    
    # Изменяем сообщение, чтобы показать новое содержание и клавиатуру
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, 
                                text=order_description,
                                reply_markup=order_keyboard)

@dp.callback_query_handler(lambda c: c.data == 'back_to_main_order')


async def back_to_main_menu_from_order(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Получаем текущий баланс пользователя, чтобы воссоздать основное меню
    current_balance = await get_user_balance(user_id)
    main_menu = get_post_registration_keyboard(current_balance)
    
    # Изменяем сообщение, чтобы снова показать основное меню
    welcome_message = ("🚀 Добро пожаловать в лучший помощник для студентов! "
                       "Здесь вы можете быстро и надежно получить помощь с учебными задачами. Выберите действие и погрузитесь в мир знаний с нами!")
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, 
                                text=welcome_message, reply_markup=main_menu)
