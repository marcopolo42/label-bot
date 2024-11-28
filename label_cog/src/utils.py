from datetime import datetime, timedelta
from label_cog.src.config import Config


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


