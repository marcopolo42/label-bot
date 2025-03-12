import os
import yaml


# Singleton class
class Config(dict):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.load_config_files()
        return cls._instance

    def load_file(self, config_file):
        with open(config_file, mode='r') as f:
            config_data = yaml.safe_load(f.read())
        if config_data is None:
            return
        else:
            self.update(config_data)

    def load_config_files(self):
        config_dir = os.path.join(os.getcwd(), 'label_cog', 'config')
        for file in os.listdir(config_dir):
            if file.endswith('.yaml'):
                self.load_file(os.path.join(config_dir, file))

