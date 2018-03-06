import telegram.ext
from mock import Mock
from telegram import Bot

from config import TELEGRAM_TOKEN

if TELEGRAM_TOKEN:
    bot = Bot(TELEGRAM_TOKEN)
else:
    bot = Mock()

dispatcher = telegram.ext.Dispatcher(bot, None)

