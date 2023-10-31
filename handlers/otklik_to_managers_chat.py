import aiosqlite
from db.models import DATABASE
from bot import bot


async def fetch_notification_data(response_id: int):
    
    print(f"Received response_id: {response_id}")  # Временный вывод для проверки

    async with aiosqlite.connect(DATABASE) as db:

        # Извлекаем данные об отклике
        cursor = await db.execute(
            """
            SELECT order_id, user_id, assistant_id, proposed_price, customer_price
            FROM responses
            WHERE response_id = ?
            """, (response_id,)
        )
        response_data = await cursor.fetchone()
        print (response_data)
        if not response_data:
            return None  # Если отклик не найден
        
        order_id = response_data[0]

        # Извлекаем данные о заказе
        cursor = await db.execute(
            """
            SELECT * 
            FROM orders
            WHERE order_id = ?
            """, (order_id,)
        )
        order_data = await cursor.fetchone()
        if not order_data:
            return None  # Если заказ не найден
        
        customer_chat = await bot.get_chat(response_data[1])
        assistant_chat = await bot.get_chat(response_data[2])
        
        usernames = {
            response_data[1]: customer_chat.username,
            response_data[2]: assistant_chat.username
        }
        print (order_data)
        return order_data, response_data, usernames



async def send_notification_to_managers(order_id: int, manager_chat_id: int):
    data = await fetch_notification_data(order_id)
    print(data)
    if not data:
        return  # Если не удалось извлечь данные

    order_data, response_data, usernames = data
    customer_username = usernames.get(response_data[1])
    assistant_username = usernames.get(response_data[2])

    potential_revenue = response_data[4] - response_data[3]  # Разность цены заказчика и исполнителя

    notification_text = (
        f"По заказу #Order{str(order_data[0]).zfill(6)} новый отклик!\n"
        f"Заказчик: @{customer_username}\n"
        f"Цена заказчика: {response_data[4]}\n"
        f"Исполнитель: @{assistant_username}\n"
        f"Цена исполнителя: {response_data[3]}\n"
        f"Потенциальная выручка: {potential_revenue}\n\n"
        f"Информация о заказе:\n"
        f"Предмет: {order_data[2]}\n"
        f"Описание: {order_data[3]}\n"
        f"Срок: {order_data[4]}\n"
        f"Время проверки: {order_data[5]}\n"
        f"Цена заказа: {order_data[6]}\n"
    )

    await bot.send_message(manager_chat_id, notification_text)

