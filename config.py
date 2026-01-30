import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    # API Keys
    NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', '')
    GNEWS_API_KEY = os.getenv('GNEWS_API_KEY', '')
    WEATHERAPI_KEY = os.getenv('WEATHERAPI_KEY', '')
    
    # Ollama
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'geotrade.db')
    
    # News API Endpoints
    NEWSAPI_URL = 'https://newsapi.org/v2/everything'
    GNEWS_URL = 'https://gnews.io/api/v4/search'
    WEATHERAPI_URL = 'https://api.weatherapi.com/v1/current.json'
    WEATHERAPI_FORECAST_URL = 'https://api.weatherapi.com/v1/forecast.json'

    
    # Severity Thresholds
    SEVERITY_LOW = 3
    SEVERITY_MEDIUM = 6
    SEVERITY_HIGH = 8
    
    # Pagination
    NEWS_PER_PAGE = 10
    MAX_NEWS_RESULTS = 50
