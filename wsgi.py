# wsgi.py
import os
import sys

# Add the current directory to the Python path
# This is usually not needed on Railway, but it's good practice
# for local testing.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app instance directly from your app.py file
from app import create_app

# The Gunicorn callable. It must be named 'app'
# as per your Procfile, which is `wsgi:app`.
app = create_app()