#Формирование пунктов меню

import datetime
import re
import asyncio
import os
from aiogram.utils import exceptions
from aiogram import types
from bot import dp, bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from handlers.reshenie_zadach import orders_data, generate_order_menu

# Создаем состояния для каждого из пунктов
class OrderForm(StatesGroup):
    Subject = State()
    Description = State()
    Files = State()
    Deadline = State()
    CheckTime = State()
    Price = State()