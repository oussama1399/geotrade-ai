"""
JSON Storage Model for GeoTrade AI
Replaces SQLite database with simple JSON file storage
"""
import json
import os
from datetime import datetime
from config import Config

class Database:
    def __init__(self, db_path='data/assessments.json'):
        self.db_path = db_path
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        """Ensure data directory and JSON file exist"""
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f:
                json.dump([], f)
    
    def _read_data(self):
        """Read data from JSON file"""
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_data(self, data):
        """Write data to JSON file"""
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    def save_assessment(self, product, country, summary_data):
        """Save assessment to JSON"""
        data = self._read_data()
        
        assessment_id = len(data) + 1
        
        new_assessment = {
            'id': assessment_id,
            'product': product,
            'country': country,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_risk': summary_data.get('overall_risk', 'unknown'),
            'risk_score': summary_data.get('risk_score', 0),
            'total_events': summary_data.get('total_events', 0),
            'avg_severity': summary_data.get('avg_severity', 0),
            'summary_data': summary_data,
            'articles': []  # Will be populated by save_articles
        }
        
        data.append(new_assessment)
        self._write_data(data)
        
        return assessment_id
    
    def save_articles(self, assessment_id, articles):
        """Save news articles to the assessment in JSON"""
        data = self._read_data()
        
        # Find the assessment
        for assessment in data:
            if assessment['id'] == assessment_id:
                # Add timestamp to articles if missing
                for article in articles:
                    if 'created_at' not in article:
                        article['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                assessment['articles'] = articles
                break
        
        self._write_data(data)
    
    def get_recent_assessments(self, limit=10):
        """Get recent assessments from JSON"""
        data = self._read_data()
        
        # Sort by id descending (newest first)
        sorted_data = sorted(data, key=lambda x: x['id'], reverse=True)
        
        return sorted_data[:limit]
    
    def get_assessment_by_id(self, assessment_id):
        """Get assessment by ID from JSON"""
        data = self._read_data()
        
        for assessment in data:
            if assessment['id'] == assessment_id:
                return assessment
                
        return None
