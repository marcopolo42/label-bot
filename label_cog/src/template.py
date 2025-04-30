from label_cog.src.database import get_today_prints_count

from label_cog.src.config import Config

from label_cog.src.utils import get_lang

import importlib.util

import os

from label_cog.src.utils import get_discord_url, get_local_directory
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)


class TemplateException(Exception):
    pass


class Template:
    def __init__(self):
        self.key = None
        self.data = dict()

    def _load_raw_template_config(self, type):
        if type == "no_templates":
            raise TemplateException("no_templates")
        templates = Config().get("templates")
        template = None
        for t in templates:
            if t["key"] == type:
                template = t
                break
        if template is None:
            raise TemplateException("missing_template_config")
        return template

    def load(self, type, author, lang):
        try:
            self._assign_values(type, lang)
            self._add_and_validate_files()
            self._load_data(author)
        except TemplateException as e:
            logger.error(f"Error loading template config: {e}")
            return str(e)
        except Exception as e:
            logger.error(f"Error loading template config: {e}")
            raise e

    def _assign_values(self, type, lang):
        raw = self._load_raw_template_config(type)
        self.key = raw.get("key")

        self._add_and_validate_files()

        self.name = get_lang(raw.get("name"), lang)
        self.description = get_lang(raw.get("description"), lang)
        self.emoji = raw.get("emoji", "🏷")
        self.settings = raw.get("settings", None)
        self.allowed_roles = raw.get("allowed_roles", None)
        self.daily_role_limits = raw.get("daily_role_limits", None)
        self.fields = raw.get("fields", None)
        self.free = raw.get("free", False)
        self.reload_button = raw.get("reload_button", False)

    def _add_and_validate_files(self):
        self.folder_path = get_local_directory("templates", self.key)
        if not os.path.isdir(self.folder_path):
            raise TemplateException("missing_template_folder")

        self.html_path = os.path.join(self.folder_path, "template.html")
        self.style_path = os.path.join(self.folder_path, "style.css")
        self.backend_path = os.path.join(self.folder_path, "backend.py")

        if (not os.path.exists(self.html_path)
                or not os.path.exists(self.style_path)):
            raise TemplateException("missing_template_files")

    def _load_data(self, author):
        # data is not cleared before loading a new template to keep memmory of previously uploaded data from the user
        self.add_author_data(author)
        self.add_settings_data()
        # backend data is processed later when making the label so that it can use the user filled data

    def get_daily_role_limit(self, user_roles):
        if self.daily_role_limits is None:
            return 25
        limit_found_flag = False
        limit = 0
        u_roles = [role.name.lower() for role in user_roles]
        a_roles = [role.lower() for role in self.allowed_roles]
        for role in u_roles:
            if role in a_roles:
                tmp = self.daily_role_limits.get(role, 0)
                if tmp > limit:
                    limit = tmp
                    limit_found_flag = True

        if not limit_found_flag:
            limit = 25
        return limit

    async def get_prints_available_today(self, author):
        limit = self.get_daily_role_limit(author.roles)
        available = limit - await get_today_prints_count(author, self.key)
        if available < 0:
            return 0
        return available

    def add_author_data(self, author):
        if author is None:
            return
        # default information that is always available. More info can be added based on the template configuration file
        new_data = dict(
            user_id=str(author.id),
            user_at=f"@{author.name}",
            user_name=author.name,
            user_display_name=author.display_name,
            user_picture=author.avatar,
            user_url=get_discord_url(str(author.id)), # todo move to backend of label
            user_roles=[role.name.lower() for role in author.roles],
        )
        self.data.update(new_data)

    def add_settings_data(self):
        if self.settings:
            for key, value in self.settings.items():
                self.data.update({key: value})

    async def process_backend_data(self):
        if not os.path.exists(self.backend_path):
            return
        # Load the module dynamically
        # The backend is a python file in the template folder with specific code that processes data for the template
        spec = importlib.util.spec_from_file_location("backend", self.backend_path)
        backend_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(backend_module)
        # backend.pry should define an async function `process_data` that returns a dictionary and has a parameter `data` to use the settings data
        if hasattr(backend_module, 'process_data'):
            processed_data = await backend_module.process_data(self.data)
            if processed_data is not None:
                self.data.update(processed_data)
        else:
            logger.error(f"Backend for {self.key} is missing the process_data function")
