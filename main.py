from aiogram import executor
from bot import dp

# Импорт обработчиков
import handlers.start
import handlers.user
import handlers.reshatel_handler
import handlers.faq_handler
import handlers.order_handler
import handlers.balance_handler
import handlers.reshenie_zadach
import handlers.order_process
import handlers.file_handlers
import handlers.order_submission_handlers
import handlers.order_deadline
import handlers.order_description
import handlers.order_check_time
import handlers.order_price
import handlers.order_subject
import handlers.our_reviews
import handlers.my_orders
import handlers.add_new_assistant
import handlers.otklik_handler

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
