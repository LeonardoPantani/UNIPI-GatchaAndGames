import re
import uuid
from datetime import datetime

MAX_PAGENUMBER = 1000
MIN_PAGENUMBER = 1


def sanitize_uuid_input(input_string):
    # Check if sanitized input is a valid UUIDv4
    try:
        uuid_obj = uuid.UUID(input_string, version=4)
        if str(uuid_obj).lower() == input_string.lower():
            # Input is a valid UUIDv4, return True with input
            return True, input_string
    except ValueError:
        pass

    sanitized_input = input_string.replace("-", "")
    # If not a valid UUIDv4, check if sanitized input is 32 characters and alphanumeric
    if len(sanitized_input) == 32 and re.match(r"^[a-fA-F0-9]+$", sanitized_input):
        # Format it into UUIDv4 style
        formatted_uuid = f"{sanitized_input[:8]}-{sanitized_input[8:12]}-{sanitized_input[12:16]}-{sanitized_input[16:20]}-{sanitized_input[20:]}"
        return True, formatted_uuid.lower()

    # If neither condition is met, return False and empty string
    return False, ""


def sanitize_string_input(input_string):
    # List of potentially dangerous characters or patterns to remove
    dangerous_characters = [
        "'",  # Single quote, used for escaping
        '"',  # Double quote
        ";",  # Semicolon, used to end SQL statements
        "--",  # Comment in SQL
        "#",  # Comment in MySQL
        "\\",  # Backslash, used for escaping
        "`",  # Backtick, often used in SQL identifiers
    ]

    # Replace each dangerous character with an empty string
    sanitized_string = input_string
    for char in dangerous_characters:
        sanitized_string = sanitized_string.replace(char, "")

    # Remove any SQL keywords that might indicate injection attempts
    sanitized_string = re.sub(
        r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|FROM|WHERE|JOIN|DATABASE)\b",
        "",
        sanitized_string,
        flags=re.IGNORECASE,
    )

    return sanitized_string


def sanitize_email_input(input_email):
    # Trim whitespace from both ends
    input_email = input_email.strip()

    # Convert to lowercase for uniformity
    input_email = input_email.lower()

    # Remove any special characters that should not be in an input_email
    input_email = re.sub(r"[^\w.%+-@]", "", input_email)

    # Step 4: Validate the sanitized email
    if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", input_email):
        return True, input_email
    else:
        return False, ""


def sanitize_pagenumber_input(input_number):
    if input_number > MAX_PAGENUMBER:
        return MAX_PAGENUMBER
    if input_number < MIN_PAGENUMBER:
        return MIN_PAGENUMBER
    return input_number


def sanitize_gacha_input(input_gacha):
    valid, input_gacha["gacha_uuid"] = sanitize_uuid_input(input_gacha["gacha_uuid"])
    if not valid:
        return False
    input_gacha["name"] = sanitize_string_input(input_gacha["name"])

    return input_gacha


def sanitize_pool_input(input_pool):
    try:
        input_pool["public_name"] = sanitize_string_input(input_pool["public_name"])

        if (
            not isinstance(input_pool["probability_common"], float)
            or not isinstance(input_pool["probability_rare"], float)
            or not isinstance(input_pool["probability_epic"], float)
            or not isinstance(input_pool["probability_legendary"], float)
        ):
            return False

        # check if sum of probabilities is 1
        if (
            input_pool["probability_legendary"]
            + input_pool["probability_epic"]
            + input_pool["probability_rare"]
            + input_pool["probability_common"]
        ) != 1:
            return False

        if input_pool["price"] < 1:
            return False

        for i in range(len(input_pool["items"])):
            valid, input_pool["items"][i] = sanitize_uuid_input(input_pool["items"][i])
            if not valid:
                return False

        return input_pool
    except Exception as e:
        return False


def sanitize_auction_input(input_auction):
    try:
        valid, input_auction["auction_uuid"] = sanitize_uuid_input(input_auction["auction_uuid"])
        if not valid:
            return False

        valid, input_auction["inventory_item_id"] = sanitize_uuid_input(input_auction["inventory_item_id"])
        if not valid:
            return False

        if input_auction["current_bidder"]:
            valid, input_auction["current_bidder"] = sanitize_uuid_input(input_auction["current_bidder"])
            if not valid:
                return False
            if input_auction["current_bid"] < input_auction["starting_price"]:
                return False
        else:
            input_auction["current_bid"] = 0

        input_auction["end_time"] = input_auction["end_time"].replace(tzinfo=None)

        if input_auction["end_time"] < datetime.now() and input_auction["status"] != "closed":
            return False

        if input_auction["end_time"] > datetime.now() and input_auction["status"] != "open":
            return False

        if input_auction["starting_price"] < 0 or input_auction["current_bid"] < 0:
            return False

        input_auction["end_time"] = str(input_auction["end_time"])

        input_auction["inventory_item_owner_id"] = ""

        return input_auction

    except Exception as e:
        print(e)
        return False


def sanitize_team_input(input_team):
    try:
        for item in input_team:
            valid, item = sanitize_uuid_input(item)
            if not valid:
                return False

        if len(input_team) != 7:
            return False

    except Exception as e:
        return False

    return input_team
