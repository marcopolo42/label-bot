from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster

from PIL import Image

Image.MAX_IMAGE_PIXELS = 33177600  # Increase pixel limit for the PIL dependency (8K)

import os
import dotenv
dotenv.load_dotenv()


def ql_brother_print_usb(image, count):
    printer = os.getenv("PRINTER_ID")
    backend = 'pyusb'  # 'pyusb', 'linux_kernel', 'network'
    model = os.getenv("PRINTER_MODEL")
    if image is None:
        return
    im = Image.open(image)
    qlr = BrotherQLRaster(model)
    # enable if in dev mode
    qlr.exception_on_warning = True if os.getenv("ENV") == "dev" else False
    if im.size[0] > 1465 and im.size[1] > 1465: # todo enable proper error handling and test this
        print("Image is too big to be printed in a 62mm label")
        raise ValueError("Image is too big to be printed in a 62mm label")
    instructions = convert(
        qlr=qlr,
        images=[im] * count, # Takes a list of file names or PIL objects.
        label='62',
        rotate=('0' if im.size[0] <= 1465 else '90'),  # 'Auto', '0', '90', '270'. 1465 is the width of a 62mm label in pixels
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

