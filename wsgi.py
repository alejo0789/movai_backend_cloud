# wsgi.py
# Import create_app from the root app.py file, not from the app package
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app.py module directly to avoid confusion with app package
import importlib.util
spec = importlib.util.spec_from_file_location("app_module", os.path.join(os.path.dirname(__file__), "app.py"))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

app = app_module.create_app()

if __name__ == "__main__":
    app.run()