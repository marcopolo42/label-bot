import os
import base64
import mimetypes
import random
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)


def get_random_file(folder_path):
    """
    Get a random file from the specified folder.
    :param folder_path: The name of the folder to search in.
    :return: A random file path from the folder.
    """
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    if not files:
        logger.error(f"No files found in the folder: {folder_path}")
        return None
    return os.path.join(folder_path, random.choice(files))


# Convert an image to a Base64-encoded string with MIME prefix
# searches the local template folder for the image

def image_to_base64(image_path):
    try:
        # Guess the MIME type based on the file extension
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            raise ValueError(f"Cannot determine MIME type for file: {image_path}")

        with open(image_path, "rb") as image_file:  # Open in binary mode
            base64_data = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:{mime_type};base64,{base64_data}"
    except FileNotFoundError:
        logger.error(f"Error: File '{image_path}' not found.")
        return None
    except Exception as e:
        logger.error(f"An error occurred while processing the file: {e}")
        return None


def process_data(data):
    folder_name = "characters_art_smash"
    folder_path = str(os.path.join(os.path.dirname(os.path.abspath(__file__)), folder_name))
    image_path = get_random_file(folder_path)
    new_data = {
        "image_base64": image_to_base64(image_path),
    }
    return new_data
