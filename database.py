import sqlite3
import logging
from config import Config

logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes connection to the SQLite database with Row factory."""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes the database schema if it doesn't already exist."""
    conn = get_db_connection()
    try:
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()

# --- Activity Logging ---
def log_activity(activity_type, description):
    """Logs a user interaction activity to the database."""
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO activities (activity_type, description) VALUES (?, ?)",
            (activity_type, description)
        )
        conn.commit()
    except Exception as e:
        logger.error("Error logging activity: %s", e)
    finally:
        conn.close()

# --- Quote Operations ---
def insert_quote(quote_text, author):
    """
    Inserts a quote into the database.
    If the quote already exists (text + author unique combination),
    it updates the generated_at timestamp to the current time and returns the existing quote's ID.
    """
    conn = get_db_connection()
    try:
        # Check if quote already exists
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM quotes WHERE quote_text = ? AND author = ?",
            (quote_text.strip(), author.strip())
        )
        row = cursor.fetchone()
        
        if row:
            quote_id = row['id']
            # Update generated_at to put it at the top of history
            conn.execute(
                "UPDATE quotes SET generated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (quote_id,)
            )
            conn.commit()
            return quote_id
        
        # Otherwise insert new quote
        cursor.execute(
            "INSERT INTO quotes (quote_text, author) VALUES (?, ?)",
            (quote_text.strip(), author.strip())
        )
        quote_id = cursor.lastrowid
        conn.commit()
        return quote_id
    finally:
        conn.close()

# --- Favorite Operations ---
def toggle_favorite(quote_id):
    """
    Toggles a quote's favorite status.
    Returns 'added' if favorited, 'removed' if unfavorited.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Fetch quote text for activity description
        cursor.execute("SELECT quote_text, author FROM quotes WHERE id = ?", (quote_id,))
        quote = cursor.fetchone()
        if not quote:
            return None
        
        # Check if already favorited
        cursor.execute("SELECT id FROM favorites WHERE quote_id = ?", (quote_id,))
        fav = cursor.fetchone()
        
        short_text = f"\"{quote['quote_text'][:30]}...\" by {quote['author']}"
        
        if fav:
            # Remove from favorites
            conn.execute("DELETE FROM favorites WHERE quote_id = ?", (quote_id,))
            conn.commit()
            log_activity("unfavorite", f"Removed favorite: {short_text}")
            return "removed"
        else:
            # Add to favorites
            conn.execute("INSERT INTO favorites (quote_id) VALUES (?)", (quote_id,))
            conn.commit()
            log_activity("favorite", f"Favorited quote: {short_text}")
            return "added"
    finally:
        conn.close()

def is_favorite(quote_id):
    """Checks if a quote is currently favorited."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM favorites WHERE quote_id = ?", (quote_id,))
        return cursor.fetchone() is not None
    finally:
        conn.close()

# --- Daily Quote Operations ---
def get_daily_quote(date_str):
    """Retrieves the daily quote assigned to a specific date."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT q.*, (f.id IS NOT NULL) AS is_favorite
            FROM daily_quotes dq
            JOIN quotes q ON dq.quote_id = q.id
            LEFT JOIN favorites f ON q.id = f.quote_id
            WHERE dq.date = ?
            """,
            (date_str,)
        )
        return cursor.fetchone()
    finally:
        conn.close()

def set_daily_quote(date_str, quote_id):
    """Sets the daily quote mapping for a specific date."""
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO daily_quotes (date, quote_id) VALUES (?, ?)",
            (date_str, quote_id)
        )
        conn.commit()
    finally:
        conn.close()

