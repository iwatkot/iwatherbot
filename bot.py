import os
import asyncio

from enum import Enum
from re import escape

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from decouple import config

import globals as g

from logger import Logger
from database import Database
from api import Instance
from imaging import Drawer

logger = Logger(__name__)

storage = MemoryStorage()
bot = Bot(token=config("TOKEN"))

dp = Dispatcher(bot=bot, storage=storage)


class Messages(Enum):
    # Messages for commands.
    START = (
        "Hello, this bot can help you to get weather forecasts\\.\n\n"
        "To start using the bot, please save a location in the `Location` menu\\.\n\n"
        "Powered by [WeatherAPI](https://www.weatherapi.com/)\\."
    )

    # Messages for menu changes.
    MENU_CHANGED = "You switched to the  `{menu}` ."

    # Messages for locations.
    SEARCH_LOCATION = "Please, send the name of the  `location`  to search."
    SEARCH_RESULTS = "Please, choose the  `location`  from the list below."
    NO_RESULTS = "No results found for your query. Please, try again."
    LOCATION_UPDATED = "Your location has been updated to  `{location}` ."
    NO_LOCATION = (
        "You haven't saved a location yet. Please use the  `Change location`  "
        "button in the  `Location`  menu."
    )
    LOCATION = "You have a saved location:  `{location}` ."

    # Messages for errors and exceptions.
    DRAWING_ERROR = (
        "Something went wrong while drawing the image. Please, try again later."
    )
    NO_WEATHER = (
        "Something went wrong while getting weather data. Please, try again later."
    )

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

    MENU = [MAIN_FORECASTS, MAIN_LOCATION]
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
        Messages.START.value,
        reply_markup=await reply_keyboard(Buttons.MENU.menu()),
        parse_mode="MarkdownV2",
        disable_web_page_preview=True,
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


@dp.message_handler(Text(equals=Buttons.SAVED_LOCATION.value))
async def saved_location(message: types.Message):
    telegram_id, username = await get_user_data(message)

    db = Database(telegram_id)
    location = db.get_user_location()
    db.disconnect()

    if not location:
        await bot.send_message(
            telegram_id, Messages.NO_LOCATION.escaped(), parse_mode="MarkdownV2"
        )

        logger.debug(
            f"Sent to user with telegram ID [{telegram_id}] no location message."
        )

        return

    await bot.send_message(
        telegram_id,
        Messages.LOCATION.format(location=location),
        parse_mode="MarkdownV2",
    )

    logger.debug(
        f"Sent to user with telegram ID [{telegram_id}] location message. Location: [{location}]."
    )


@dp.message_handler(Text(equals=Buttons.CURRENT_WEATHER.value))
async def current_weather(message: types.Message):
    telegram_id, username = await get_user_data(message)

    db = Database(telegram_id)
    location = db.get_user_location()
    db.disconnect()

    if not location:
        await bot.send_message(
            telegram_id, Messages.NO_LOCATION.escaped(), parse_mode="MarkdownV2"
        )

        logger.debug(
            f"Sent to user with telegram ID [{telegram_id}] no location message."
        )

        return

    ins = Instance(telegram_id)
    response = ins.get_current_weather(location)

    if not response:
        await bot.send_message(
            telegram_id, Messages.NO_WEATHER.escaped(), parse_mode="MarkdownV2"
        )

        logger.warning(
            f"Sent to user with telegram ID [{telegram_id}] no weather message."
        )

        return

    weather = extract_current_weather(response.to_dict())

    d = Drawer(weather)
    image = d.draw_current_weather()

    if not image:
        await bot.send_message(
            telegram_id, Messages.DRAWING_ERROR.escaped(), parse_mode="MarkdownV2"
        )

        logger.warning(
            f"Sent to user with telegram ID [{telegram_id}] drawing error message."
        )

    photo = InputFile(image)

    await bot.send_photo(telegram_id, photo)

    logger.debug(
        f"Sent to user with telegram ID [{telegram_id}] current weather image."
    )

    await asyncio.sleep(60)

    try:
        os.remove(image)
        logger.debug(f"Successfully deleted image [{image}].")
    except FileNotFoundError:
        logger.error(f"There was an error while deleting image [{image}].")


