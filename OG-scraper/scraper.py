from flask import Flask, request, jsonify
from recipe_scrapers import scrape_html
from flask_cors import CORS
from recipe_scrapers._exceptions import (
    ElementNotFoundInHtml,
    FieldNotProvidedByWebsiteException,
    FillPluginException,
    NoSchemaFoundInWildMode,
    OpenGraphException,
    RecipeSchemaNotFound,
    SchemaOrgException,
    StaticValueException,
    WebsiteNotImplementedError
)
import sys
import os
import uuid
import re
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, Optional, Tuple

# Add parent directory to path to import error_logger
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from error_logger import get_error_logger

app = Flask(__name__)
CORS(app, origins='*')
error_logger = get_error_logger()


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate URL format.
    
    Args:
        url: URL string to validate
        
    Returns:
        Tuple: (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"
    
    url = url.strip()
    
    # Basic URL pattern check
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        return False, "Invalid URL format. Must start with http:// or https://"
    
    # Check for valid domain
    try:
        result = urlparse(url)
        if not result.netloc:
            return False, "URL must contain a valid domain"
    except Exception as e:
        return False, f"URL validation error: {str(e)}"
    
    return True, None


def is_recipe_valid(recipe: Dict) -> Tuple[bool, Optional[Dict]]:
    """
    Validate scraped recipe for completeness.
    
    Checks:
    1. Recipe must have non-empty ingredients array
    2. Recipe must have non-empty title
    3. No scraper-level error
    
    Args:
        recipe: Recipe dictionary from scraper
        
    Returns:
        Tuple: (is_valid, error_response_dict_if_invalid)
    """
    # Check for scraper-level error
    if recipe.get("error"):
        return False, None  # Will handle separately
    
    # Check for empty ingredients
    ingredients = recipe.get("ingredients", [])
    if not ingredients or len(ingredients) == 0:
        return False, None  # Will handle separately
    
    # Check for empty title
    title = recipe.get("title", "").strip()
    if not title:
        return False, None  # Will handle separately
    
    return True, None


def create_recipe_response(recipe: Dict) -> Dict:
    """
    Create successful recipe response.
    
    Args:
        recipe: Scraped recipe dictionary
        
    Returns:
        Recipe response with recipe_id set to None (to be assigned by /assign-recipe-id)
    """
    return {
        "error": False,
        "error_id": None,
        "recipe_id": None,  # Not assigned yet; requires /assign-recipe-id endpoint
        "timestamp": datetime.now().isoformat(),
        "source_url": recipe.get("url"),
        "recipe": recipe
    }

error_logger = get_error_logger()

def safe_scrape(scraper, func, default=""):
    try:
        result = func()
        return result if result is not None else default
    except (
        ElementNotFoundInHtml,
        FieldNotProvidedByWebsiteException,
        FillPluginException,
        NoSchemaFoundInWildMode,
        OpenGraphException,
        RecipeSchemaNotFound,
        SchemaOrgException,
        StaticValueException,
        WebsiteNotImplementedError,
        AttributeError,
        NotImplementedError
    ):
        return default

def scrape_single_recipe(url: str, timeout: int = 30) -> Tuple[Dict, Optional[str], Optional[str]]:
    """
    Scrape a single recipe from URL.
    
    Args:
        url: Recipe URL
        timeout: Request timeout in seconds (default 30)
        
    Returns:
        Tuple: (recipe_dict, error_type, error_message)
        - If successful: (recipe_dict, None, None)
        - If error: (None, error_type, error_message)
    """
    try:
        # Add timeout to scrape request
        import socket
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        
        try:
            scraper = scrape_html(html=None, org_url=url, online=True, supported_only=True)
        finally:
            socket.setdefaulttimeout(original_timeout)

        recipe_response = {
            "author": str(safe_scrape(scraper, scraper.author)),
            "canonical_url": str(safe_scrape(scraper, scraper.canonical_url)),
            "category": str(safe_scrape(scraper, scraper.category)),
            "cook_time": str(safe_scrape(scraper, scraper.cook_time)),
            "cooking_method": str(safe_scrape(scraper, scraper.cooking_method)),
            "cuisine": str(safe_scrape(scraper, scraper.cuisine)),
            "description": str(safe_scrape(scraper, scraper.description)),
            "dietary_restrictions": str(safe_scrape(scraper, scraper.dietary_restrictions)),
            "host": str(safe_scrape(scraper, scraper.host)),
            "image": str(safe_scrape(scraper, scraper.image)),
            "ingredients": safe_scrape(scraper, scraper.ingredients, default=[]),
            "instructions_list": safe_scrape(scraper, scraper.instructions_list, default=[]),
            "keywords": safe_scrape(scraper, scraper.keywords, default=[]),
            "language": safe_scrape(scraper, scraper.language),
            "nutrients": safe_scrape(scraper, scraper.nutrients, default={}),
            "prep_time": str(safe_scrape(scraper, scraper.prep_time)),
            "ratings": str(safe_scrape(scraper, scraper.ratings)),
            "ratings_count": str(safe_scrape(scraper, scraper.ratings_count)),
            "reviews": safe_scrape(scraper, scraper.reviews, default=[]),
            "site_name": str(safe_scrape(scraper, scraper.site_name)),
            "title": str(safe_scrape(scraper, scraper.title)),
            "total_time": str(safe_scrape(scraper, scraper.total_time)),
            "yields": str(safe_scrape(scraper, scraper.yields)),
            "url": url,
            "error": None
        }
        
        return recipe_response, None, None
        
    except socket.timeout:
        return None, "timeout", f"Request to {url} timed out after {timeout} seconds"
    except ConnectionError as e:
        return None, "connection_error", f"Connection error while scraping {url}: {str(e)}"
    except Exception as e:
        return None, "scraper_error", f"Scraper error: {str(e)}"



# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/status', methods=['GET'])
def status():
    """
    Health check endpoint.
    
    Returns:
        - status: "ok"
        - recent_errors: List of last 5 errors
        - error_stats: Error counts by type
    """
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "recent_errors": error_logger.get_recent_errors(limit=5),
        "error_stats": error_logger.get_error_stats()
    }), 200


