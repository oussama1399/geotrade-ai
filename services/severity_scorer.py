"""
Severity Scorer Service
Analyzes filtered news and assigns severity scores
"""
import ollama
from config import Config
from utils.prompts import SEVERITY_SCORING_PROMPT, SUMMARY_PROMPT
from utils.helpers import parse_json_response, truncate_text

class SeverityScorer:
    def __init__(self):
        self.model = Config.OLLAMA_MODEL
        
    def score_events(self, filtered_articles, product, country):
        """
        Score severity of filtered news articles
        
        Args:
            filtered_articles: List of filtered news articles
            product: Product being imported
            country: Source country
            
        Returns:
            List of articles with severity scores
        """
        scored_articles = []
        
        for article in filtered_articles:
            try:
                # Score severity
                severity_data = self._score_article(article, product, country)
                
                # Add severity data to article
                article['severity_score'] = severity_data.get('severity_score', 5)
                article['category'] = severity_data.get('category', 'unknown')
                article['impact_type'] = severity_data.get('impact_type', 'medium_term')
                article['confidence'] = severity_data.get('confidence', 50)
                article['severity_reasoning'] = severity_data.get('reasoning', '')
                article['recommendations'] = severity_data.get('recommendations', [])
                
                scored_articles.append(article)
                
            except Exception as e:
                print(f"Error scoring article: {e}")
                # Add default scores
                article['severity_score'] = 5
                article['category'] = 'unknown'
                article['impact_type'] = 'medium_term'
                article['confidence'] = 50
                article['severity_reasoning'] = 'Unable to assess severity'
                article['recommendations'] = []
                scored_articles.append(article)
        
        # Sort by severity score (highest first)
        scored_articles.sort(key=lambda x: x.get('severity_score', 0), reverse=True)
        
        return scored_articles
    
    def _score_article(self, article, product, country):
        """Score severity of a single article using Ollama"""
        try:
            # Prepare event details
            event_details = f"""
Title: {article.get('title', '')}
Description: {article.get('description', '')}
Content: {truncate_text(article.get('content', ''), 800)}
Published: {article.get('published_at', '')}
Source: {article.get('source', '')}
Relevance Score: {article.get('relevance_score', 0)}/10
Key Factors: {', '.join(article.get('key_factors', []))}
"""
            
            # Build prompt
            prompt = SEVERITY_SCORING_PROMPT.format(
                product=product,
                country=country,
                event_details=event_details
            )
            
            # Call Ollama
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert risk analyst. Always respond with valid JSON only.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.3,
                }
            )
            
            # Parse response
            response_text = response['message']['content']
            severity_data = parse_json_response(response_text)
            
            return severity_data
            
        except Exception as e:
            print(f"Error in severity scoring: {e}")
            return {
                'severity_score': 5,
                'category': 'unknown',
                'impact_type': 'medium_term',
                'confidence': 50,
                'reasoning': 'Unable to assess severity',
                'recommendations': []
            }
    
    def generate_summary(self, scored_articles, product, country):
        """
        Generate overall risk assessment summary
        
        Args:
            scored_articles: List of scored articles
            product: Product being imported
            country: Source country
            
        Returns:
            Dictionary with overall risk assessment
        """
        try:
            # Prepare events summary
            events_summary = []
            for i, article in enumerate(scored_articles[:10], 1):  # Top 10 events
                events_summary.append(f"""
{i}. {article.get('title', 'Unknown')}
   Severity: {article.get('severity_score', 0)}/10
   Category: {article.get('category', 'unknown')}
   Impact: {article.get('impact_type', 'unknown')}
   Reasoning: {truncate_text(article.get('severity_reasoning', ''), 200)}
""")
            
            events_text = '\n'.join(events_summary)
            
            # Build prompt
            prompt = SUMMARY_PROMPT.format(
                product=product,
                country=country,
                events_summary=events_text
            )
            
            # Call Ollama
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert risk analyst. Always respond with valid JSON only.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.4,
                }
            )
            
            # Parse response
            response_text = response['message']['content']
            summary = parse_json_response(response_text)
            
            # Add statistics
            summary['total_events'] = len(scored_articles)
            summary['avg_severity'] = sum(a.get('severity_score', 0) for a in scored_articles) / len(scored_articles) if scored_articles else 0
            summary['high_severity_count'] = len([a for a in scored_articles if a.get('severity_score', 0) >= 7])
            
            return summary
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            # Calculate basic statistics
            avg_severity = sum(a.get('severity_score', 0) for a in scored_articles) / len(scored_articles) if scored_articles else 0
            
            return {
                'overall_risk': 'medium' if avg_severity > 5 else 'low',
                'risk_score': round(avg_severity, 1),
                'top_concerns': ['Unable to generate detailed analysis'],
                'recommended_actions': ['Review individual events manually'],
                'timeline': 'Unknown',
                'total_events': len(scored_articles),
                'avg_severity': avg_severity,
                'high_severity_count': len([a for a in scored_articles if a.get('severity_score', 0) >= 7])
            }
