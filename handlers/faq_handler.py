#Обработчик кнопки Задать вопрос/FAQ

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import dp, bot
from handlers.user import get_post_registration_keyboard
from db.database import get_user_balance

@dp.callback_query_handler(lambda c: c.data == 'question')
async def open_faq_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Создаем клавиатуру для меню FAQ
    faq_keyboard = InlineKeyboardMarkup()
    faq_keyboard.add(InlineKeyboardButton("FAQ", url='https://telegra.ph/FAQ-CHastye-voprosy-10-19'))
    faq_keyboard.add(InlineKeyboardButton("Обратиться к менеджеру", url='https://t.me/roman_glushkov'))
    faq_keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_main_faq"))
    
    # Message to be displayed
    faq_message = ("🔍 Прежде чем задать вопрос, пожалуйста, ознакомьтесь с нашим FAQ.\n"
                   "Там вы найдете ответы на многие популярные вопросы. 📘\n\n"
                   "📩 Если у вас все еще остались вопросы после прочтения FAQ, "
                   "не стесняйтесь обращаться к нашему менеджеру!")
    
    # Изменяем сообщение, чтобы показать новое содержание и клавиатуру
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, 
                                text=faq_message,
                                reply_markup=faq_keyboard)

@dp.callback_query_handler(lambda c: c.data == 'back_to_main_faq')
async def back_to_main_menu_from_faq(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Получаем текущий баланс пользователя, чтобы воссоздать основное меню
    current_balance = await get_user_balance(user_id)
    main_menu = get_post_registration_keyboard(current_balance)
    
    # Изменяем сообщение, чтобы снова показать основное меню
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, 
                                text="🚀 Добро пожаловать в лучший помощник для студентов!\n🤝 Здесь вы можете быстро и надежно получить помощь с учебными задачами. Наши эксперты готовы помочь вам прямо сейчас. Выберите действие и погрузитесь в мир знаний с нами!", reply_markup=main_menu)
