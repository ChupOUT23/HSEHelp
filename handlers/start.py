#Обработчик команды /start

from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot import dp
from db.database import user_exists, get_user_balance
from handlers.user import get_post_registration_keyboard

# Создаем клавиатуру для команды /start
start_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Поделиться контактом", request_contact=True)
)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    
    if not await user_exists(user_id):
        await message.answer(
            "Привет! Я бот-помощник для студентов. Чтобы продолжить, поделитесь своим контактом.",
            reply_markup=start_keyboard
        )
    else:
        await message.answer(
            "🚀 Добро пожаловать в лучший помощник для студентов!\n🤝 Здесь вы можете быстро и надежно получить помощь с учебными задачами. Наши эксперты готовы помочь вам прямо сейчас. Выберите действие и погрузитесь в мир знаний с нами!",
            reply_markup=get_post_registration_keyboard(await get_user_balance(user_id))
        )
