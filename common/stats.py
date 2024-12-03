def map_grade_to_number(grade):
    grade = grade.upper()
    mapping = {
        'A': 5,
        'B': 4,
        'C': 3,
        'D': 2,
        'E': 1
    }
    return mapping.get(grade, None)  # Returns None if grade is not found


def map_number_to_grade(number):
    reverse_mapping = {
        5: 'A',
        4: 'B',
        3: 'C',
        2: 'D',
        1: 'E'
    }
    return reverse_mapping.get(number, None)  # Returns None if number is not found