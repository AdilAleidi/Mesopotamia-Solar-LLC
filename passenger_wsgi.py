# /passenger_wsgi.py
import os
import sys

# Virtualenv activation
VENV_PATH = os.path.expanduser("~/venv/bin/python")
if sys.executable != VENV_PATH:
    os.execl(VENV_PATH, VENV_PATH, *sys.argv)

# Path configuration
sys.path.insert(0, os.path.dirname(__file__))

# Import the application factory
from app import create_app

# Create application instance
application = create_app()