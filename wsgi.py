# wsgi.py
from app import app

# This is what WSGI servers like Gunicorn will look for
if __name__ == "__main__":
    app.run()