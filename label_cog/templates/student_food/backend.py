from datetime import datetime, timedelta


def get_time(days_to_add=0):
    if days_to_add is None:
        days_to_add = 0
    time = datetime.now() + timedelta(days=days_to_add)
    return time.strftime("%d.%m.%Y %Hh")


def process_data(data):
    expiration_date = get_time(data.get("expiration"))
    return {"expiration_date": expiration_date}

