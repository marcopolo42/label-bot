import os
import yaml


# Singleton class
class Config(dict):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.update_from_file()
        return cls._instance

    def update_from_file(self):
        config_file = os.path.join(os.getcwd(), "label_cog", "config.yaml")
        with open(config_file, mode='r') as f:
            config_data = yaml.safe_load(f.read())
        self.update(config_data)
