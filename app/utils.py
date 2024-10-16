import re

def email_check(email):
    if(re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email)):
        return True
    else:
        return False

def username_check(username):
    if re.fullmatch(r'[A-Za-z0-9_]+', username):
        return True
    else:
        return False