# --- History Page Operations ---
def get_quote_history(page, per_page, search_query=""):
    """
    Returns a paginated list of generated quotes.
    Each item contains quote data and is_favorite flag.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        offset = (page - 1) * per_page
        
        if search_query:
            query_param = f"%{search_query}%"
            cursor.execute(
                """
                SELECT q.*, (f.id IS NOT NULL) AS is_favorite
                FROM quotes q
                LEFT JOIN favorites f ON q.id = f.quote_id
                WHERE q.quote_text LIKE ? OR q.author LIKE ?
                ORDER BY q.generated_at DESC
                LIMIT ? OFFSET ?
                """,
                (query_param, query_param, per_page, offset)
            )
        else:
            cursor.execute(
                """
                SELECT q.*, (f.id IS NOT NULL) AS is_favorite
                FROM quotes q
                LEFT JOIN favorites f ON q.id = f.quote_id
                ORDER BY q.generated_at DESC
                LIMIT ? OFFSET ?
                """,
                (per_page, offset)
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_history_count(search_query=""):
    """Returns the total number of history records matching a search query."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if search_query:
            query_param = f"%{search_query}%"
            cursor.execute(
                "SELECT COUNT(*) FROM quotes WHERE quote_text LIKE ? OR author LIKE ?",
                (query_param, query_param)
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM quotes")
        return cursor.fetchone()[0]
    finally:
        conn.close()

# --- Favorite Page Operations ---
def get_favorites(search_query=""):
    """Returns all favorited quotes, optionally filtered by search."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if search_query:
            query_param = f"%{search_query}%"
            cursor.execute(
                """
                SELECT q.*, 1 AS is_favorite
                FROM favorites f
                JOIN quotes q ON f.quote_id = q.id
                WHERE q.quote_text LIKE ? OR q.author LIKE ?
                ORDER BY f.added_at DESC
                """,
                (query_param, query_param)
            )
        else:
            cursor.execute(
                """
                SELECT q.*, 1 AS is_favorite
                FROM favorites f
                JOIN quotes q ON f.quote_id = q.id
                ORDER BY f.added_at DESC
                """
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

# --- Custom Collection Operations ---
def create_collection(name, description=""):
    """Creates a custom collection for quotes."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO collections (name, description) VALUES (?, ?)",
            (name.strip(), description.strip())
        )
        collection_id = cursor.lastrowid
        conn.commit()
        log_activity("collection_create", f"Created collection: \"{name.strip()}\"")
        return collection_id
    finally:
        conn.close()

def get_collections():
    """Gets all collections along with their quote count."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.*, COUNT(cq.quote_id) AS quote_count
            FROM collections c
            LEFT JOIN collection_quotes cq ON c.id = cq.collection_id
            GROUP BY c.id
            ORDER BY c.name ASC
            """
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_collection(collection_id):
    """Retrieves a single collection's info."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM collections WHERE id = ?", (collection_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def delete_collection(collection_id):
    """Deletes a collection (associated quotes removed via cascade)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM collections WHERE id = ?", (collection_id,))
        collection = cursor.fetchone()
        if collection:
            conn.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
            conn.commit()
            log_activity("collection_delete", f"Deleted collection: \"{collection['name']}\"")
            return True
        return False
    finally:
        conn.close()

def add_quote_to_collection(collection_id, quote_id):
    """Adds a quote to a custom collection."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Verify collection and quote exist
        cursor.execute("SELECT name FROM collections WHERE id = ?", (collection_id,))
        coll = cursor.fetchone()
        cursor.execute("SELECT quote_text, author FROM quotes WHERE id = ?", (quote_id,))
        q = cursor.fetchone()
        
        if not coll or not q:
            return False, "Collection or Quote does not exist"
        
        cursor.execute(
            "SELECT 1 FROM collection_quotes WHERE collection_id = ? AND quote_id = ?",
            (collection_id, quote_id)
        )
        if cursor.fetchone():
            return False, "Quote is already in this collection"
            
        conn.execute(
            "INSERT INTO collection_quotes (collection_id, quote_id) VALUES (?, ?)",
            (collection_id, quote_id)
        )
        conn.commit()
        
        short_text = f"\"{q['quote_text'][:20]}...\""
        log_activity("collection_add", f"Added {short_text} to \"{coll['name']}\"")
        return True, "Successfully added"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def remove_quote_from_collection(collection_id, quote_id):
    """Removes a quote association from a collection."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM collections WHERE id = ?", (collection_id,))
        coll = cursor.fetchone()
        cursor.execute("SELECT quote_text FROM quotes WHERE id = ?", (quote_id,))
        q = cursor.fetchone()
        
        if not coll or not q:
            return False
            
        conn.execute(
            "DELETE FROM collection_quotes WHERE collection_id = ? AND quote_id = ?",
            (collection_id, quote_id)
        )
        conn.commit()
        
        short_text = f"\"{q['quote_text'][:20]}...\""
        log_activity("collection_remove", f"Removed {short_text} from \"{coll['name']}\"")
        return True
    finally:
        conn.close()

