import os
from datetime import datetime
from blabel import LabelWriter
from label_cog.src.image_utils import pdf_to_pil_img, convert_to_grayscale, add_margins, invert_image, mirror_image, pil_to_BytesIO
from label_cog.src.coins_render import add_price_icon
import random
import aiofiles
import aiofiles.os
import label_cog.src.global_vars as global_vars
from label_cog.src.logging_dotenv import setup_logger
from label_cog.src.coins import cost_of_sticker_in_coins
from io import BytesIO
from PIL import Image
logger = setup_logger(__name__)


class Label:
    def __init__(self):
        self.template = None
        self.count = 1
        self.cost = 0
        #return files
        self.img_print = None
        self.img_preview = None

    async def make(self):
        # removes previous files
        if self.template is None or self.count < 1:
            return

        # wait for the user provided image and add it to the data
        if self.template.settings is not None and self.template.settings.get("image_upload") is not None:
            future = global_vars.file_uploads_futures.get(int(self.template.data.get("user_id")))
            file_bytes = await future
            self.template.data.update({"img_bytes": file_bytes})

        await self.template.process_backend_data() # process the backend data before creating the final label

        # the file name is created using the author's ID and the current timestamp
        #file_name = f"{self.template.data.get('user_name')}_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}"
        #base_path = get_cache_directory(file_name=file_name)

        #image creation
        label_writer = LabelWriter(item_template_path=f"{self.template.folder_path}/template.html",
                                   default_stylesheets=(f"{self.template.folder_path}/style.css",))
        records = [self.template.data]
        raw_pdf = label_writer.write_labels(records)
        self.img_print = pdf_to_pil_img(raw_pdf)
        self.img_print = convert_to_grayscale(self.img_print)
        self.cost = cost_of_sticker_in_coins(self)

        #preview creation
        self.img_preview = add_margins(self.img_print, (3, 3, 3, 3), dpi=300)
        self.img_preview = add_price_icon(self.img_preview, self.cost)

        self.easter_egg()

    def easter_egg(self):
        # one out of 100 labels will be inverted or mirrored
        #if "food" in self.template.key:  # todo update with final templates names
        if random.randint(0, 100) == 0:
            self.img_preview = invert_image(self.img_preview)
            self.img_print = invert_image(self.img_print)
        if random.randint(0, 100) == 0:
            self.img_preview = mirror_image(self.img_preview)
            self.img_print = mirror_image(self.img_print)

    async def reset(self):
        self.img_print = None
        self.img_preview = None
        self.template = None
        self.count = 0
