import os

ENVIRONMENT = bool(os.environ.get('ENVIRONMENT', False))

if ENVIRONMENT:
    try:
        API_ID = int(os.environ.get('API_ID', 0))
    except ValueError:
        raise Exception("Your API_ID is not a valid integer.")
    API_HASH = os.environ.get('API_HASH', None)
    BOT_TOKEN = os.environ.get('BOT_TOKEN', None)
else:
    # Fill the Values
    API_ID = 32302646
    API_HASH = "fdcf1fccc9b479190960094b7e9953af"
    BOT_TOKEN = "8379457890:AAFGcAlrYnk26yrbFpQj3MhkbQv-AhzIGoc"