@app.route('/scrape', methods=['POST'])
def scrape():
    """
    Scrape a recipe from URL with validation.
    
    Request body:
    {
        "url": "https://example.com/recipe",
        "timeout": 30  (optional, default 30)
    }
    
    Returns on success (200):
    {
        "error": false,
        "error_id": null,
        "recipe_id": null,
        "timestamp": "2026-03-16T...",
        "source_url": "https://...",
        "recipe": { ...full recipe object... }
    }
    
    Returns on validation error (400):
    {
        "error": true,
        "error_id": "err_1710603000_a3f2c1",
        "error_type": "validation_error",
        "error_message": "...",
        "timestamp": "2026-03-16T..."
    }
    
    Returns on scraper error (500):
    {
        "error": true,
        "error_id": "err_1710603000_b4g3d2",
        "error_type": "empty_ingredients|scraper_error|connection_error|timeout",
        "error_message": "...",
        "timestamp": "2026-03-16T...",
        "source_url": "https://..."
    }
    """
    try:
        # Parse request
        data = request.get_json()
        if not data:
            error_resp = error_logger.get_error_response(
                error_type="validation_error",
                error_message="Request body must be valid JSON"
            )
            return jsonify(error_resp), 400
        
        url = data.get('url', '').strip()
        timeout = data.get('timeout', 30)
        
        # Validate URL
        is_valid, error_msg = validate_url(url)
        if not is_valid:
            error_resp = error_logger.get_error_response(
                error_type="validation_error",
                error_message=error_msg,
                source_url=url
            )
            return jsonify(error_resp), 400
        
        # Scrape recipe with timeout
        recipe, error_type, error_message = scrape_single_recipe(url, timeout=timeout)
        
        # Check for scraper-level errors
        if error_type:
            error_resp = error_logger.get_error_response(
                error_type=error_type,
                error_message=error_message,
                source_url=url
            )
            return jsonify(error_resp), 500
        
        # Validate recipe (check for empty ingredients, errors, etc.)
        is_valid, _ = is_recipe_valid(recipe)
        if not is_valid:
            # Determine specific error reason
            if recipe.get("error"):
                error_type = "scraper_error"
                error_message = f"Recipe scraper error: {recipe.get('error')}"
            elif not recipe.get("ingredients") or len(recipe.get("ingredients", [])) == 0:
                error_type = "empty_ingredients"
                error_message = "Recipe has no ingredients"
            elif not recipe.get("title", "").strip():
                error_type = "validation_error"
                error_message = "Recipe has no title"
            else:
                error_type = "validation_error"
                error_message = "Recipe failed validation"
            
            error_resp = error_logger.get_error_response(
                error_type=error_type,
                error_message=error_message,
                source_url=url
            )
            return jsonify(error_resp), 400
        
        # Success: return recipe without recipe_id (requires /assign-recipe-id)
        response = create_recipe_response(recipe)
        return jsonify(response), 200
        
    except Exception as e:
        # Unexpected error
        error_resp = error_logger.get_error_response(
            error_type="scraper_error",
            error_message=f"Unexpected error: {str(e)}",
            source_url=url if 'url' in locals() else None,
            stacktrace=str(e)
        )
        return jsonify(error_resp), 500


