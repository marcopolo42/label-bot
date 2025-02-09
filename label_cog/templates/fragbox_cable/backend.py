import os
import base64
import mimetypes


# Debugging: Print current working directory
print(f"Current working directory: {os.getcwd()}")


# Convert an image to a Base64-encoded string with MIME prefix
# searches the local template folder for the image
def image_to_base64(image_name):
    image_path = str(os.path.join(os.path.dirname(os.path.abspath(__file__)), image_name))
    try:
        # Guess the MIME type based on the file extension
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            raise ValueError(f"Cannot determine MIME type for file: {image_path}")

        with open(image_path, "rb") as image_file:  # Open in binary mode
            base64_data = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:{mime_type};base64,{base64_data}"
    except FileNotFoundError:
        print(f"Error: File '{image_path}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred while processing the file: {e}")
        return None


async def process_data(data):
    image_name = "text_fragbox.png"
    new_data = {
        "image_base64": image_to_base64(image_name),
    }
    return new_data
