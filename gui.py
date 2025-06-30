import webview
from app import app
import threading
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    # We need to change the template and static folder paths to be absolute
    # for PyInstaller to find them.
    app.template_folder = resource_path('templates')
    
    # Start the Flask server in a separate thread
    flask_thread = threading.Thread(target=lambda: app.run(host='127.0.0.1', port=5000))
    flask_thread.daemon = True
    flask_thread.start()

    # Create a webview window that displays the Flask app
    webview.create_window(
        'Meeting Protokoll Generator',
        'http://127.0.0.1:5000',
        width=1200,
        height=800
    )
    
    # Start the webview event loop
    webview.start()