# Functions for registered message handlers.


async def location_search(message: types.Message):
    telegram_id, username = await get_user_data(message)
    query = message.text

    instance = Instance(telegram_id)
    search_results = instance.search(query)

    if not search_results:
        await bot.send_message(
            telegram_id, Messages.NO_RESULTS.escaped(), parse_mode="MarkdownV2"
        )

        logger.debug(
            f"Sent to user with telegram ID [{telegram_id}] no results message. Search results: [{search_results}]."
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

    logger.debug(
        f"Extracted location [{location}] from callback data for user with telegram ID [{telegram_id}]."
    )

    db = Database(telegram_id)
    db.update_user(username, location)
    db.disconnect()

    await bot.send_message(
        telegram_id,
        Messages.LOCATION_UPDATED.format(location=location),
        parse_mode="MarkdownV2",
    )

    logger.debug(
        f"Sent to user with telegram ID [{telegram_id}] location update message."
    )


# Keyboard generators.


async def reply_keyboard(reply_buttons: list):
    reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for button in reply_buttons:
        reply_keyboard.add(KeyboardButton(button))

    logger.debug(f"Generated reply keyboard with length [{len(reply_buttons)}].")

    return reply_keyboard


async def inline_keyboard(inline_buttons: dict):
    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    for callback_data, text in inline_buttons.items():
        inline_keyboard.add(
            InlineKeyboardButton(callback_data=callback_data, text=text)
        )

    logger.debug(f"Generated inline keyboard with length [{len(inline_buttons)}].")

    return inline_keyboard


# Utility functons.


def extract_current_weather(data: dict):

    logger.debug(
        f"Starting to extract current weather from data dict with length [{len(data)}]."
    )

    return {
        "code": data["current"]["condition"]["code"],
        "icon": data["current"]["condition"]["icon"],
        "feelslike_c": data["current"]["feelslike_c"],
        "humidity": data["current"]["humidity"],
        "is_day": data["current"]["is_day"],
        "pressure_mb": data["current"]["pressure_mb"],
        "uv": data["current"]["uv"],
        "wind_dir": data["current"]["wind_dir"],
        "wind_kph": data["current"]["wind_kph"],
        "name": data["location"]["name"],
        "localtime": data["location"]["localtime"],
    }


async def get_user_data(data: dict):
    """Extracting data from message or callback and logging it."""
    telegram_id = data.from_user.id
    username = data.from_user.username

    try:
        logger.debug(
            f"Message from [{username}] with telegram ID [{telegram_id}]: [{data.text}]."
        )
    except AttributeError:
        logger.debug(
            f"Callback from [{username}] with telegram ID [{telegram_id}]: [{data.data}]."
        )

    return telegram_id, username


def init_checks():
    logger.debug("Starting initial checks.")

    logger.debug(f"Readed absolute path as [{g.ABSOLUTE_PATH}].")

    os.makedirs(g.LOG_DIR, exist_ok=True)
    os.makedirs(g.TMP_DIR, exist_ok=True)

    logger.debug(
        f"Created log directory as [{g.LOG_DIR}]. Created tmp directory as [{g.TMP_DIR}]."
    )

    logger.debug(f"The log file path is set to [{g.LOG_FILE}].")

    logger.debug(f"Loaded JSON file with [{len(g.CONDITIONS)}] conditions.")
    logger.debug(f"Loaded JSON file with [{len(g.CONDITIONS_TYPES)}] condition types.")

    logger.debug(f"Defined path to the font as [{g.ARIMO_BOLD}].")
    logger.debug(f"File with the font exists: [{os.path.exists(g.ARIMO_BOLD)}].")

    test = Database(0)

    if not test.exists_in_database():
        logger.debug("Successfully checked connection to the database.")

    test.disconnect()

    logger.debug("Initial checks successfully completed.")


if __name__ == "__main__":
    init_checks()
    logger.info("Bot starting.")
    executor.start_polling(dp)
