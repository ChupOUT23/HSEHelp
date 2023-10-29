from aiogram import types
import aiosqlite
from bot import dp
from config import ADMINS
from db.models import DATABASE
from handlers.state_assistant import NewAssistant
from aiogram.dispatcher import FSMContext


async def add_assistant(data: dict):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute(
            """
            INSERT INTO assistants (tg_username, user_id, full_name, phone_number, university, faculty, specialization, graduation_year, priority_subjects, cover_letter) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (data["tg_username"], data["user_id"], data["full_name"], data["phone_number"], data["university"], data["faculty"], data["specialization"], data["graduation_year"], data["priority_subjects"], data["cover_letter"])
        )
        await db.commit()

@dp.message_handler(commands=['addassistance'])
async def add_assistance_start(message: types.Message):
    user_id = message.from_user.id

    if user_id not in ADMINS:
        await message.reply("У вас нет прав использовать эту команду.")
        return

    await message.reply("Введите ник исполнителя в Telegram (без @).")
    await NewAssistant.tg_username.set()  # Переходим к следующему состоянию в машине состояний

@dp.message_handler(state=NewAssistant.tg_username)
async def process_tg_username(message: types.Message, state: FSMContext):
    user_id = message.from_user.id  # Получаем user_id
    await state.update_data(tg_username=message.text, user_id=user_id)  # Сохраняем user_id
    await message.reply("Введите ФИО исполнителя.")
    await NewAssistant.full_name.set()


@dp.message_handler(state=NewAssistant.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.reply("Введите номер телефона исполнителя.")
    await NewAssistant.phone_number.set()

@dp.message_handler(state=NewAssistant.phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    await state.update_data(phone_number=message.text)
    await message.reply("Введите ВУЗ исполнителя.")
    await NewAssistant.university.set()

@dp.message_handler(state=NewAssistant.university)
async def process_university(message: types.Message, state: FSMContext):
    await state.update_data(university=message.text)
    await message.reply("Введите факультет на котором учится/учился исполнитель.")
    await NewAssistant.faculty.set()

@dp.message_handler(state=NewAssistant.faculty)
async def process_faculty(message: types.Message, state: FSMContext):
    await state.update_data(faculty=message.text)
    await message.reply("Введите специализацию исполнителя.")
    await NewAssistant.specialization.set()

@dp.message_handler(state=NewAssistant.specialization)
async def process_specialization(message: types.Message, state: FSMContext):
    await state.update_data(specialization=message.text)
    await message.reply("Введите год окончания обучения исполнителя.")
    await NewAssistant.graduation_year.set()

@dp.message_handler(state=NewAssistant.graduation_year)
async def process_graduation_year(message: types.Message, state: FSMContext):
    await state.update_data(graduation_year=message.text)
    await message.reply("Введите приоритетные предметы исполнителя.")
    await NewAssistant.priority_subjects.set()

@dp.message_handler(state=NewAssistant.priority_subjects)
async def process_priority_subjects(message: types.Message, state: FSMContext):
    await state.update_data(priority_subjects=message.text)
    await message.reply("Введите сопроводительное письмо.")
    await NewAssistant.cover_letter.set()

@dp.message_handler(state=NewAssistant.cover_letter)
async def process_cover_letter(message: types.Message, state: FSMContext):
    await state.update_data(cover_letter=message.text)  # Добавляем cover_letter в state
    user_data = await state.get_data()
    await add_assistant(user_data)
    await state.finish()
    await message.reply("Исполнитель успешно добавлен!")


