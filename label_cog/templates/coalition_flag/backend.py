def get_coalition(user_roles):
    # the names should be in lowercase
    coalitions = ["house of cores", "house of processes", "house of threads", "the sharks", "the frogs", "the penguins"]
    common_elements = [role.lower() for role in coalitions if role in user_roles]
    if common_elements:
        print(f"common_elements: {common_elements}")
        return common_elements[0]
    return ""


def process_data(data):
    print("Data received in backend")
    print(data)
    new_data = {
        "coalition": get_coalition(data.get("user_roles", []))
    }
    return new_data

