from label_cog.src.db_utils import get_today_prints_count

from label_cog.src.config import Config


class Template:
    def __init__(self, type, lang):
        lang = lang
        raw = self.load_template(type)
        self.key = raw.get("key")
        self.name = raw.get("name").get(lang)
        self.description = raw.get("description").get(lang)
        self.emoji = raw.get("emoji")

        self.settings = raw.get("settings")

        self.allowed_roles = raw.get("allowed_roles")

        self.daily_role_limits = raw.get("daily_role_limits")

        self.fields = raw.get("fields")

    def load_template(self, type):
        templates = Config().get("templates")
        template = None
        for t in templates:
            if t["key"] == type:
                template = t
                break
        if template is None:
            raise ValueError(f"Template {type} not found in config file")
        return template

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
