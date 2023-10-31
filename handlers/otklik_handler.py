from aiogram import types
import aiosqlite
from bot import dp, bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.contrib.middlewares.fsm import FSMMiddleware
from config import MANAGERS_CHAT_ID
from db.models import DATABASE
from aiogram.dispatcher.filters.state import State, StatesGroup

from handlers.otklik_to_managers_chat import send_notification_to_managers


def generate_price_offer_menu(order_id):
    markup = InlineKeyboardMarkup()
    item1 = InlineKeyboardButton("Предложить цену", callback_data=f"offer_price_{order_id}")
    item2 = InlineKeyboardButton("Отменить", callback_data="cancel_offer")
    markup.add(item1, item2)
    return markup

@dp.callback_query_handler(lambda c: c.data.startswith('respond_'))
async def respond_to_order(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[-1])
    await bot.send_message(
        callback_query.from_user.id, 
        f"Вы откликнулись на заказ #Order{str(order_id).zfill(6)}. Выберите действие:",
        reply_markup=generate_price_offer_menu(order_id)
    )

@dp.callback_query_handler(lambda c: c.data == 'cancel_offer')
async def cancel_offer(callback_query: types.CallbackQuery):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

class OfferPrice(StatesGroup):
    price = State()  # состояние, когда пользователь вводит цену

@dp.callback_query_handler(lambda c: c.data.startswith('offer_price_'))
async def ask_for_price(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = int(callback_query.data.split('_')[-1])
    await state.set_data({"order_id": order_id})  # Сохраняем order_id в FSMContext
    await bot.send_message(
        callback_query.from_user.id,
        "Пожалуйста, введите предлагаемую цену:"
    )
    await OfferPrice.price.set()

@dp.message_handler(state=OfferPrice.price)
async def save_offer_price(message: types.Message, state: FSMContext):
    user_data = await state.get_data()  # Получаем данные из FSMContext
    order_id = user_data.get("order_id")
    assistant_id = message.from_user.id  # ID пользователя, который предложил цену
    proposed_price = int(message.text)  # Предполагая, что цена - это целое число

    async with aiosqlite.connect(DATABASE) as db:
        # Извлекаем данные о заказе из таблицы orders
        cursor = await db.execute(
            """
            SELECT user_id, price
            FROM orders
            WHERE order_id = ?
            """, (order_id,)
        )
        order_data = await cursor.fetchone()

        if not order_data:
            await bot.send_message(message.from_user.id, f"Ошибка: заказ с ID {order_id} не найден!")
            await state.finish()
            return

        user_id, customer_price = order_data

        # Сохраняем предложенную цену в таблице responses
        await db.execute(
            """
            INSERT INTO responses (order_id, user_id, assistant_id, proposed_price, customer_price)
            VALUES (?, ?, ?, ?, ?)
            
            """, (order_id, user_id, assistant_id, proposed_price, customer_price)
        )
        cursor = await db.execute("SELECT MAX(response_id) FROM responses")
        response_row = await cursor.fetchone()
        response_id = response_row[0]

        print (response_id)
        await db.commit()

    await bot.send_message(message.from_user.id, f"Ваше предложение цены {proposed_price} для заказа #{order_id} успешно отправлено!")
    await send_notification_to_managers(response_id, MANAGERS_CHAT_ID)
    await state.finish()  # Завершаем FSM
