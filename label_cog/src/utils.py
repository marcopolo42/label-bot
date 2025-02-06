from datetime import datetime, timedelta
from label_cog.src.config import Config
import os


def get_lang(dict, lang):
    if dict is None:
        return None
    languages_codes = [language.get("key") for language in Config().get("languages")]
    if lang not in languages_codes:
        print(f"Language {lang} not found in the config file")
        lang = "en"
    if lang not in dict:
        return dict[list(dict.keys())[0]]
    else:
        return dict.get(lang)


def get_translation(key, lang):
    translations = Config().get("translations")
    if translations is None:
        raise ValueError("Translations are missing from the config file")
    if key not in translations:
        raise ValueError(f"translation of {key} is missing from the config file")
    return get_lang(translations.get(key), lang)


def get_time(days_to_add=0):
    if days_to_add is None:
        days_to_add = 0
    time = datetime.now() + timedelta(days=days_to_add)
    return time.strftime("%d.%m.%Y %Hh")


def get_discord_url(id):
    if id is None:
        return None
    # return "https://profile.intra.42.fr/users/" + id
    return "https://discordapp.com/users/" + str(id)


def get_local_directory(folder=None, folder_or_file=None):
    if folder is None:
        return os.path.join(os.getcwd(), 'label_cog')
    if folder_or_file is None:
        return os.path.join(os.getcwd(), 'label_cog', folder)
    else:
        return os.path.join(os.getcwd(), 'label_cog', folder, folder_or_file)


def get_cache_directory(file_name=None):
    if file_name is None:
        file_name = ""
    env = os.getenv('ENV')
    if env == 'prod':
        return os.path.join("/dev/shm", 'label_bot', 'cache', file_name)
    if env == 'dev':
        return os.path.join(os.getcwd(), 'label_cog', 'cache', file_name)
    else:
        print("ENV is not set")
        return os.path.join(os.getcwd(), 'label_cog', 'cache', file_name)
