#Обработчик пополнение Баланса

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import dp, bot
from handlers.user import get_post_registration_keyboard
from db.database import get_user_balance

@dp.callback_query_handler(lambda c: c.data == 'balance')
async def open_balance_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Получаем текущий баланс пользователя
    current_balance = await get_user_balance(user_id)
    
    # Создаем клавиатуру для меню баланса
    balance_keyboard = InlineKeyboardMarkup()
    balance_keyboard.add(InlineKeyboardButton("Пополнить баланс", url='https://your-payment-link.com'))
    balance_keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_main_balance"))
    
    # Сообщение с информацией о балансе
    balance_message = f"💰 Ваш баланс составляет {current_balance} рублей.\n\n🔽 Чтобы пополнить, нажмите кнопку ниже."
    
    # Изменяем сообщение, чтобы показать информацию о балансе и клавиатуру
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, 
                                text=balance_message,
                                reply_markup=balance_keyboard)

@dp.callback_query_handler(lambda c: c.data == 'back_to_main_balance')
async def back_to_main_menu_from_balance(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Получаем текущий баланс пользователя, чтобы воссоздать основное меню
    current_balance = await get_user_balance(user_id)
    main_menu = get_post_registration_keyboard(current_balance)
    
    # Изменяем сообщение, чтобы снова показать основное меню
    welcome_message = ("🚀 Добро пожаловать в лучший помощник для студентов! "
                       "Здесь вы можете быстро и надежно получить помощь с учебными задачами. Выберите действие и погрузитесь в мир знаний с нами!")
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, 
                                text=welcome_message, reply_markup=main_menu)
