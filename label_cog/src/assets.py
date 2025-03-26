import os
import yaml
from PIL import Image
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)


# Singleton class
class Assets(dict):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Assets, cls).__new__(cls)
            cls._instance.load_assets()
        return cls._instance

    def load_image(self, image_file):
        with open(image_file, 'rb') as f: #using this instead of raw image.open to make sure it is read only.
            img = Image.open(f)
            img.load() #loading in memory so that it may lag only the first time.
            self.update({os.path.basename(image_file): img})

    def load_assets(self):
        logger.debug("Loading assets")
        config_dir = os.path.join(os.getcwd(), 'label_cog', 'assets')
        for file in os.listdir(config_dir):
            logger.debug(f"Checking asset: {file}")
            if file.endswith('.png') or file.endswith('.jpg'):
                logger.debug(f"Loading asset: {file}")
                self.load_image(os.path.join(config_dir, file))
