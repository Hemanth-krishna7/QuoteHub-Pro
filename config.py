import os

class Config:
    # Secret key for Flask sessions/cookies
    SECRET_KEY = os.environ.get('SECRET_KEY', 'quotehub-secret-dev-key-1293847')
    
    # Path to SQLite database file
    # On Render, this can be set to a persistent disk mount like /var/data/quotes.db
    DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'quotes.db'))
    
    # Ensure directory for database exists (crucial for persistent mounts)
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
