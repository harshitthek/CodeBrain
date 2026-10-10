import os
import sys
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        # Get port number from environment variable, default is 8001
        port = '8000'
        execute_from_command_line(["manage.py", "runserver", port])
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        sys.exit(1)