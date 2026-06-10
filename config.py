import os

class Config:
    # Secret key for Flask sessions/cookies
    SECRET_KEY = os.environ.get(
        'SECRET_KEY',
        'quotehub-secret-dev-key-1293847'
    )

    # Local SQLite database path
    DB_PATH = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'quotes.db'
    )