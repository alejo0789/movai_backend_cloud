# wsgi.py
# Import create_app from the root app.py file, not from the app package
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # This imports from app.py in root directory

app = create_app()

if __name__ == "__main__":
    app.run()