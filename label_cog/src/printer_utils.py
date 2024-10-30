from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster

from PIL import Image


def ql_brother_print_usb(image, count=1):
    if image is None:
        return
    im = Image.open(image)
    #print images size
    print(im.size) #todo remove debug
    print(f"height {im.size[0]} width {im.size[1]}") #todo remove debug
    backend = 'pyusb'  # 'pyusb', 'linux_kernel', 'network'
    model = 'QL-710W'
    printer = 'usb://0x04f9:0x20c0/000D9Z773204'  # Get these values from the Windows usb driver filter.  Linux/Raspberry Pi uses '/dev/usb/lp0'. Macos use 'lsusb' from homebrew.
    qlr = BrotherQLRaster(model)
    qlr.exception_on_warning = True #todo remove for production
    instructions = convert(

        qlr=qlr,
        images=[im],  # Takes a list of file names or PIL objects.
        label='62',
        rotate=('0' if im.size[0] > im.size[1] else '90'),  # 'Auto', '0', '90', '270'
        threshold=70.0,  # Black and white threshold in percent.
        dither=False,
        compress=False,
        red=False,  # Only True if using Red/Black 62 mm label tape.
        dpi_600=False,
        hq=True,  # False for low quality.
        cut=True

    )
    send(instructions=instructions, printer_identifier=printer, backend_identifier=backend, blocking=True)

