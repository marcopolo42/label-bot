import os
from PIL import Image, ImageOps
import fitz # PyMuPDF

Image.MAX_IMAGE_PIXELS = 33177600  # Increase pixel limit for the PIL dependency (8K)


def convert_to_grayscale(image_path):
    image = Image.open(image_path)
    grayscale_image = ImageOps.grayscale(image)
    grayscale_image.save(image_path)


def pdf_to_image(pdf, image_path):
    doc = fitz.open(pdf)  # we are using pymupdf because it is easier to install than pdf2image(poppler)
    page = doc.load_page(0)
    # get the pixmap of the page at 600 dpi
    pix = page.get_pixmap(alpha=False, dpi=600)  # todo does 600 instead of 300 work better ?
    pix.save(image_path)
    doc.close()


def add_margin(image_path, output_path, margin_mm, dpi=300):
    """
    Adds a white margin around an image.

    :param image_path: Path to the original image.
    :param output_path: Path to save the new image with the margin.
    :param margin_mm: Size of the margin in millimeters.
    :param dpi: Dots per inch of the image for conversion to pixels.
    """
    # Open the original image
    img = Image.open(image_path)

    # Convert mm to pixels
    margin_px = int((margin_mm / 25.4) * dpi)

    # Calculate new dimensions
    new_width = img.width + 2 * margin_px
    new_height = img.height + 2 * margin_px

    # Create a new image with white background
    new_img = Image.new("RGB", (new_width, new_height), color="white")

    # Paste the original image onto the new image, centered
    new_img.paste(img, (margin_px, margin_px))

    # Save the resulting image
    new_img.save(output_path)
    print(f"Image with margin saved to {output_path}")


def invert_image(image_path):
    image = Image.open(image_path)
    inverted_image = ImageOps.invert(image)
    inverted_image.save(image_path)


def mirror_image(image_path):
    image = Image.open(image_path)
    mirrored_image = ImageOps.mirror(image)
    mirrored_image.save(image_path)