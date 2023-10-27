import aiosqlite

DATABASE = "HSE.db"

async def create_db():
    async with aiosqlite.connect(DATABASE) as db:
        # Создаем таблицу пользователей
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE,
                phone_number TEXT,
                balance REAL DEFAULT 0.0
            )
            """
        )
        
        # Создаем таблицу для заказов с автоинкрементным order_id
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                description TEXT,
                deadline TEXT,
                check_time INTEGER,
                price REAL DEFAULT 0.0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """
        )

        # Создаем таблицу для файлов
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                order_id INTEGER,
                user_id INTEGER,
                file_id TEXT,
                file_path TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
            """
        )

        await db.commit()