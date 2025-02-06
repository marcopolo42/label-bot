import os
from datetime import datetime
from label_cog.src.utils import get_cache_directory
from blabel import LabelWriter
from label_cog.src.image_utils import pdf_to_image, convert_to_grayscale, add_margin, invert_image, mirror_image
import random

class Label:
    def __init__(self):
        self.template = None
        self.count = 1
        #return files
        self.pdf = None
        self.image = None
        self.preview = None

    def make(self):
        # removes previous files
        self.clear_files()
        if self.template is None or self.count < 1:
            return

        self.template.process_backend_data() # process the backend data before creating the final label

        # the file name is created using the author's ID and the current timestamp
        file_name = f"{self.template.data.get('user_name')}_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}"
        base_path = get_cache_directory(file_name=file_name)
        self.pdf = base_path + ".pdf"
        self.image = base_path + ".png"
        self.preview = base_path + "_preview.png"

        label_writer = LabelWriter(item_template_path=f"{self.template.folder_path}/template.html",
                                   default_stylesheets=(f"{self.template.folder_path}/style.css",))
        #pdf creation
        records = [self.template.data]
        label_writer.write_labels(records, target=self.pdf)
        #image creation
        pdf_to_image(self.pdf, self.image)
        convert_to_grayscale(self.image)
        #creation of the preview from the printed image
        add_margin(self.image, self.preview, margin_mm=3, dpi=300)
        self.easter_egg()

    def easter_egg(self):
        # one out of 100 labels will be inverted or mirrored
        if "food" in self.template.key:  # todo update with final templates names
            if random.randint(0, 100) == 0:
                invert_image(self.preview)
                invert_image(self.image)
            if random.randint(0, 100) == 0:
                mirror_image(self.preview)
                mirror_image(self.image)

    def clear_files(self):
        print("clearing label files")
        if self.pdf is not None and os.path.exists(self.pdf):
            os.remove(self.pdf)
            self.pdf = None
        if self.image is not None and os.path.exists(self.image):
            os.remove(self.image)
            self.image = None
        if self.preview is not None and os.path.exists(self.preview):
            os.remove(self.preview)
            self.preview = None
        print(f"pdf: {self.pdf}, image: {self.image}")

    def reset(self):
        self.clear_files()
        self.template = None
        self.count = 0