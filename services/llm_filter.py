"""
LLM Filter Service
Uses Ollama to filter and analyze news relevance
"""
import ollama
import json
from config import Config
from utils.prompts import RELEVANCE_ASSESSMENT_PROMPT
from utils.helpers import parse_json_response, truncate_text

class LLMFilter:
    def __init__(self):
        self.model = Config.OLLAMA_MODEL
        self.base_url = Config.OLLAMA_BASE_URL
        
    def filter_news(self, articles, product, country):
        """
        Filter news articles for relevance using LLM
        
        Args:
            articles: List of news articles
            product: Product being imported
            country: Source country
            
        Returns:
            List of filtered articles with relevance scores
        """
        filtered_articles = []
        
        for article in articles:
            try:
                # Assess relevance
                assessment = self._assess_relevance(article, product, country)
                
                # Only include if relevant
                if assessment.get('is_relevant', False):
                    article['relevance_score'] = assessment.get('relevance_score', 0)
                    article['relevance_reasoning'] = assessment.get('reasoning', '')
                    article['key_factors'] = assessment.get('key_factors', [])
                    filtered_articles.append(article)
                    
            except Exception as e:
                print(f"Error filtering article: {e}")
                # Include article with low score if filtering fails
                article['relevance_score'] = 5
                article['relevance_reasoning'] = 'Unable to assess relevance'
                article['key_factors'] = []
                filtered_articles.append(article)
        
        # Sort by relevance score (highest first)
        filtered_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return filtered_articles
    
    def _assess_relevance(self, article, product, country):
        """Assess relevance of a single article using Ollama"""
        try:
            # Prepare content (use description or content)
            content = article.get('content') or article.get('description', '')
            content = truncate_text(content, 1000)  # Limit token usage
            
            # Build prompt
            prompt = RELEVANCE_ASSESSMENT_PROMPT.format(
                product=product,
                country=country,
                title=article.get('title', ''),
                content=content
            )
            
            # Call Ollama
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert analyst. Always respond with valid JSON only.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.3,  # Lower temperature for more consistent output
                }
            )
            
            # Parse response
            response_text = response['message']['content']
            assessment = parse_json_response(response_text)
            
            return assessment
            
        except Exception as e:
            print(f"Error in LLM assessment: {e}")
            # Return default assessment
            return {
                'is_relevant': True,  # Default to including articles
                'relevance_score': 5,
                'reasoning': 'Unable to assess relevance',
                'key_factors': []
            }
    
    def check_ollama_connection(self):
        """Check if Ollama is running and model is available"""
        try:
            # Try to list models
            models = ollama.list()
            
            # Check if our model is available
            model_names = [m['name'] for m in models.get('models', [])]
            
            if self.model in model_names or any(self.model in name for name in model_names):
                return {
                    'status': 'connected',
                    'model': self.model,
                    'available_models': model_names
                }
            else:
                return {
                    'status': 'model_not_found',
                    'model': self.model,
                    'available_models': model_names,
                    'message': f'Model {self.model} not found. Please pull it with: ollama pull {self.model}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Cannot connect to Ollama: {str(e)}. Make sure Ollama is running.'
            }
