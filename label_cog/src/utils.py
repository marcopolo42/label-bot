import os
from datetime import datetime, timedelta
from PIL import Image, ImageOps
import fitz
import yaml
from label_cog.src.config import Config

Image.MAX_IMAGE_PIXELS = 8294400  # Increase pixel limit for the PIL dependency (4K)


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


def convert_to_grayscale(image_path):
    image = Image.open(image_path)
    grayscale_image = ImageOps.grayscale(image)
    grayscale_image.save(image_path)


def pdf_to_image(pdf):
    doc = fitz.open(pdf)  # we are using pymupdf because it is easier to install than pdf2image(poppler)
    page = doc.load_page(0)
    # get the pixmap of the page at 600 dpi
    pix = page.get_pixmap(alpha=False, dpi=600)  # todo does 600 instead of 300 work better ?
    image_path = f"{os.getcwd()}/label_cog/images/{os.path.splitext(os.path.basename(pdf))[0]}.png"
    pix.save(image_path)
    doc.close()
    return image_path
