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
                manager_message_order INTEGER,
                assistance_message_order INTEGER,
                manager_chat_file_id TEXT, 
                assistance_chat_file_id TEXT, 
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

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS assistants (
                assistant_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_username TEXT,
                user_id INTEGER UNIQUE,  -- ID исполнителя в Telegram
                full_name TEXT,
                phone_number TEXT,
                university TEXT,
                faculty TEXT,
                specialization TEXT,
                graduation_year TEXT,
                priority_subjects TEXT,
                cover_letter TEXT
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE responses (
                response_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                user_id INTEGER,  -- Заказчик
                assistant_id INTEGER,
                proposed_price INTEGER,
                customer_price INTEGER
            )
            """
);



        await db.commit()
