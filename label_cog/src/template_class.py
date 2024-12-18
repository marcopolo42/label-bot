from label_cog.src.db_utils import get_today_prints_count

from label_cog.src.config import Config

from label_cog.src.utils import get_lang

import importlib.util

import os


class TemplateException(Exception):
    pass


class Template:
    def __init__(self, type, lang):
        raw = self.load_template_config(type)
        self.key = raw.get("key")

        # the folder name of the template should be the same as the value
        self.folder_path = os.path.join(os.getcwd(), 'label_cog', 'templates', self.key)
        if not os.path.exists(self.folder_path):
            raise TemplateException("missing_template_folder")

        self.name = get_lang(raw.get("name"), lang)
        self.description = get_lang(raw.get("description"), lang)
        self.emoji = raw.get("emoji")
        self.settings = raw.get("settings")
        self.allowed_roles = raw.get("allowed_roles")
        self.daily_role_limits = raw.get("daily_role_limits")
        self.fields = raw.get("fields")

        self.html_path = os.path.join(self.folder_path, "template.html")
        self.style_path = os.path.join(self.folder_path, "style.css")
        self.backend_path = os.path.join(self.folder_path, "backend.py")
        self.data = {}
        self.load_data()

    def load_template_config(self, type):
        templates = Config().get("templates")
        template = None
        for t in templates:
            if t["key"] == type:
                template = t
                break
        if template is None:
            raise TemplateException("missing_template_config")
        return template

    def load_data(self):
        self.add_settings_data()
        self.add_processed_backend_data()

    def get_daily_limit(self, user_roles):
        if self.daily_role_limits is None:
            return 25
        limit = 0
        u_roles = [role.name.lower() for role in user_roles]
        a_roles = [role.lower() for role in self.allowed_roles]
        for role in u_roles:
            if role in a_roles:
                tmp = self.daily_role_limits.get(role)
                if tmp is None:
                    tmp = 25
                if limit < tmp:
                    limit = tmp
        return limit

    def prints_available_today(self, author, conn):
        limit = self.get_daily_limit(author.roles)
        available = limit - get_today_prints_count(author, self.key, conn)
        if available < 0:
            return 0
        return available

    def add_settings_data(self):
        if self.settings:
            for key, value in self.settings.items():
                self.data.update({key: value})

    def add_processed_backend_data(self):
        if not os.path.exists(self.backend_path):
            return
        # Load the module dynamically
        # The backend is a python file in the template folder with specific code that processes data for the template
        spec = importlib.util.spec_from_file_location("backend", self.backend_path)
        backend_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(backend_module)
        # backend.py should define a function `process_data` that returns a dictionary and has a parameter `data` to use the settings data
        if hasattr(backend_module, 'process_data'):
            self.data.update(backend_module.process_data(self.data))
            print(f"Data processed by backend for {self.key}: {self.data}")
        else:
            print(f"Backend for {self.key} is missing the process_data function")