def get_collection_quotes(collection_id, search_query=""):
    """Retrieves all quotes inside a collection with search filter."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if search_query:
            query_param = f"%{search_query}%"
            cursor.execute(
                """
                SELECT q.*, (f.id IS NOT NULL) AS is_favorite
                FROM collection_quotes cq
                JOIN quotes q ON cq.quote_id = q.id
                LEFT JOIN favorites f ON q.id = f.quote_id
                WHERE cq.collection_id = ? AND (q.quote_text LIKE ? OR q.author LIKE ?)
                ORDER BY cq.added_at DESC
                """,
                (collection_id, query_param, query_param)
            )
        else:
            cursor.execute(
                """
                SELECT q.*, (f.id IS NOT NULL) AS is_favorite
                FROM collection_quotes cq
                JOIN quotes q ON cq.quote_id = q.id
                LEFT JOIN favorites f ON q.id = f.quote_id
                WHERE cq.collection_id = ?
                ORDER BY cq.added_at DESC
                """,
                (collection_id,)
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_quote_collections(quote_id):
    """Retrieves all collections that a specific quote belongs to."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.*
            FROM collection_quotes cq
            JOIN collections c ON cq.collection_id = c.id
            WHERE cq.quote_id = ?
            ORDER BY c.name ASC
            """,
            (quote_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

# --- Activity Log Operations ---
def get_recent_activities(limit=10):
    """Retrieves the recent activity log for the dashboard feed."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM activities ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

# --- Statistics & Metrics ---
def get_statistics():
    """Calculates statistics for the dashboard metrics and charts."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # KPI calculations
        cursor.execute("SELECT COUNT(*) FROM quotes")
        total_quotes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM favorites")
        total_favorites = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM collections")
        total_collections = cursor.fetchone()[0]
        
        # Top Authors
        cursor.execute(
            """
            SELECT author, COUNT(*) AS count
            FROM quotes
            GROUP BY author
            ORDER BY count DESC, author ASC
            LIMIT 5
            """
        )
        top_authors = [dict(row) for row in cursor.fetchall()]
        
        # Quote discoveries past 7 days (for chart)
        cursor.execute(
            """
            SELECT DATE(generated_at) AS date_label, COUNT(*) AS count
            FROM quotes
            WHERE generated_at >= datetime('now', '-7 days')
            GROUP BY DATE(generated_at)
            ORDER BY date_label ASC
            """
        )
        history_chart = [dict(row) for row in cursor.fetchall()]
        
        # Collection distribution (quotes per collection)
        cursor.execute(
            """
            SELECT c.name, COUNT(cq.quote_id) AS count
            FROM collections c
            LEFT JOIN collection_quotes cq ON c.id = cq.collection_id
            GROUP BY c.id
            ORDER BY count DESC
            LIMIT 5
            """
        )
        collections_chart = [dict(row) for row in cursor.fetchall()]
        
        return {
            "total_quotes": total_quotes,
            "total_favorites": total_favorites,
            "total_collections": total_collections,
            "top_authors": top_authors,
            "history_chart": history_chart,
            "collections_chart": collections_chart
        }
    finally:
        conn.close()
