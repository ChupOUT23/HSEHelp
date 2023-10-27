#Обработчик кнопки Задать вопрос/FAQ
#Обработчик кнопки НАШИ ОТЗЫВЫ
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import dp, bot
from handlers.user import get_post_registration_keyboard
from db.database import get_user_balance

@dp.callback_query_handler(lambda c: c.data == 'our_reviews')
async def open_reviews_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Создаем клавиатуру для меню Отзывов
    reviews_keyboard = InlineKeyboardMarkup()
    reviews_keyboard.add(InlineKeyboardButton("Перейти в группу с отзывами", url='https://t.me/hsereviews'))
    reviews_keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_main_reviews"))
    
    # Message to be displayed
    reviews_message = ("Дорогой студент!😊\n"
                   "Если вы сомневаетесь в качестве нашего сервиса, приглашаем вас перейти в нашу группу с отзывами от реальных клиентов. 🌟\n\n"
                   "Мы предоставляем профессиональную помощь студентам с экзаменами, домашними заданиями и многим другим. 📚📝\n\n"
                   "Убедитесь в нашей компетентности и надежности, прочитав отзывы тех, кто уже воспользовался нашими услугами! 👍")
    
    # Изменяем сообщение, чтобы показать новое содержание и клавиатуру
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, 
                                text=reviews_message,
                                reply_markup=reviews_keyboard)

@dp.callback_query_handler(lambda c: c.data == 'back_to_main_reviews')
async def back_to_main_menu_from_reviews(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Получаем текущий баланс пользователя, чтобы воссоздать основное меню
    current_balance = await get_user_balance(user_id)
    main_menu = get_post_registration_keyboard(current_balance)
    
    # Изменяем сообщение, чтобы снова показать основное меню
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, 
                                text="🚀 Добро пожаловать в лучший помощник для студентов!\n🤝 Здесь вы можете быстро и надежно получить помощь с учебными задачами. Наши эксперты готовы помочь вам прямо сейчас. Выберите действие и погрузитесь в мир знаний с нами!", reply_markup=main_menu)
