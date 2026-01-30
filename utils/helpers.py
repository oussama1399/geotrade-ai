"""
Helper utility functions for GeoTrade AI
"""
from datetime import datetime, timedelta
import re
import json

def format_date(date_str):
    """Format date string to readable format"""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return date_str

def get_date_range(days_back=7):
    """Get date range for news queries"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text.strip()

def truncate_text(text, max_length=500):
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def parse_json_response(response_text):
    """Parse JSON from LLM response, handling markdown code blocks"""
    try:
        # Try direct JSON parse
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Try to find JSON object in text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        raise ValueError("Could not parse JSON from response")

def get_severity_color(score):
    """Get color code based on severity score"""
    if score <= 3:
        return 'success'  # Green
    elif score <= 6:
        return 'warning'  # Yellow
    elif score <= 8:
        return 'orange'   # Orange
    else:
        return 'danger'   # Red

def get_severity_label(score):
    """Get label based on severity score"""
    if score <= 3:
        return 'Low Risk'
    elif score <= 6:
        return 'Medium Risk'
    elif score <= 8:
        return 'High Risk'
    else:
        return 'Critical Risk'

def deduplicate_news(articles):
    """Remove duplicate news articles based on title similarity"""
    seen_titles = set()
    unique_articles = []
    
    for article in articles:
        title = article.get('title', '').lower()
        # Simple deduplication based on title
        title_key = re.sub(r'[^\w\s]', '', title)[:50]
        
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)
    
    return unique_articles

def build_search_query(product, country):
    """Build optimized search query for news APIs"""
    # Combine product and country with relevant keywords
    keywords = [
        f'"{product}" "{country}"',
        f'{product} import {country}',
        f'{country} trade {product}',
        f'{country} export {product}'
    ]
    return ' OR '.join(keywords)
