import os
from datetime import datetime
from label_cog.src.utils import get_time, get_discord_url
from blabel import LabelWriter
from label_cog.src.image_utils import pdf_to_image, convert_to_grayscale, add_margin, invert_image, mirror_image
import random


class Label:
    def __init__(self, author):
        self.template = None
        self.count = 1
        self.validated = None
        # default information that is always available. More info can be added based on the template config
        self.data = dict(
            user_display_name=author.display_name,
            user_name=author.name,
            user_at=f"@{author.name}",
            user_picture=author.avatar,
            user_url=get_discord_url(str(author.id)),
            user_id=author.id,
            creation_date=get_time(),
            random_number=random.randint(0, 100)
        )
        #return files
        self.pdf = None
        self.image = None
        self.preview = None

    def make(self):
        # removes previous files
        self.clear()
        if self.template is None:
            return
        if self.count < 1:
            return

        # the folder name of the template should be the same as the value
        directory = os.path.join(os.getcwd(), 'label_cog', 'templates', self.template.key)
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Template folder for {self.template.key} is missing")
        label_writer = LabelWriter(item_template_path=f"{directory}/template.html",
                                   default_stylesheets=(f"{directory}/style.css",))

        # Set the data from the template
        if self.template.settings:
            for key, value in self.template.settings.items():
                self.data.update({key: value})
        #Set the data that need processing
        self.data.update({"expiration_date": get_time(self.data.get("expiration"))})

        # Makes multiple copies of the label #todo will be removed in the future because we will print the images not the pdfs
        records = []
        for i in range(self.count):
            records.append(self.data)

        # the file name is created using the author's ID and the current timestamp
        base_name = f"{self.data.get('user_name')}_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}"

        self.pdf = os.path.join(os.getcwd(), 'label_cog', 'cache', f"{base_name}.pdf")
        self.image = os.path.join(os.getcwd(), 'label_cog', 'cache', f"{base_name}.png")
        self.preview = os.path.join(os.getcwd(), 'label_cog', 'cache', f"{base_name}_preview.png")

        #pdf creation
        label_writer.write_labels(records, target=self.pdf)
        #image creation
        pdf_to_image(self.pdf, self.image)
        convert_to_grayscale(self.image)
        #creation of the preview from the printed image
        add_margin(self.image, self.preview, margin_mm=3, dpi=300)
        # easter egg random one out of 100 labels
        if "food" in self.template.key: #todo update with final templates names
            if random.randint(0, 100) == 0:
                invert_image(self.preview)
            if random.randint(0, 100) == 0:
                mirror_image(self.preview)

    def clear(self):
        print("clearing label files")
        if self.pdf is not None and os.path.exists(self.pdf):
            os.remove(self.pdf)
            self.pdf = None
        if self.image is not None and os.path.exists(self.image):
            os.remove(self.image)
            self.image = None
        print(f"pdf: {self.pdf}, image: {self.image}")

    def reset(self):
        self.clear()
        self.template = None
        self.count = 0
        self.validated = False