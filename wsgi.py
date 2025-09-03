# wsgi.py
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the create_app function from your existing app.py file
# We need to be explicit to avoid conflicts with the app/ directory
import importlib.util

# Load app.py specifically as a module
spec = importlib.util.spec_from_file_location("main_app", "app.py")
main_app = importlib.util.module_from_spec(spec)
sys.modules["main_app"] = main_app
spec.loader.exec_module(main_app)

# Create the Flask app using your existing create_app function
app = main_app.create_app()

if __name__ == "__main__":
    app.run()