from datetime import datetime, timedelta
from label_cog.src.config import Config
import os
import socket
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)


def get_lang(dict, lang):
    if dict is None:
        return None
    languages_codes = [language.get("key") for language in Config().get("languages")]
    if lang not in languages_codes:
        logger.warning(f"Language {lang} not found in the config file")
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


def get_current_ip():
    # Step 1: Get the local hostname.
    local_hostname = socket.gethostname()
    # Step 2: Get a list of IP addresses associated with the hostname.
    ip_addresses = socket.gethostbyname_ex(local_hostname)[2]
    # Step 3: Filter out loopback addresses (IPs starting with "127.").
    filtered_ips = [ip for ip in ip_addresses if not ip.startswith("127.")]
    # Step 4: Extract the first IP address (if available) from the filtered list.
    first_ip = filtered_ips[:1]
    # Step 5: Print the obtained IP address to the console.
    return first_ip
