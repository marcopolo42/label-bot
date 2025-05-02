from datetime import datetime, timedelta
from random import randint
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)


def get_user_role_icon(user_roles, user_name):
    # Find first matching name icon (case-insensitive)
    name_icons = {
        "duck": "🦆",
        "jaqueme": "🦆",
        "smash": "🏆",
        "belarbi": "🏎️"
    }
    username_lower = user_name.lower()
    if username_lower in name_icons:
        return name_icons[username_lower]

    # Find first matching role (case-insensitive)
    role_icons = {
        "alumni": "🎓",
        "student": "📚",
        "bocal": "🐟",
        "piscine": "🏊"
    }
    for role in user_roles:
        role_lower = role.lower()
        if role_lower in role_icons:
            return role_icons[role_lower]

    return ""


def get_time(days_to_add=0):
    if days_to_add is None:
        days_to_add = 0
    time = datetime.now() + timedelta(days=days_to_add)
    return time.strftime("%d.%m.%Y %Hh")


def get_role_expiration_date(user_roles, data):
    user_roles = [role.lower() for role in user_roles]

    #makes a list of all the keys starting with "expiration_" and removes it from the keys
    expiration_lengths = {key.replace("expiration_", ""): value for key, value in data.items() if key.startswith("expiration_")}
    logger.debug(f"expiration_lengths: {expiration_lengths}")
    logger.debug(f"user_roles: {user_roles}")
    days_to_add = 1 #minimum expiration in case no role is found
    for role in user_roles:
        if role in expiration_lengths:
            if role == "bocal":
                return "∞"
            if days_to_add < expiration_lengths[role]:
                days_to_add = expiration_lengths[role]
    logger.debug(f"days_to_add: {days_to_add}")
    return get_time(days_to_add)


def process_data(data):
    new_data = {
        "expiration_date": get_role_expiration_date(data.get("user_roles", []), data),
        "user_icon": get_user_role_icon(data.get("user_roles", []), data.get("user_display_name")),
        "random_number": randint(0, 100)} #for easter egg
    return new_data

