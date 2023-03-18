import os

from PIL import Image, ImageDraw, ImageFont

import globals as g

from logger import Logger

logger = Logger(__name__)


class Drawer:
    def __init__(self, weather):
        self.weather = weather
        self.select_background()

    def select_background(self):
        code = self.weather.get("code")
        condition = "fair" if code in g.CONDITIONS_TYPES["fair"] else "rain"

        logger.debug(
            f"Readed code: [{code}] from weather data, identified it as [{condition}]."
        )

        is_day = self.weather.get("is_day")
        self.time = "day" if is_day == 1 else "night"

        logger.debug(
            f"Readed is_day: [{is_day}] from weather data, identified it as [{self.time}]."
        )

        self.background = os.path.join(
            g.BACKGROUNDS_DIR, f"{condition}_{self.time}.png"
        )

        logger.debug(f"Selected background: {self.background}.")

    def select_icon(self):
        self.icon = os.path.join(
            g.ICONS_DIR, self.time, os.path.basename(self.weather.get("icon"))
        )

        logger.debug(f"Path to the selected icon: [{self.icon}].")

    def draw_current_weather(self):
        XY_NAME = (256, 50)
        XY_DATE = (256, 140)
        XY_TEMP = (256, 280)
        XY_ICON = (512, 0, 1024, 512)

        self.select_icon()

        image = Image.open(self.background)

        logger.debug(f"Successfully opened background image: [{self.background}].")

        icon = Image.open(self.icon).convert("RGBA")

        logger.debug(f"Successfully opened icon image: [{self.icon}].")

        try:
            image.paste(icon, XY_ICON, mask=icon)

            logger.debug("Successfully pasted icon on the background image.")

        except Exception as error:
            logger.error(
                f"Error while pasting icon on the background image: [{error}]."
            )

        draw = ImageDraw.Draw(image)

        if len(self.weather.get("name")) > 10:
            name_font = ImageFont.truetype(g.ARIMO_BOLD, 50)

            logger.debug(
                f"Name of the city [{self.weather.get('name')}] is too long, using smaller font."
            )

        else:
            name_font = ImageFont.truetype(g.ARIMO_BOLD, 80)

        date_font = ImageFont.truetype(g.ARIMO_BOLD, 20)
        temp_font = ImageFont.truetype(g.ARIMO_BOLD, 100)
        base_font = ImageFont.truetype(g.ARIMO_BOLD, 60)

        draw.text(
            XY_NAME, self.weather.get("name"), font=name_font, fill="white", anchor="mt"
        )

        draw.text(
            XY_DATE,
            self.weather.get("localtime"),
            font=date_font,
            fill="white",
            anchor="mt",
        )

        draw.text(
            XY_TEMP,
            f"{self.weather.get('feelslike_c')} °С",
            font=temp_font,
            fill="white",
            anchor="mt",
        )

        logger.debug(
            "Successfully drawn name, date and temperature on the background image."
        )

        xy_base = {
            f"{self.weather.get('wind_dir')}": (356, 630),
            f"{self.weather.get('wind_kph')} km/h": (356, 690),
            f"{self.weather.get('humidity')} %": (356, 910),
            f"{self.weather.get('pressure_mb')} mm": (668, 660),
            f"{round(float(self.weather.get('uv')), 1)}": (668, 910),
        }

        for text, xy in xy_base.items():
            draw.text(xy, text, font=base_font, fill="white", anchor="mt")

            logger.debug(f"Successfully drawn [{text}] on the background image.")

        filepath = os.path.join(
            g.TMP_DIR, f"current_weather_{self.weather.get('name')}.png"
        )

        image.save(filepath)

        logger.debug(f"Successfully saved image to: [{filepath}].")

        return filepath
