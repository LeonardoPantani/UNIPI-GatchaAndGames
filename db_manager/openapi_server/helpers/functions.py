STAND_ATTRIBUTES = ['power', 'speed', 'durability', 'precision', 'range', 'potential']

LETTERS_MAP = {
    'A': 5,
    'B': 4,
    'C': 3,
    'D': 2,
    'E': 1
}


def stats_letter_to_number(gacha_attributes):
    letters_map = {
        'A': 5,
        'B': 4,
        'C': 3,
        'D': 2,
        'E': 1
    }
    
    converted = {}
    for attr in STAND_ATTRIBUTES:
        letter = gacha_attributes.get(attr)
        converted[attr] = letters_map.get(letter)
    return converted


def stats_number_to_letter(gacha_attributes):
    numbers_map = {value: key for key, value in LETTERS_MAP.items()}
    converted = {}
    for attr in STAND_ATTRIBUTES:
        number = gacha_attributes.get(attr)
        converted[attr] = numbers_map.get(number)
    return converted