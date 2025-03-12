from label_cog.src.config import Config

from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)


class Session:
    def __init__(self, author, lang):
        self.author = author
        self.roles = Roles(author.roles)
        self.lang = lang


class Roles:
    def __init__(self, author_roles):
        self.names_lower = [role.name.lower() for role in author_roles]
        self.add_bocal_if_needed()

    def is_bocal_role(self):
        bocal_roles = [role.lower() for role in Config().get("bocal_roles")]
        return any(role in self.names_lower for role in bocal_roles)

    def add_bocal_if_needed(self):
        if self.is_bocal_role():
            logger.info("User has a bocal role")
            self.names_lower.append(Config().get("bocal_role_name").lower())

    def set_as_only_role(self, role):
        self.names_lower = [role.lower()]