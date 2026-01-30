"""
GeoTrade AI - Main Library Interface
This module acts as the entry point for integrating GeoTrade AI into larger systems.
"""
import sys
import os

# Add the core directory to python path so internal imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.join(current_dir, 'geotrade_core')
sys.path.append(core_dir)

# Now we can import from the core modules
from services.news_aggregator import NewsAggregator
from services.weather_service import WeatherService
from services.llm_filter import LLMFilter
from services.severity_scorer import SeverityScorer
from models.database import Database

class GeoTradeSystem:
    def __init__(self):
        """Initialize all AI and data services"""
        self.news = NewsAggregator()
        self.weather = WeatherService()
        self.filter = LLMFilter()
        self.scorer = SeverityScorer()
        
        # Initialize DB with the correct path inside geotrade_core
        db_path = os.path.join(core_dir, 'data', 'assessments.json')
        self.db = Database(db_path=db_path)
        
    def analyze_risk(self, product: str, source_country: str, days_back: int = 7):
        """
        Perform a complete risk analysis for a product import
        
        Args:
            product: Name of the product (e.g., "Electronics")
            source_country: Origin country (e.g., "China")
            days_back: Number of days to look back for news
            
        Returns:
            Dictionary containing the full assessment including summary, events, and weather
        """
        print(f"[*] Starting analysis for {product} from {source_country} to Morocco")
        
        # 1. Fetch News
        articles = self.news.fetch_news(product, source_country, days_back)
        if not articles:
            return {"error": "No news data found", "status": "failed"}
            
        # 2. Filter Relevance (AI)
        relevant_articles = self.filter.filter_news(articles, product, source_country)
        if not relevant_articles:
            return {"error": "No relevant news identified", "status": "no_risks"}
            
        # 3. Score Severity (AI)
        scored_events = self.scorer.score_events(relevant_articles, product, source_country)
        
        # 4. Generate Strategic Summary (AI)
        summary = self.scorer.generate_summary(scored_events, product, source_country)
        
        # 5. Check Weather Logistics
        weather = self.weather.get_weather_impact(source_country)
        
        # 6. Save to History
        assessment_id = self.db.save_assessment(product, source_country, summary)
        self.db.save_articles(assessment_id, scored_events)
        
        return {
            "status": "success",
            "assessment_id": assessment_id,
            "summary": summary,
            "weather": weather,
            "events": scored_events,
            "meta": {
                "product": product,
                "source": source_country,
                "destination": "Morocco"
            }
        }

    def check_system_health(self):
        """Check if all separate modules are functioning"""
        llm_status = self.filter.check_ollama_connection()
        return {
            "ollama": llm_status,
            "database": "connected" if self.db else "error"
        }

# Simplified functional interface for direct import
_system = GeoTradeSystem()

def assess_impact(product, country, days_back=7):
    """
    Main public function to assess geopolitical impact
    """
    return _system.analyze_risk(product, country, days_back)

if __name__ == "__main__":
    # Example usage when running standalone
    print("Testing GeoTrade AI System Integration...")
    # Example test
    result = assess_impact("Textiles", "China")
    import json
    print(json.dumps(result, indent=2))
