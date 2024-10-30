import os
from datetime import datetime
from label_cog.src.utils import pdf_to_image, convert_to_grayscale, get_time, get_discord_url
from blabel import LabelWriter


class Label:
    def __init__(self, author):
        self.template = None
        self.count = 1
        self.validated = None
        # default information that is always available. More info can be added based on the template config
        self.data = dict(
            user_name=author.display_name,
            user_picture=author.avatar,
            user_url=get_discord_url(str(author.id)),
            creation_date=get_time()
        )
        #return files
        self.pdf = None
        self.image = None

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
                                   default_stylesheets=(f"{directory}/style.css",)) # todo check if this works for images

        # Set the settings from the template to the data available for the label creation
        if self.template.settings:
            for key, value in self.template.settings.items():
                self.data.update({key: value})

        # Makes multiple copies of the label #todo will be removed in the future because we will print the images not the pdfs
        records = []
        for i in range(self.count):
            records.append(self.data)

        # Writes the labels to a PDF file with a unique file name using the author's ID and the current timestamp
        self.pdf = os.path.join(os.getcwd(), 'label_cog', 'pdfs', f"{self.data.get("user_name")}_{datetime.now().strftime('%d-%m-%Y-%Hh%Mm%Ss')}.pdfs")
        label_writer.write_labels(records, target=self.pdf)
        self.image = pdf_to_image(self.pdf)
        convert_to_grayscale(self.image)

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