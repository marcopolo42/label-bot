from datetime import datetime, timedelta
from random import randint


def get_user_role_icon(user_roles, user_name):
    #easter egg
    print(f"user_name: {user_name}")
    if "duck" in user_name.lower() or "jaqueme" in user_name.lower():
        return "🦆"
    if "smash" in user_name.lower():
        return "🏆"
    if "belarbi" in user_name.lower():
        return " 🏎️"

    print(f"roles: {user_roles}")
    if "alumni" in user_roles:
        return "🎓"
    if "student" in user_roles:
        return "📚"
    if "bocal" in user_roles:
        return "🐟"
    if "piscine" in user_roles:
        return "🏊"
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
    print(f"expiration_lengths: {expiration_lengths}")
    print(f"user_roles: {user_roles}")
    days_to_add = 1 #minimum expiration in case no role is found
    for role in user_roles:
        if role in expiration_lengths:
            if role == "bocal":
                return "∞"
            if days_to_add < expiration_lengths[role]:
                days_to_add = expiration_lengths[role]
    print(f"days_to_add: {days_to_add}")
    return get_time(days_to_add)


def process_data(data):
    print("Data received in backend")
    print(data)
    new_data = {
        "expiration_date": get_role_expiration_date(data.get("user_roles", []), data),
        "user_icon": get_user_role_icon(data.get("user_roles", []), data.get("user_display_name")),
        "random_number": randint(0, 100)} #for easter egg
    return new_data

