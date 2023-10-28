from aiogram import types
from bot import dp
from config import ADMINS

@dp.message_handler(commands=['addassistance'])
async def add_assistance(message: types.Message):
    user_id = message.from_user.id

    # Проверяем, является ли пользователь администратором
    if user_id not in ADMINS:
        await message.reply("У вас нет прав использовать эту команду.")
        return

    # Если пользователь является администратором, продолжаем процесс добавления исполнителя
    # Здесь вы можете добавить логику по добавлению исполнителя: сохранение его данных в базу данных, отправка ему сообщения с приветствием и так далее.

    await message.reply("Введите данные нового исполнителя.")
