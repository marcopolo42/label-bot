from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster
from label_cog.src.database import can_user_afford, spend_user_coins
from label_cog.src.coins import cost_of_sticker_in_coins
from label_cog.src.config import Config
from asyncio import sleep as aio_sleep

from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)

import os
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)


async def print_label(label, author):
    if not await can_user_afford(author, label.cost):
        return "not_enough_coins"
    try:
        print_status = ql_brother_print_usb(label.img_print, label.count)
    except Exception as e:
        if str(e) == "Device not found":
            logger.error("Printer not found")
            return "printer_not_found"
        else:
            logger.error(e, type(e), e.__traceback__, e.__dict__)
            logger.error(f"\033[91mError while printing: {e}\033[0m")
            return "error_print"
    else:
        outcome = print_status.get("outcome")
        if outcome == "printed":
            await spend_user_coins(author, label.cost)
            return "printed"
        else:
            logger.error(f"Print status: {print_status}")
            return "error_print"


def ql_brother_print_usb(img, count):
    printer = os.getenv("PRINTER_ID")
    backend = os.getenv("PRINTER_BACKEND") # 'pyusb', 'linux_kernel', 'network'
    model = os.getenv("PRINTER_MODEL")
    if img is None:
        raise ValueError("img is None")
    if count < 1:
        raise ValueError("print count is less than 1")
    qlr = BrotherQLRaster(model)
    # enabled in dev mode
    qlr.exception_on_warning = True if os.getenv("ENV") == "dev" else False
    if img.size[0] > 1465 and img.size[1] > 1465: # todo enable proper error handling and test this
        logger.info("Image is too big to be printed in a 62mm label")
        raise ValueError("Image is too big to be printed in a 62mm label")
    instructions = convert(
        qlr=qlr,
        images=[img] * count, # Takes a list of file names or PIL objects.
        label='62',
        rotate=('0' if img.size[0] <= 1465 else '90'),  # 'Auto', '0', '90', '270'. #
        threshold=70.0,  # Black and white threshold in percent. # todo test this
        dither=True,
        compress=False,
        red=False,  # Only True if using Red/Black 62 mm label tape.
        dpi_600=False,
        hq=True,  # False for low quality.
        cut=True

    )
    status = send(instructions=instructions, printer_identifier=printer, backend_identifier=backend, blocking=True) #blocking means that the function will wait for the printer to finish printing before returning
    return status

