import os

from PIL import Image, ImageDraw, ImageFont

import globals as g

from logger import Logger

logger = Logger(__name__)


class Drawer:
    def select_background(self, weather):
        code = weather.get("code")
        condition = "fair" if code in g.CONDITIONS_TYPES["fair"] else "rain"

        logger.debug(
            f"Readed code: [{code}] from weather data, identified it as [{condition}]."
        )

        is_day = weather.get("is_day")
        time = "day" if is_day == 1 else "night"

        logger.debug(
            f"Readed is_day: [{is_day}] from weather data, identified it as [{time}]."
        )

        background = os.path.join(g.BACKGROUNDS_DIR, f"{condition}_{time}.png")

        logger.debug(f"Selected background: {background}.")

        return background

    def select_icon(self, link, is_day):
        time = "day" if is_day == 1 else "night"

        icon = os.path.join(g.ICONS_DIR, time, os.path.basename(link))

        logger.debug(f"Path to the selected icon: [{icon}].")

        return icon

    def draw_current_weather(self, weather):
        background = self.select_background(weather)
        icon = self.select_icon(weather.get("icon"), weather.get("is_day"))

        XY_NAME = (256, 50)
        XY_DATE = (256, 140)
        XY_TEMP = (256, 280)
        XY_ICON = (512, 0, 1024, 512)

        background_image = Image.open(background)

        logger.debug(f"Successfully opened background image: [{background}].")

        icon_image = Image.open(icon).convert("RGBA")

        logger.debug(f"Successfully opened icon image: [{icon}].")

        try:
            background_image.paste(icon_image, XY_ICON, mask=icon_image)

            logger.debug("Successfully pasted icon on the background image.")

        except Exception as error:
            logger.error(
                f"Error while pasting icon on the background image: [{error}]."
            )

        draw = ImageDraw.Draw(background_image)

        if len(weather.get("name")) > 10:
            name_font = ImageFont.truetype(g.ARIMO_BOLD, 50)

            logger.debug(
                f"Name of the city [{weather.get('name')}] is too long, using smaller font."
            )

        else:
            name_font = ImageFont.truetype(g.ARIMO_BOLD, 80)

        date_font = ImageFont.truetype(g.ARIMO_BOLD, 20)
        temp_font = ImageFont.truetype(g.ARIMO_BOLD, 100)
        base_font = ImageFont.truetype(g.ARIMO_BOLD, 60)

        draw.text(
            XY_NAME, weather.get("name"), font=name_font, fill="white", anchor="mt"
        )

        draw.text(
            XY_DATE,
            weather.get("localtime"),
            font=date_font,
            fill="white",
            anchor="mt",
        )

        draw.text(
            XY_TEMP,
            f"{weather.get('feelslike_c')} °С",
            font=temp_font,
            fill="white",
            anchor="mt",
        )

        logger.debug(
            "Successfully drawn name, date and temperature on the background image."
        )

        xy_base = {
            f"{weather.get('wind_dir')}": (356, 630),
            f"{weather.get('wind_kph')} km/h": (356, 690),
            f"{weather.get('humidity')} %": (356, 910),
            f"{weather.get('pressure_mb')} mm": (668, 660),
            f"{round(float(weather.get('uv')), 1)}": (668, 910),
        }

        for text, xy in xy_base.items():
            draw.text(xy, text, font=base_font, fill="white", anchor="mt")

            logger.debug(f"Successfully drawn [{text}] on the background image.")

        filepath = os.path.join(g.TMP_DIR, f"current_weather_{weather.get('name')}.png")

        background_image.save(filepath)

        logger.debug(f"Successfully saved image to: [{filepath}].")

        return filepath

    def draw_forecast_weather(self, weather: list, metadata: dict[str, int]) -> str:
        XY_DATE = (256, 82)
        XY_TEMP = (768, 50)
        ROW_XS, ROW_YS = 32, 110
        CELL_H, CELL_W = 200, 160
        ROWS, COLS = 4, 6

        background = os.path.join(g.BACKGROUNDS_DIR, "forecast.png")

        logger.debug(f"Selected background: {background}.")

        background_image = Image.open(background)

        logger.debug(f"Successfully opened background image: [{background}].")

        draw = ImageDraw.Draw(background_image)

        base_font = ImageFont.truetype(g.ARIMO_BOLD, 50)
        date_font = ImageFont.truetype(g.ARIMO_BOLD, 20)
        temp_font = ImageFont.truetype(g.ARIMO_BOLD, 70)

        draw.text(
            XY_DATE,
            metadata.get("date"),
            font=date_font,
            fill="white",
            anchor="mm",
        )

        draw.text(
            XY_TEMP,
            f"{metadata.get('maxtemp_c')} / {metadata.get('mintemp_c')} °С",
            font=temp_font,
            fill="white",
            anchor="mm",
        )

        logger.debug("Successfully drawn date and temperature on the background image.")

        xy_base = {
            f"{metadata.get('location')}": (256, 35),
            f"{metadata.get('avg_humidity')} %": (272, 960),
            f"{metadata.get('sunrise')}": (592, 960),
            f"{metadata.get('sunset')}": (912, 960),
        }

        for text, xy in xy_base.items():
            draw.text(xy, text, font=base_font, fill="white", anchor="mm")

            logger.debug(f"Successfully drawn [{text}] on the background image.")

        hour_font = ImageFont.truetype(g.ARIMO_BOLD, 20)
        temp_font = ImageFont.truetype(g.ARIMO_BOLD, 30)
        rain_font = ImageFont.truetype(g.ARIMO_BOLD, 20)

        for row in range(ROWS):

            logger.debug(f"Starting to draw row [{row}]...")

            y = ROW_YS + row * CELL_H
            for col in range(COLS):

                logger.debug(f"Starting to draw column [{col}]...")

                x = ROW_XS + col * CELL_W

                index = row * COLS + col

                hour = weather[index].get("time")
                temp = weather[index].get("feelslike_c")
                prec = max(
                    weather[index].get("chance_of_rain"),
                    weather[index].get("chance_of_snow"),
                )

                logger.debug(
                    f"Got cell data. Hour: [{hour}], temp: [{temp}], prec: [{prec}]."
                )

                draw.text(
                    (x + 80, y + 10), hour, font=hour_font, fill="white", anchor="mt"
                )

                draw.text(
                    (x + 80, y + 140),
                    f"{temp} °С",
                    font=temp_font,
                    fill="white",
                    anchor="mt",
                )

                if prec > 0:
                    draw.text(
                        (x + 80, y + 170),
                        f"{prec} %",
                        font=rain_font,
                        fill="#007ae1",
                        anchor="mt",
                    )

                icon = self.select_icon(
                    weather[index].get("icon"), weather[index].get("is_day")
                )

                icon_image = Image.open(icon).convert("RGBA")
                icon_image = icon_image.resize((100, 100))

                try:
                    background_image.paste(
                        icon_image, (x + 30, y + 30), mask=icon_image
                    )

                    # logger.debug("Successfully pasted icon on the background image.")

                except Exception as error:
                    logger.error(
                        f"Error while pasting icon on the background image: [{error}]."
                    )

                logger.debug(f"Finished working on index [{index}] and column [{col}].")

            logger.debug(f"Finished working on row [{row}].")

        logger.debug("Successfully drawn all cells on the background image.")

        filepath = os.path.join(
            g.TMP_DIR, f"forecast_weather_{metadata.get('location')}.png"
        )

        background_image.save(filepath)

        logger.debug(f"Successfully saved image to: [{filepath}].")

        return filepath
