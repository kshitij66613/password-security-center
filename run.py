"""Development entry point.

Run with ``python run.py``. Debug mode follows the selected configuration
(FLASK_ENV=development by default). Never run the debug server in production;
use a WSGI server such as gunicorn or waitress instead.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
