"""
GeoTrade AI - Flask Application
Main application file with routes and API endpoints
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from config import Config
from services.news_aggregator import NewsAggregator
from services.weather_service import WeatherService
from services.llm_filter import LLMFilter
from services.severity_scorer import SeverityScorer
from models.database import Database

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize services
news_aggregator = NewsAggregator()
weather_service = WeatherService()
llm_filter = LLMFilter()
severity_scorer = SeverityScorer()
db = Database()

@app.route('/')
def index():
    """Main dashboard page"""
    recent_assessments = db.get_recent_assessments(limit=5)
    return render_template('index.html', recent_assessments=recent_assessments)

@app.route('/api/check-ollama', methods=['GET'])
def check_ollama():
    """Check Ollama connection status"""
    status = llm_filter.check_ollama_connection()
    return jsonify(status)

@app.route('/api/assess', methods=['POST'])
def assess_risk():
    """
    Main endpoint to assess geopolitical risk
    
    Request JSON:
    {
        "product": "electronics",
        "country": "China",
        "days_back": 7
    }
    """
    try:
        data = request.get_json()
        product = data.get('product', '').strip()
        country = data.get('country', '').strip()
        days_back = data.get('days_back', 7)
        
        if not product or not country:
            return jsonify({
                'status': 'error',
                'message': 'Product and country are required'
            }), 400
        
        # Step 1: Fetch news
        print(f"Fetching news for {product} from {country}...")
        news_articles = news_aggregator.fetch_news(product, country, days_back)
        
        if not news_articles:
            return jsonify({
                'status': 'warning',
                'message': 'No news articles found',
                'data': {
                    'product': product,
                    'country': country,
                    'articles': [],
                    'summary': {
                        'overall_risk': 'unknown',
                        'risk_score': 0,
                        'message': 'No data available for analysis'
                    }
                }
            })
        
        # Step 2: Filter with LLM
        print(f"Filtering {len(news_articles)} articles with LLM...")
        filtered_articles = llm_filter.filter_news(news_articles, product, country)
        
        if not filtered_articles:
            return jsonify({
                'status': 'warning',
                'message': 'No relevant news found after filtering',
                'data': {
                    'product': product,
                    'country': country,
                    'articles': [],
                    'summary': {
                        'overall_risk': 'low',
                        'risk_score': 1,
                        'message': 'No significant risks identified'
                    }
                }
            })
        
        # Step 3: Score severity
        print(f"Scoring severity for {len(filtered_articles)} articles...")
        scored_articles = severity_scorer.score_events(filtered_articles, product, country)
        
        # Step 4: Generate summary
        print("Generating risk summary...")
        summary = severity_scorer.generate_summary(scored_articles, product, country)
        
        # Step 5: Get weather impact
        print("Fetching weather data...")
        weather_impact = weather_service.get_weather_impact(country)
        
        # Step 6: Save to database
        assessment_id = db.save_assessment(product, country, summary)
        db.save_articles(assessment_id, scored_articles)
        
        # Prepare response
        response_data = {
            'product': product,
            'country': country,
            'assessment_id': assessment_id,
            'summary': summary,
            'weather': weather_impact,
            'articles': scored_articles[:20],  # Return top 20
            'total_articles_found': len(news_articles),
            'relevant_articles': len(filtered_articles)
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Risk assessment completed',
            'data': response_data
        })
        
    except Exception as e:
        print(f"Error in risk assessment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/assessment/<int:assessment_id>', methods=['GET'])
def get_assessment(assessment_id):
    """Get assessment by ID"""
    assessment = db.get_assessment_by_id(assessment_id)
    
    if not assessment:
        return jsonify({
            'status': 'error',
            'message': 'Assessment not found'
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': assessment
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get assessment history"""
    limit = request.args.get('limit', 10, type=int)
    assessments = db.get_recent_assessments(limit)
    
    return jsonify({
        'status': 'success',
        'data': assessments
    })

@app.route('/assessment/<int:assessment_id>')
def view_assessment(assessment_id):
    """View detailed assessment page"""
    assessment = db.get_assessment_by_id(assessment_id)
    
    if not assessment:
        return render_template('error.html', message='Assessment not found'), 404
    
    return render_template('assessment.html', assessment=assessment)

if __name__ == '__main__':
    print("Starting GeoTrade AI...")
    print(f"Ollama Model: {Config.OLLAMA_MODEL}")
    print(f"Ollama URL: {Config.OLLAMA_BASE_URL}")
    
    # Check Ollama connection
    ollama_status = llm_filter.check_ollama_connection()
    print(f"Ollama Status: {ollama_status.get('status')}")
    
    if ollama_status.get('status') == 'error':
        print(f"WARNING: {ollama_status.get('message')}")
    
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
