from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)


def get_coalition(user_roles):
    # the names should be in lowercase
    coalitions = ["house of cores", "house of processes", "house of threads", "the sharks", "the frogs", "the penguins"]
    common_elements = [role.lower() for role in coalitions if role in user_roles]
    if common_elements:
        logger.debug(f"common_elements: {common_elements}")
        return common_elements[0]
    return ""


async def process_data(data):
    new_data = {
        "coalition": get_coalition(data.get("user_roles", []))
    }
    return new_data

