import requests
import random
import logging

logger = logging.getLogger(__name__)

FALLBACK_QUOTES = [
    {"q": "The only limit to our realization of tomorrow is our doubts of today.", "a": "Franklin D. Roosevelt"},
    {"q": "Do not go where the path may lead, go instead where there is no path and leave a trail.", "a": "Ralph Waldo Emerson"},
    {"q": "It is during our darkest moments that we must focus to see the light.", "a": "Aristotle"},
    {"q": "Life is what happens when you're busy making other plans.", "a": "John Lennon"},
    {"q": "The future belongs to those who believe in the beauty of their dreams.", "a": "Eleanor Roosevelt"},
    {"q": "In the end, it's not the years in your life that count. It's the life in your years.", "a": "Abraham Lincoln"},
    {"q": "The greatest glory in living lies not in never falling, but in rising every time we fall.", "a": "Nelson Mandela"},
    {"q": "The way to get started is to quit talking and begin doing.", "a": "Walt Disney"},
    {"q": "If life were predictable it would cease to be life, and be without flavor.", "a": "Eleanor Roosevelt"},
    {"q": "Spread love everywhere you go. Let no one ever come to you without leaving happier.", "a": "Mother Teresa"},
    {"q": "Tell me and I forget. Teach me and I remember. Involve me and I learn.", "a": "Benjamin Franklin"},
    {"q": "The best way to predict the future is to create it.", "a": "Peter Drucker"},
    {"q": "It always seems impossible until it's done.", "a": "Nelson Mandela"},
    {"q": "Keep your face always toward the sunshine—and shadows will fall behind you.", "a": "Walt Whitman"},
    {"q": "Success is not final, failure is not fatal: it is the courage to continue that counts.", "a": "Winston Churchill"},
    {"q": "You miss 100% of the shots you don't take.", "a": "Wayne Gretzky"},
    {"q": "Whether you think you can or you think you can't, you're right.", "a": "Henry Ford"},
    {"q": "I have not failed. I've just found 10,000 ways that won't work.", "a": "Thomas A. Edison"},
    {"q": "A person who never made a mistake never tried anything new.", "a": "Albert Einstein"},
    {"q": "Believe you can and you're halfway there.", "a": "Theodore Roosevelt"}
]

class QuoteAPIClient:
    """Client for retrieving quotes from external APIs with built-in fallbacks."""

    @staticmethod
    def _is_rate_limited(quote_text, author):
        """Checks if the API response is actually a rate limit message."""
        if author == "ZenQuotes.io" and "too many requests" in quote_text.lower():
            return True
        return False

    @classmethod
    def fetch_random_quote(cls):
        """
        Fetches a random quote from ZenQuotes.
        Falls back to a curated local list on error or rate-limiting.
        """
        try:
            # ZenQuotes random endpoint
            response = requests.get("https://zenquotes.io/api/random", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    text = data[0].get("q", "")
                    author = data[0].get("a", "Unknown")
                    
                    if not cls._is_rate_limited(text, author) and text:
                        return {"text": text, "author": author, "source": "ZenQuotes API"}
        except Exception as e:
            # Log error internally and trigger fallback
            logger.error("ZenQuotes API Random request failed: %s", e)
            
        # Fallback to local curated quotes
        fallback = random.choice(FALLBACK_QUOTES)
        return {"text": fallback["q"], "author": fallback["a"], "source": "Local Fallback"}

    @classmethod
    def fetch_daily_quote(cls):
        """
        Fetches the Quote of the Day from ZenQuotes.
        Falls back to a curated local list on error or rate-limiting.
        """
        try:
            # ZenQuotes today endpoint
            response = requests.get("https://zenquotes.io/api/today", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    text = data[0].get("q", "")
                    author = data[0].get("a", "Unknown")
                    
                    if not cls._is_rate_limited(text, author) and text:
                        return {"text": text, "author": author, "source": "ZenQuotes Daily API"}
        except Exception as e:
            logger.error("ZenQuotes API Daily request failed: %s", e)
            
        # Fallback to local curated quotes (hashed by today's date day for stability)
        import datetime
        day_of_year = datetime.datetime.now().timetuple().tm_yday
        fallback = FALLBACK_QUOTES[day_of_year % len(FALLBACK_QUOTES)]
        return {"text": fallback["q"], "author": fallback["a"], "source": "Local Fallback (Daily)"}