@app.route('/assign-recipe-id', methods=['POST'])
def assign_recipe_id():
    """
    Assign a unique recipe_id to a validated recipe.
    
    This endpoint is called AFTER /scrape succeeds.
    It generates a UUID-based recipe_id and appends it to the recipe JSON.
    
    Request body:
    {
        "recipe_json": { recipe object from /scrape },
        "recipe_url": "https://example.com/recipe"  (optional)
    }
    
    Returns on success (200):
    {
        "error": false,
        "recipe_id": "rec_a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5o6",
        "recipe_json_with_id": {
            ...recipe object with "id": "rec_..."...
        }
    }
    
    Returns on validation error (400):
    {
        "error": true,
        "error_message": "...",
        "recipe_id": null
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": True,
                "error_message": "Request body must be valid JSON",
                "recipe_id": None
            }), 400
        
        recipe_json = data.get('recipe_json')
        recipe_url = data.get('recipe_url')
        
        # Validate recipe_json
        if not recipe_json or not isinstance(recipe_json, dict):
            return jsonify({
                "error": True,
                "error_message": "recipe_json must be a non-empty dictionary",
                "recipe_id": None
            }), 400
        
        if not recipe_json.get("url"):
            return jsonify({
                "error": True,
                "error_message": "recipe_json must contain 'url' field",
                "recipe_id": None
            }), 400
        
        # Generate recipe_id (UUID format: rec_[uuid])
        recipe_id = f"rec_{uuid.uuid4()}"
        
        # Create recipe JSON with ID
        recipe_with_id = recipe_json.copy()
        recipe_with_id["id"] = recipe_id
        
        return jsonify({
            "error": False,
            "recipe_id": recipe_id,
            "recipe_json_with_id": recipe_with_id,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": True,
            "error_message": f"Unexpected error: {str(e)}",
            "recipe_id": None
        }), 500


@app.route('/scrape-recipe', methods=['POST'])
def scrape_recipe():
    """
    Deprecated: Use /scrape instead.
    
    Maintained for backward compatibility.
    """
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({"error": "No URL provided"}), 400

        recipe, error_type, error_message = scrape_single_recipe(url)
        
        if error_type:
            return jsonify({
                "error": error_message,
                "url": url
            }), 500
        
        return jsonify(recipe), 200 if not recipe.get("error") else 500

    except Exception as e:
        return jsonify({
            "error": str(e),
            "url": url if 'url' in locals() else None
        }), 500


@app.route('/bulk-scrape', methods=['POST'])
def bulk_scrape():
    """
    Bulk scrape multiple recipes (deprecated endpoint).
    
    Maintained for backward compatibility.
    Use /scrape with loop in client code instead.
    """
    try:
        data = request.get_json()
        urls = data.get('urls', [])

        if not urls or not isinstance(urls, list):
            return jsonify({"error": "No URLs array provided"}), 400

        results = []
        for url in urls:
            if url:
                recipe, error_type, error_message = scrape_single_recipe(url)
                if error_type:
                    results.append({
                        "error": error_message,
                        "url": url
                    })
                else:
                    results.append(recipe)

        return jsonify({"results": results}), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
            "results": []
        }), 500


if __name__ == "__main__":
    app.run(debug=True)