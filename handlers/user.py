#Формирование основного меню приложения

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import dp, bot
from db.database import add_user, get_user_balance

def get_post_registration_keyboard(current_balance: float) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Новый заказ", callback_data="new_order"))
    keyboard.add(InlineKeyboardButton("Мои заказы", callback_data="my_orders"))
    keyboard.add(InlineKeyboardButton(f"Баланс: {current_balance}", callback_data="balance"))
    keyboard.add(InlineKeyboardButton("Реферальная программа", callback_data="referal"))
    keyboard.add(InlineKeyboardButton("Задать вопрос/FAQ", callback_data="question"))
    keyboard.add(InlineKeyboardButton("Хочу стать решателем!", callback_data="reshatel_new"))
    keyboard.add(InlineKeyboardButton("Наши отзывы", callback_data="our_reviews"))

    return keyboard

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def handle_contact(message: types.Message):
    user_id = message.from_user.id
    contact = message.contact.phone_number
    
    await add_user(user_id, contact)
    
    # Get the current balance of the user
    current_balance = await get_user_balance(user_id)
    
    # Generate the keyboard with the current balance
    post_registration_keyboard = get_post_registration_keyboard(current_balance)

    await bot.send_message(user_id, f"Спасибо! Ваш номер телефона {contact} был успешно зарегистрирован.", reply_markup=types.ReplyKeyboardRemove())    
    await bot.send_message(user_id, "🚀 Добро пожаловать в лучший помощник для студентов!\n\nЗдесь вы можете быстро и надежно получить помощь с учебными задачами. Выберите действие и погрузитесь в мир знаний с нами!", reply_markup=post_registration_keyboard)
