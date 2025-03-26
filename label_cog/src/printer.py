from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster
from label_cog.src.database import can_user_afford, spend_user_coins

from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)

import os
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)


async def print_label(label, author):
    display_status = None
    if not await can_user_afford(author, label.template.price):
        return "not_enough_coins"
    try:
        print_status = ql_brother_print_usb(label.img_print, label.template.price)
    except Exception as e:
        logger.error(e, type(e), e.__traceback__, e.__dict__)
        logger.error(f"\033[91mError while printing: {e}\033[0m")
        display_status = "error_print"
    else:
        outcome = print_status.get("outcome")
        if outcome == "error":
            display_status = "error_print"
        elif outcome == "printed":
            display_status = "printed"
            await spend_user_coins(author, label.template.price)
        else:
            raise ValueError(f"Unexpected outcome: {outcome}")
    return display_status


def ql_brother_print_usb(img, count):
    printer = os.getenv("PRINTER_ID")
    backend = os.getenv("PRINTER_BACKEND") # 'pyusb', 'linux_kernel', 'network'
    model = os.getenv("PRINTER_MODEL")
    if img is None:
        raise ValueError("img is None")
    qlr = BrotherQLRaster(model)
    # enable if in dev mode
    qlr.exception_on_warning = True if os.getenv("ENV") == "dev" else False
    if img.size[0] > 1465 and img.size[1] > 1465: # todo enable proper error handling and test this
        logger.info("Image is too big to be printed in a 62mm label")
        raise ValueError("Image is too big to be printed in a 62mm label")
    instructions = convert(
        qlr=qlr,
        images=[img] * count, # Takes a list of file names or PIL objects.
        label='62',
        rotate=('0' if img.size[0] <= 1465 else '90'),  # 'Auto', '0', '90', '270'. 1465 is the width of a 62mm label in pixels
        threshold=70.0,  # Black and white threshold in percent.
        dither=True,
        compress=False,
        red=False,  # Only True if using Red/Black 62 mm label tape.
        dpi_600=False,
        hq=True,  # False for low quality.
        cut=True

    )
    status = send(instructions=instructions, printer_identifier=printer, backend_identifier=backend, blocking=True) #blocking means that the function will wait for the printer to finish printing before returning
    return status

