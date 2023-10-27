#Функции-обработчики базы данных

import aiosqlite
from db.models import DATABASE

# Добавляем функцию для проверки наличия пользователя
async def user_exists(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone() is not None

async def add_user(user_id: int, phone_number: str, balance: float = 0.0):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "INSERT INTO users (user_id, phone_number, balance) VALUES (?, ?, ?)",
            (user_id, phone_number, balance)
        )
        await db.commit()

async def get_user_balance(user_id: int) -> float:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                return result[0]
            else:
                return 0.0  # Возвращаем 0.0, если пользователя не существует или у него нет баланса