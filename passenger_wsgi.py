import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.app import app as application  # Fixed import path

if __name__ == "__main__":
    application.run()