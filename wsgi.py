# wsgi.py
from app import create_app

# Gunicorn needs a callable named 'app'
# It will use this to start your Flask application
app = create_app()