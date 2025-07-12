from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster
from label_cog.src.database import can_user_afford, spend_user_coins
from label_cog.src.config import Config
from asyncio import sleep as aio_sleep

from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)

import os
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)


def get_cost_of_area_in_cents(area_mm2):
    roll_width = Config().get("roll_width")
    roll_length = Config().get("roll_length")
    roll_price = Config().get("roll_price")
    roll_area_mm2 = roll_width * roll_length
    roll_price_in_cents = roll_price * 100  # convert to cents
    roll_price_in_cents_per_mm2 = roll_price_in_cents / roll_area_mm2
    cost_of_area_in_cents = area_mm2 * roll_price_in_cents_per_mm2
    return cost_of_area_in_cents


def get_area_of_label(label):
    # get the size of the label in mm
    ppi = 600
    img_width_mm = round((label.img_print.size[0] / ppi) * 25.4)
    img_height_mm = round((label.img_print.size[1] / ppi) * 25.4)
    img_area_mm2 = img_width_mm * img_height_mm
    logger.debug(
        f"label.img_print.size: {label.img_print.size}\n"
        f"\nlabel size in mm: {img_width_mm} x {img_height_mm}"
        f"\nlabel size in mm2: {img_area_mm2}"
        f"\nrotation: {('0' if label.img_print.size[0] <= 1465 else '90')}\n"
        f"\nPPI: {ppi}"
    )
    return img_area_mm2


#mesure in cm squared the surface area of a label being printed.
def cost_of_sticker_in_coins(label):
    if label.template.free:
        return 0
    img_area_mm2 = get_area_of_label(label)
    cost = get_cost_of_area_in_cents(img_area_mm2)
    cost_in_coins = round((cost / 100) / Config().get("coin_value"))
    logger.debug(
        f"cost of label in cents: {cost}"
        f"\ncost of label in coins: {cost_in_coins}"
    )
    if cost_in_coins < 1:
        cost_in_coins = 1
    return cost_in_coins


def coins_to_money(coins):
    return int(coins * float(Config().get("coin_value")))


def money_to_coins(money):
    return int(money / float(Config().get("coin_value")))



