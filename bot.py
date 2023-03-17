from enum import Enum
from re import escape

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text, Regexp
from decouple import config


from logger import Logger
from database import Database, User
from api import Instance

logger = Logger(__name__)

storage = MemoryStorage()
bot = Bot(token=config("TOKEN"))

dp = Dispatcher(bot=bot, storage=storage)


class Messages(Enum):
    # Messages for commands.
    START = "Hello, this bot can help you to get weather forecasts."

    # Messages for menu changes.
    MENU_CHANGED = "You switched to the `{menu}`."

    # Messages for...
    SEARCH_LOCATION = "Please, send the name of the location to search."
    SEARCH_RESULTS = "Please, choose the location from the list below."
    NO_RESULTS = "No results found for your query."

    def escaped(self):
        return escape(self.value)

    def format(self, **kwargs):
        return escape(self.value.format(**kwargs))


class Buttons(Enum):
    MAIN_MENU = "Main menu"
    MAIN_FORECASTS = "Forecasts"
    MAIN_LOCATION = "Location"

    CURRENT_WEATHER = "Current weather"

    SAVED_LOCATION = "Saved location"
    CHANGE_LOCATION = "Change location"

    MENU = [CURRENT_WEATHER, MAIN_FORECASTS, MAIN_LOCATION]
    FORECASTS = [CURRENT_WEATHER, MAIN_MENU]
    LOCATION = [SAVED_LOCATION, CHANGE_LOCATION, MAIN_MENU]

    def menu(self):
        return list(self.value)


# Functions for commands.


@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    telegram_id, username = await get_user_data(message)
    await bot.send_message(
        telegram_id,
        Messages.START.escaped(),
        reply_markup=await reply_keyboard(Buttons.MAIN.menu()),
        parse_mode="MarkdownV2",
    )


# Functions for menu sections.


@dp.message_handler(Text(equals=Buttons.MAIN_MENU.value))
async def main_menu(message: types.Message):
    telegram_id, username = await get_user_data(message)
    await bot.send_message(
        telegram_id,
        Messages.MENU_CHANGED.format(menu=Buttons.MAIN_MENU.value),
        reply_markup=await reply_keyboard(Buttons.MENU.menu()),
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.MAIN_FORECASTS.value))
async def forecasts(message: types.Message):
    telegram_id, username = await get_user_data(message)
    await bot.send_message(
        telegram_id,
        Messages.MENU_CHANGED.format(menu=Buttons.MAIN_FORECASTS.value),
        reply_markup=await reply_keyboard(Buttons.FORECASTS.menu()),
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.MAIN_LOCATION.value))
async def location(message: types.Message):
    telegram_id, username = await get_user_data(message)
    await bot.send_message(
        telegram_id,
        Messages.MENU_CHANGED.format(menu=Buttons.MAIN_LOCATION.value),
        reply_markup=await reply_keyboard(Buttons.LOCATION.menu()),
        parse_mode="MarkdownV2",
    )


# Functions for buttons.


@dp.message_handler(Text(equals=Buttons.CHANGE_LOCATION.value))
async def change_location(message: types.Message):
    telegram_id, username = await get_user_data(message)

    message = await bot.send_message(
        telegram_id, Messages.SEARCH_LOCATION.escaped(), parse_mode="MarkdownV2"
    )
    dp.register_message_handler(location_search)

    logger.debug(
        f"Registered message handler (location_search) for user with telegram ID [{telegram_id}]."
    )


async def location_search(message: types.Message):
    telegram_id, username = await get_user_data(message)
    query = message.text

    instance = Instance(telegram_id)
    search_results = instance.search(query)

    if not search_results:
        await bot.send_message(
            telegram_id, Messages.NO_RESULTS.escaped(), parse_mode="MarkdownV2"
        )
        return

    inline_buttons = {
        f"setlocation_{result['name']}": f"{result['name']}, {result['country']}"
        for result in search_results
    }

    await bot.send_message(
        telegram_id,
        Messages.SEARCH_RESULTS.escaped(),
        reply_markup=await inline_keyboard(inline_buttons),
        parse_mode="MarkdownV2",
    )

    logger.debug(
        f"Sent to user with telegram ID [{telegram_id}] search results with length {len(inline_buttons)}."
    )

    dp.message_handlers.unregister(location_search)

    logger.debug(
        f"Cleared message handler (location_search) for user with telegram ID [{telegram_id}]."
    )


# Functions for callback data catching.


@dp.callback_query_handler(text_contains="setlocation_")
async def setlocation_callback(callback_query: types.CallbackQuery):
    telegram_id, username = await get_user_data(callback_query)
    location = callback_query.data.split("setlocation_")[1]

    db = Database(telegram_id)
    db.update_location(username, location)


# Keyboard generators.


async def reply_keyboard(reply_buttons: list):
    reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for button in reply_buttons:
        reply_keyboard.add(KeyboardButton(button))

    logger.debug(f"Generated reply keyboard with length {len(reply_buttons)}.")

    return reply_keyboard


async def inline_keyboard(inline_buttons: dict):
    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    for callback_data, text in inline_buttons.items():
        inline_keyboard.add(
            InlineKeyboardButton(callback_data=callback_data, text=text)
        )

    logger.debug(f"Generated inline keyboard with length {len(inline_buttons)}.")

    return inline_keyboard


# Utility functons.


async def get_user_data(data: dict):
    """Extracting data from message or callback and logging it."""
    telegram_id = data.from_user.id
    username = data.from_user.username

    try:
        logger.debug(
            f"Message from {username} with telegram ID {telegram_id}: {data.text}."
        )
    except AttributeError:
        logger.debug(
            f"Callback from {username} with telegram ID {telegram_id}: {data.data}."
        )

    return telegram_id, username


if __name__ == "__main__":
    logger.info("Bot starting.")
    executor.start_polling(dp)
