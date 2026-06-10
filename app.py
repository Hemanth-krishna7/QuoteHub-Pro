import math
import datetime
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import database
from api_client import QuoteAPIClient
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database tables on startup
logger.info("Initializing database schema...")
database.init_db()

@app.context_processor
def inject_now():
    """Injects current time into template context for footer/headers."""
    return {'now': datetime.datetime.utcnow()}

# --- VIEW ROUTES ---

@app.route('/')
def index():
    """Main dashboard page displaying the Daily Quote and Quote Generator."""
    today_str = datetime.date.today().isoformat()
    
    # 1. Fetch or generate the Daily Quote
    daily_quote = database.get_daily_quote(today_str)
    if not daily_quote:
        api_daily = QuoteAPIClient.fetch_daily_quote()
        # Insert quote into main table
        quote_id = database.insert_quote(api_daily['text'], api_daily['author'])
        # Map as today's daily quote
        database.set_daily_quote(today_str, quote_id)
        # Log activity
        database.log_activity("daily_fetch", f"Fetched new Daily Quote of the Day: \"{api_daily['text'][:20]}...\"")
        daily_quote = database.get_daily_quote(today_str)
        
    # 2. Fetch the active/latest random quote from history (so generator card isn't empty on load)
    # If no quotes exist, fetch one and insert it
    history_count = database.get_history_count()
    if history_count == 0:
        api_rand = QuoteAPIClient.fetch_random_quote()
        rand_id = database.insert_quote(api_rand['text'], api_rand['author'])
        database.log_activity("generate", f"Generated initial random quote: \"{api_rand['text'][:20]}...\"")
        
    latest_quotes = database.get_quote_history(1, 1)
    active_quote = latest_quotes[0] if latest_quotes else None
    
    # 3. Get collections for the collections quick-add dropdown
    collections = database.get_collections()
    
    return render_template(
        'index.html',
        daily_quote=daily_quote,
        active_quote=active_quote,
        collections=collections
    )

@app.route('/history')
def history():
    """Paginated quote generation history with search."""
    search_query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    total_count = database.get_history_count(search_query)
    total_pages = math.ceil(total_count / per_page)
    # Ensure page boundary
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
        
    quotes = database.get_quote_history(page, per_page, search_query)
    collections = database.get_collections()
    
    return render_template(
        'history.html',
        quotes=quotes,
        current_page=page,
        total_pages=total_pages,
        search_query=search_query,
        collections=collections
    )

@app.route('/favorites')
def favorites():
    """User favorited quotes list with search."""
    search_query = request.args.get('q', '').strip()
    quotes = database.get_favorites(search_query)
    collections = database.get_collections()
    
    return render_template(
        'favorites.html',
        quotes=quotes,
        search_query=search_query,
        collections=collections
    )

@app.route('/collections')
def collections():
    """Collections management page."""
    collections_list = database.get_collections()
    return render_template('collections.html', collections=collections_list)

@app.route('/collections/<int:collection_id>')
def collection_detail(collection_id):
    """View and search quotes within a specific collection."""
    collection = database.get_collection(collection_id)
    if not collection:
        flash("Collection not found.", "danger")
        return redirect(url_for('collections'))
        
    search_query = request.args.get('q', '').strip()
    quotes = database.get_collection_quotes(collection_id, search_query)
    all_collections = database.get_collections()
    
    return render_template(
        'collection_detail.html',
        collection=collection,
        quotes=quotes,
        search_query=search_query,
        collections=all_collections
    )

@app.route('/stats')
def stats():
    """Dashboard showing analytics, charts, and activity log."""
    statistics = database.get_statistics()
    recent_activities = database.get_recent_activities(15)
    return render_template(
        'stats.html',
        stats=statistics,
        activities=recent_activities
    )


# --- JSON API ENDPOINTS (FOR AJAX CONTROLS) ---

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """
    Asynchronously fetches a random quote, saves it,
    and returns details along with favorite status.
    """
    try:
        quote_data = QuoteAPIClient.fetch_random_quote()
        quote_id = database.insert_quote(quote_data['text'], quote_data['author'])
        database.log_activity("generate", f"Generated random quote: \"{quote_data['text'][:20]}...\"")
        
        # Check if it was already favorited in the past
        is_fav = database.is_favorite(quote_id)
        
        return jsonify({
            "status": "success",
            "quote": {
                "id": quote_id,
                "text": quote_data['text'],
                "author": quote_data['author'],
                "is_favorite": is_fav
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/favorite/<int:quote_id>', methods=['POST'])
def api_favorite(quote_id):
    """Asynchronously toggles favorite status for a quote."""
    try:
        action = database.toggle_favorite(quote_id)
        if not action:
            return jsonify({"status": "error", "message": "Quote not found"}), 404
            
        return jsonify({
            "status": "success",
            "action": action
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/collections', methods=['POST'])
def api_create_collection():
    """Creates a custom collection."""
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({"status": "error", "message": "Collection name is required"}), 400
            
        collection_id = database.create_collection(name, description)
        return jsonify({
            "status": "success",
            "collection": {
                "id": collection_id,
                "name": name,
                "description": description
            }
        })
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "A collection with this name already exists."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/collections/<int:collection_id>', methods=['DELETE'])
def api_delete_collection(collection_id):
    """Deletes a custom collection."""
    try:
        success = database.delete_collection(collection_id)
        if success:
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Collection not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/collections/<int:collection_id>/add', methods=['POST'])
def api_add_to_collection(collection_id):
    """Adds a quote to a collection."""
    try:
        data = request.get_json() or {}
        quote_id = data.get('quote_id')
        
        if not quote_id:
            return jsonify({"status": "error", "message": "Quote ID is required"}), 400
            
        success, msg = database.add_quote_to_collection(collection_id, quote_id)
        if success:
            return jsonify({"status": "success", "message": msg})
        return jsonify({"status": "error", "message": msg}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/collections/<int:collection_id>/remove/<int:quote_id>', methods=['POST'])
def api_remove_from_collection(collection_id, quote_id):
    """Removes a quote from a collection."""
    try:
        success = database.remove_quote_from_collection(collection_id, quote_id)
        if success:
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Association not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Bind to PORT if provided by environment (e.g. Render)
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
