"""
News Aggregator Service
Fetches news from multiple sources (NewsAPI, GNews)
"""
import requests
from datetime import datetime, timedelta
from config import Config
from utils.helpers import get_date_range, clean_text, deduplicate_news, build_search_query

class NewsAggregator:
    def __init__(self):
        self.newsapi_key = Config.NEWSAPI_KEY
        self.gnews_key = Config.GNEWS_API_KEY
        
    def fetch_news(self, product, country, days_back=7):
        """
        Fetch news from multiple sources
        
        Args:
            product: Product being imported
            country: Source country
            days_back: Number of days to look back
            
        Returns:
            List of news articles
        """
        all_articles = []
        
        # Fetch from NewsAPI
        if self.newsapi_key:
            newsapi_articles = self._fetch_from_newsapi(product, country, days_back)
            all_articles.extend(newsapi_articles)
        
        # Fetch from GNews
        if self.gnews_key:
            gnews_articles = self._fetch_from_gnews(product, country, days_back)
            all_articles.extend(gnews_articles)
        
        # Deduplicate and normalize
        unique_articles = deduplicate_news(all_articles)
        
        # Sort by published date (newest first)
        unique_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        return unique_articles[:Config.MAX_NEWS_RESULTS]
    
    def _fetch_from_newsapi(self, product, country, days_back):
        """Fetch news from NewsAPI.org"""
        try:
            start_date, end_date = get_date_range(days_back)
            query = build_search_query(product, country)
            
            params = {
                'q': query,
                'from': start_date,
                'to': end_date,
                'language': 'en',
                'sortBy': 'relevancy',
                'apiKey': self.newsapi_key,
                'pageSize': 50
            }
            
            response = requests.get(Config.NEWSAPI_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for article in data.get('articles', []):
                articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'content': article.get('content', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'published_at': article.get('publishedAt', ''),
                    'image_url': article.get('urlToImage', ''),
                    'api_source': 'NewsAPI'
                })
            
            return articles
            
        except Exception as e:
            print(f"Error fetching from NewsAPI: {e}")
            return []
    
    def _fetch_from_gnews(self, product, country, days_back):
        """Fetch news from GNews API"""
        try:
            query = f'{product} {country} trade import export'
            
            params = {
                'q': query,
                'lang': 'en',
                'country': 'us',
                'max': 50,
                'apikey': self.gnews_key
            }
            
            response = requests.get(Config.GNEWS_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for article in data.get('articles', []):
                articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'content': article.get('content', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'published_at': article.get('publishedAt', ''),
                    'image_url': article.get('image', ''),
                    'api_source': 'GNews'
                })
            
            return articles
            
        except Exception as e:
            print(f"Error fetching from GNews: {e}")
            return []
    
    def search_geopolitical_events(self, country):
        """Search for geopolitical events related to a country"""
        keywords = [
            f'{country} sanctions',
            f'{country} trade war',
            f'{country} political crisis',
            f'{country} border closure',
            f'{country} tariff',
            f'{country} embargo'
        ]
        
        all_events = []
        
        for keyword in keywords:
            try:
                if self.newsapi_key:
                    params = {
                        'q': keyword,
                        'language': 'en',
                        'sortBy': 'publishedAt',
                        'apiKey': self.newsapi_key,
                        'pageSize': 10
                    }
                    
                    response = requests.get(Config.NEWSAPI_URL, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    for article in data.get('articles', []):
                        all_events.append({
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'url': article.get('url', ''),
                            'published_at': article.get('publishedAt', ''),
                            'keyword': keyword
                        })
            except Exception as e:
                print(f"Error searching for {keyword}: {e}")
                continue
        
        return deduplicate_news(all_events)[:20]
