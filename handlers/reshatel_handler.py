from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import dp, bot
from db.database import get_user_balance
from handlers.user import get_post_registration_keyboard

@dp.callback_query_handler(lambda c: c.data == 'reshatel_new')
async def become_reshatel(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Создаем новую клавиатуру с кнопками "Назад" и "Написать менеджеру"
    resh_keyboard = InlineKeyboardMarkup()
    resh_keyboard.add(InlineKeyboardButton("Написать менеджеру", url='https://t.me/roman_glushkov'))
    resh_keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_main"))
    
    # Изменяем сообщение, чтобы показать новое содержание и клавиатуру
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, 
                                text="Хочешь стать решателем? 🎓\n\n"
                                     "🤝 Мы рады, что ты проявил интерес к нашей команде решателей! Прежде чем начать, "
                                     "нам нужно удостовериться в твоих квалификациях и личности.\n\n"
                                     "Шаги для становления решателем: 🛠\n\n"
                                     "📝 1. Подготовь рассказ о себе: Опиши свои навыки, опыт и область экспертизы. Это поможет нам "
                                     "лучше понять, какие задачи будут наиболее подходящими для тебя.\n"
                                     "🆔 2. Подготовь фотографию документа: Отправь нам фотографию своего студенческого "
                                     "билета или любого другого документа, удостоверяющего личность. Это необходимо для "
                                     "подтверждения твоей личности и образования.\n"
                                     "📩 3. Свяжись с менеджером: После подготовки всех данных, пожалуйста, напиши нашему "
                                     "менеджеру. Он рассмотрит твою заявку и даст обратную связь.\n\n"
                                     "🚀 Готов начать? Нажми на кнопку ниже, чтобы написать менеджеру!",
                                reply_markup=resh_keyboard)

@dp.callback_query_handler(lambda c: c.data == 'back_to_main')
async def back_to_main_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Получаем текущий баланс пользователя, чтобы воссоздать основное меню
    current_balance = await get_user_balance(user_id)
    main_menu = get_post_registration_keyboard(current_balance)
    
    # Изменяем сообщение, чтобы снова показать основное меню
    await bot.edit_message_text(chat_id=user_id, message_id=callback_query.message.message_id, 
                                text="🚀 Добро пожаловать в лучший помощник для студентов!\n🤝 Здесь вы можете быстро и надежно получить помощь с учебными задачами. Наши эксперты готовы помочь вам прямо сейчас. Выберите действие и погрузитесь в мир знаний с нами!", reply_markup=main_menu)
