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
        self.update({os.path.basename(image_file): Image.open(image_file)})

    def load_assets(self):
        logger.debug("Loading assets")
        config_dir = os.path.join(os.getcwd(), 'label_cog', 'assets')
        for file in os.listdir(config_dir):
            logger.debug(f"Checking asset: {file}")
            if file.endswith('.png') or file.endswith('.jpg'):
                logger.debug(f"Loading asset: {file}")
                self.load_image(os.path.join(config_dir, file))
