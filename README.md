
## How and why
This Telegram bot is built on `aiogram`, `asyncio` and `aicron` libraries. It uses `sqlalchemy` and `psycopg2` to operate with PostgreSQL database, which stores all the data for users. The bot uses [WeatherAPI](https://www.weatherapi.com/) to get weather data and `PIL` to create images with weather forecasts.<br>
The main idea of this bot is to provide the possibility to get weather forecasts right in Telegram not with only formatted text, but with images. The user needs to search the location only one time and then he can just click on one button to receive the weather forecast as the location is already stored in the database. And as simple as adding you can always change the location. The next important feature is that the bot can send you notifications about the weather forecast for today and tomorrow. Just one click on the button will subscribe you to the selected notifications. And if you don't want to receive notifications anymore, just click on the button again and you will be unsubscribed.<br>

## Changelog
**2023/21/03** - Refactoring of functions, which using @aiogram.crontab. Added docstrings and type hints for functions it `database.py`.
**2023/21/03** - Added notifications about tomorrow and today's forecasts.
**2023/20/03** - Added functions for hour forecasts (today, tomorrow).
