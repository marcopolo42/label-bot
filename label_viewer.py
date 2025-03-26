import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import asyncio
from label_cog.src.template import Template, TemplateException
from label_cog.src.label import Label
from label_cog.src.view_utils import get_templates_values
from label_cog.src.logging_dotenv import setup_logger
import threading

logger = setup_logger(__name__)


class LabelTesterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Label Tester")
        self.root.focus_force()
        self.label = Label()
        self.lang = "en"  # Set default language

        # Dropdown menu for label types
        self.label_type_var = tk.StringVar()
        self.label_type_menu = ttk.Combobox(root, textvariable=self.label_type_var)
        self.label_type_menu['values'] = self.get_label_types()
        self.label_type_menu.grid(row=0, column=0, padx=10, pady=10)
        self.label_type_menu.bind("<<ComboboxSelected>>", self.on_label_type_selected)

        # Button to reload the label
        self.reload_button = tk.Button(root, text="Reload Label", command=self.reload_label)
        self.reload_button.grid(row=1, column=0, padx=10, pady=10)

        # Label to display the preview image
        self.preview_label = tk.Label(root)
        self.preview_label.grid(row=2, column=0, padx=10, pady=10)

    def get_label_types(self):
        options = get_templates_values()
        logger.debug(f"Label types: {options}")
        # Fetch available label types
        return options

    def on_label_type_selected(self, event):
        label_type = self.label_type_var.get()
        threading.Thread(target=self.run_async_render, args=(label_type,)).start()

    def run_async_render(self, label_type):
        asyncio.run(self.render_label(label_type))

    async def render_label(self, label_type):
        logger.debug(f"Rendering label for type: {label_type}")
        try:
            self.label.template = Template(label_type, self.lang, None)
            await self.label.make()
            self.display_preview(self.label.img_preview)
        except TemplateException as e:
            logger.error(f"TemplateException: {e}")
        except Exception as e:
            raise e

    def display_preview(self, image_path):
        image = Image.open(image_path)
        image.thumbnail((600, 600))
        photo = ImageTk.PhotoImage(image)
        self.preview_label.config(image=photo)
        self.preview_label.image = photo

    def reload_label(self):
        label_type = self.label_type_var.get()
        threading.Thread(target=self.run_async_render, args=(label_type,)).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = LabelTesterApp(root)
    root.mainloop()