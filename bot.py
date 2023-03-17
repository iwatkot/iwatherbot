from enum import Enum
from re import escape

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from decouple import config


from logger import Logger
from database import Session
from api import Caller

logger = Logger(__name__)

storage = MemoryStorage()
bot = Bot(token=config("TOKEN"))

dp = Dispatcher(bot=bot, storage=storage)


class Messages(Enum):
    START = "Hello, I'm a bot. I can help you to check the weather."
    MENU_CHANGED = "You switched to the `{menu}`."

    def escaped(self):
        return escape(self.value)

    def format(self, **kwargs):
        return escape(self.value.format(**kwargs))


class Buttons(Enum):
    MAIN_MENU = "Main menu"
    FORECASTS = "Forecasts"
    MY_LOCATION = "My location"

    CURRENT_WEATHER = "Current weather"

    SAVED_LOCATION = "Saved location"
    CHANGE_LOCATION = "Change location"

    MAIN = [CURRENT_WEATHER, FORECASTS, MY_LOCATION]
    OPTIONS = [CURRENT_WEATHER, MAIN_MENU]
    LOCATION = [SAVED_LOCATION, CHANGE_LOCATION, MAIN_MENU]

    def menu(self):
        return list(self.value)


# Functions for commands.


@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    telegram_id, user_name = get_user_data(message)
    await bot.send_message(
        telegram_id,
        Messages.START.escaped(),
        reply_markup=generate_reply_keyboard(Buttons.MAIN.menu()),
        parse_mode="MarkdownV2",
    )


# Functions for buttons.


@dp.message_handler(Text(equals=Buttons.MAIN_MENU.value))
async def main_menu(message: types.Message):
    telegram_id, user_name = get_user_data(message)
    await bot.send_message(
        telegram_id,
        Messages.MENU_CHANGED.format(menu=Buttons.MAIN_MENU.value),
        reply_markup=generate_reply_keyboard(Buttons.MAIN.menu()),
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.FORECASTS.value))
async def forecasts(message: types.Message):
    telegram_id, user_name = get_user_data(message)
    await bot.send_message(
        telegram_id,
        Messages.MENU_CHANGED.format(menu=Buttons.FORECASTS.value),
        reply_markup=generate_reply_keyboard(Buttons.OPTIONS.menu()),
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.MY_LOCATION.value))
async def location(message: types.Message):
    telegram_id, user_name = get_user_data(message)
    await bot.send_message(
        telegram_id,
        Messages.MENU_CHANGED.format(menu=Buttons.MY_LOCATION.value),
        reply_markup=generate_reply_keyboard(Buttons.LOCATION.menu()),
        parse_mode="MarkdownV2",
    )


# Keyboard generators.


def generate_reply_keyboard(reply_buttons: list):
    reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for button in reply_buttons:
        reply_keyboard.add(KeyboardButton(button))
    return reply_keyboard


def get_user_data(data: dict):
    """Extracting data from message or callback and logging it."""
    telegram_id = data.from_user.id
    user_name = data.from_user.username

    try:
        logger.debug(
            f"Message from {user_name} with telegram ID {telegram_id}: {data.text}."
        )
    except AttributeError:
        logger.debug(
            f"Callback from {user_name} with telegram ID {telegram_id}: {data.data}."
        )

    return telegram_id, user_name


if __name__ == "__main__":
    executor.start_polling(dp)
