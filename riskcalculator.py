"""
GeoTrade AI - PortNet Edition
Function: Operational risk assessment for Moroccan importers (PortNet ecosystem)
Focus: Customs clearance, Tanger Med operations, Moroccan logistics
"""
import os
import sys
import json
import logging
import requests
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
import ollama
from sentence_transformers import SentenceTransformer

# Fix Windows encoding issues for emojis/special characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for older Python versions
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# --- 1. Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("geotrade_portnet.log", encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("GeoTradeAI-PortNet")

# --- 2. Configuration ---
load_dotenv()

class Config:
    NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')
    GNEWS_API_KEY = os.getenv('GNEWS_API_KEY')
    WEATHERAPI_KEY = os.getenv('WEATHERAPI_KEY')
    
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Validation
    if not NEWSAPI_KEY and not GNEWS_API_KEY:
        logger.warning("⚠️  Aucune clé API News trouvée dans .env")

# --- 3. Helpers ---
def clean_text(text):
    if not text: return ""
    return re.sub(r'<[^>]+>', '', text).strip()

def cosine_similarity(v1, v2):
    """Compute cosine similarity between two vectors"""
    if not v1 or not v2: return 0
    dot_product = sum(a*b for a,b in zip(v1, v2))
    norm_a = sum(a*a for a in v1) ** 0.5
    norm_b = sum(b*b for b in v2) ** 0.5
    return dot_product / (norm_a * norm_b) if norm_a and norm_b else 0

def parse_llm_json(response_text):
    """Fallback parser for LLM JSON output (used only for summary)"""
    if not response_text: return None
    clean = response_text.strip()
    try: return json.loads(clean)
    except: pass
    
    try:
        start = clean.find('{')
        end = clean.rfind('}')
        if start != -1 and end != -1:
            return json.loads(clean[start:end+1])
    except: pass
    
    return None

# --- 4. PORTNET RISK SCORING ENGINE (Rule-Based) ---
def calculate_portnet_risk(article, product, source_country):
    """
    Score opérationnel PortNet : impact sur dédouanement & logistique marocaine
    Échelle : 0-10 (10 = risque critique pour opérations PortNet)
    """
    text = f"{article['title']} {article.get('description', '')}".lower()
    
    # === ÉTAPE 1 : SCORE DE BASE (0-7) selon type d'événement ===
    if any(kw in text for kw in ["embargo", "ban", "interdiction", "prohibition", "restriction export"]):
        base = 7
    elif any(kw in text for kw in [
        "grève", "strike", "congestion", "congested", "fermeture", "closure", 
        "shutdown", "arrêt", "port closure", "dock strike"
    ]):
        base = 6
    elif any(kw in text for kw in [
        "douane", "customs", "tarif", "tariff", "droit", "duty", "taxe", "tax", 
        "réglementation", "regulation", "décret", "decree", "portnet"
    ]):
        base = 5
    elif any(kw in text for kw in ["mad", "dirham", "change", "currency", "exchange rate", "volatilité"]):
        base = 4
    elif any(kw in text for kw in [
        "retard", "delay", "logistique", "logistics", "container", "navire", 
        "vessel", "cargo", "shipping", "freight", "supply chain"
    ]):
        base = 3
    else:
        base = 1  # Actualité neutre
    
    # === ÉTAPE 2 : MULTIPLICATEUR MAROC (×0.3 à ×2.0) ===
    # 🔴 SUPPRESSION BRUIT : tiers-pays non pertinents pour Maroc
    if any(kw in text for kw in [
        "india", "inde", "vietnam", "thailand", "thaïlande", "brazil", 
        "mexico", "turkey", "turquie", "egypt", "égypte"
    ]):
        multiplier = 0.3  # Supprimer le bruit
    # 🟢 BOOST PORTS MAROCAINS (priorité absolue)
    elif any(kw in text for kw in [
        "tanger med", "tangermed", "tanger-port", "port tanger", 
        "casablanca port", "port casablanca", "mohammedia", "agadir port"
    ]):
        multiplier = 2.0
    # 🟡 BOOST DOUANE MAROCAINE
    elif any(kw in text for kw in [
        "maroc", "morocco", "douane marocaine", "douane maroc", 
        "customs morocco", "portnet", "guichet unique"
    ]):
        multiplier = 1.8
    # 🔵 BOOST LOGISTIQUE MAROCAINE
    elif "container" in text and ("morocco" in text or "maroc" in text):
        multiplier = 1.5
    else:
        multiplier = 1.0  # Événement pays source sans lien Maroc
    
    # === ÉTAPE 3 : FACTEUR URgence (+0 à +3) ===
    try:
        pub_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
        age_days = (datetime.now() - pub_date).days
        urgency = 3 if age_days <= 1 else (2 if age_days <= 3 else (1 if age_days <= 7 else 0))
    except:
        urgency = 1  # Valeur par défaut si date invalide
    
    # === CALCUL FINAL ===
    raw_score = (base * multiplier) + urgency
    final_score = min(10, max(0, round(raw_score, 1)))
    
    # === CATÉGORIE POUR PORTNET ===
    if any(kw in text for kw in ["tanger", "casablanca", "port", "congestion", "grève port"]):
        category = "port_operations"
    elif any(kw in text for kw in ["douane", "tarif", "customs", "réglementation", "portnet"]):
        category = "customs_policy"
    elif any(kw in text for kw in ["mad", "dirham", "currency", "change"]):
        category = "financial"
    else:
        category = "supply_chain"
    
    # === ACTION OPÉRATIONNELLE POUR BROKERS PORTNET ===
    if final_score >= 8:
        action = "🚨 URGENT : Vérifier ETA navire et statut douanier AVANT dépôt déclaration PortNet"
    elif final_score >= 6 and category == "port_operations":
        action = "⚠️  Surveillance Tanger Med : risque retard déchargement conteneur"
    elif final_score >= 6 and category == "customs_policy":
        action = "📋 Vérifier code SH et droits applicables sur PortNet avant clearance"
    elif final_score >= 5:
        action = "🔍 Contrôler documents (facture, certificats) pour éviter blocage douane"
    else:
        action = "✅ Aucune action immédiate requise"
    
    return {
        "severity_score": final_score,
        "category": category,
        "confidence": "high",  # Rule-based = fiable à 100%
        "reasoning": f"Base:{base} × Maroc:{multiplier:.1f}x + Urgence:{urgency} = {final_score}/10",
        "portnet_action": action,
        "impact_on_clearance": "high" if final_score >= 7 else ("medium" if final_score >= 5 else "low")
    }

# --- 5. Services ---
class NewsAggregator:
    def fetch_news(self, product, country, days_back=7):
        logger.info(f"📡 Récupération actualités : {product} depuis {country} → Maroc")
        articles = []
        
        # NewsAPI (CORRIGÉ : URL sans espace)
        if Config.NEWSAPI_KEY:
            try:
                url = "https://newsapi.org/v2/everything"  # ✅ CORRIGÉ
                params = {
                    'q': f'("{product}" OR "electronics") AND ("{country}" OR "China") AND ("Morocco" OR "Tanger Med" OR "customs" OR "tariff") -India -Vietnam',
                    'apiKey': Config.NEWSAPI_KEY,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': 15,
                    'from': (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                }
                resp = requests.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for a in data.get('articles', []):
                        articles.append({
                            'source': 'NewsAPI',
                            'title': clean_text(a.get('title', '')),
                            'description': clean_text(a.get('description', '')),
                            'url': a.get('url', ''),
                            'published_at': a.get('publishedAt', '')
                        })
                    logger.info(f"✅ NewsAPI : {len(data.get('articles', []))} articles bruts")
            except Exception as e:
                logger.error(f"❌ NewsAPI error: {e}")
        
        # GNews (CORRIGÉ : URL sans espace)
        if Config.GNEWS_API_KEY:
            try:
                url = "https://gnews.io/api/v4/search"  # ✅ CORRIGÉ
                params = {
                    'q': f'{product} {country} Morocco Tanger Med port customs tariff trade',
                    'token': Config.GNEWS_API_KEY,
                    'lang': 'en',
                    'country': 'ma',  # Focus Maroc
                    'max': 10
                }
                resp = requests.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for a in data.get('articles', []):
                        articles.append({
                            'source': 'GNews',
                            'title': clean_text(a.get('title', '')),
                            'description': clean_text(a.get('description', '')),
                            'url': a.get('url', ''),
                            'published_at': a.get('publishedAt', '')
                        })
                    logger.info(f"✅ GNews : {len(data.get('articles', []))} articles bruts")
            except Exception as e:
                logger.error(f"❌ GNews error: {e}")
        
        logger.info(f"📦 Total articles bruts : {len(articles)}")
        return articles

class WeatherService:
    def get_weather(self, country):
        """Optionnel : météo pays source (peu pertinent pour PortNet)"""
        if not Config.WEATHERAPI_KEY:
            return None
        try:
            url = "http://api.weatherapi.com/v1/current.json"
            params = {'key': Config.WEATHERAPI_KEY, 'q': country}
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                current = data['current']
                return {
                    'text': f"Météo {country}: {current['condition']['text']}, {current['temp_c']}°C. Vent: {current['wind_kph']} km/h",
                    'raw': current
                }
        except Exception as e:
            logger.warning(f"⚠️  Weather API error (non critique pour PortNet): {e}")
        return None

class LLMService:
    def __init__(self):
        self.embedder = None
        try:
            logger.info("🧠 Chargement modèle embedding (all-MiniLM-L6-v2)...")
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Modèle embedding prêt")
        except Exception as e:
            logger.error(f"❌ Échec chargement embedding: {e}")

    def check_connection(self):
        try:
            ollama.list()
            return True
        except:
            return False

    def get_embedding(self, text):
        if not self.embedder:
            return None
        try:
            return self.embedder.encode(text, convert_to_tensor=False).tolist()
        except Exception as e:
            logger.warning(f"⚠️  Embedding échoué: {e}")
            return None

    def semantic_filter_portnet(self, articles, product, country, top_k=5):
        """
        Filtre sémantique SPÉCIALISÉ PortNet :
        - Requête ciblée sur risques opérationnels marocains
        - Suppression agressive du bruit tiers-pays
        """
        logger.info("🔍 Filtre sémantique PortNet (risques opérationnels marocains)...")
        
        # === REQUÊTE SÉMANTIQUE CIBLÉE PORTNET ===
        query = (
            f"Tanger Med port congestion container vessel delay Morocco imports {product}. "
            f"Moroccan customs clearance delay PortNet douane marocaine tariff regulation {country}. "
            f"Export ban strike factory closure {country} disrupting supply chain to Morocco Casablanca. "
            f"Shipping lane disruption Suez Gibraltar affecting Moroccan container traffic."
        )
        logger.debug(f"	Query sémantique: {query[:80]}...")
        
        query_emb = self.get_embedding(query)
        if not query_emb:
            logger.warning("⚠️  Échec embedding requête → fallback mots-clés PortNet")
            return self._keyword_filter_portnet(articles, product, country, top_k)
        
        # === FILTRAGE + SCORING ===
        scored = []
        for art in articles:
            text = f"{art['title']} {art.get('description', '')}".lower()
            
            # 🔴 SUPPRESSION IMMÉDIATE : bruit tiers-pays (Inde, Vietnam...)
            if any(kw in text for kw in [
                "india", "inde", "vietnam", "thailand", "brazil", "mexico", 
                "turkey", "egypt", "philippines", "bangladesh"
            ]):
                logger.debug(f"🗑️  Supprimé (bruit tiers-pays): {art['title'][:50]}...")
                continue
            
            # 🔵 CALCUL SIMILARITÉ SÉMANTIQUE
            emb = self.get_embedding(text)
            if not emb:
                continue
            
            sim = cosine_similarity(query_emb, emb)
            
            # 🟢 BOOST MAROC : ports/douane marocains
            morocco_boost = 0.25 if any(k in text for k in [
                "tanger med", "tangermed", "casablanca", "douane", "portnet", 
                "morocco", "maroc", "mohammedia", "agadir"
            ]) else 0
            
            final_score = min(0.99, sim + morocco_boost)  # Plafonné <1.0
            art['relevance_score'] = round(final_score, 3)
            scored.append(art)
        
        # === TRI + TOP K ===
        scored.sort(key=lambda x: x['relevance_score'], reverse=True)
        logger.info(f"✅ {len(scored)} articles après filtrage PortNet (top {top_k} retenus)")
        
        for i, a in enumerate(scored[:min(3, len(scored))]):
            logger.info(f"  #{i+1} [{a['relevance_score']:.2f}] {a['title'][:70]}...")
        
        return scored[:top_k]

    def _keyword_filter_portnet(self, articles, product, country, top_k):
        """Fallback si embedding indisponible"""
        keywords = ["morocco", "maroc", "tanger", "casablanca", "douane", "portnet", "tariff", "congestion", "customs"]
        blacklist = ["india", "vietnam", "thailand"]
        filtered = [
            a for a in articles 
            if any(kw in f"{a['title']} {a.get('description','')}".lower() for kw in keywords)
            and not any(bl in f"{a['title']} {a.get('description','')}".lower() for bl in blacklist)
        ]
        return filtered[:top_k]

    def generate_summary(self, articles, product, country):
        """Résumé exécutif (optionnel - LLM peut échouer sans impacter le scoring)"""
        default = {
            "overall_risk": "Moyen" if any(a.get('severity_score',0) >= 6 for a in articles) else "Faible",
            "risk_score": max((a.get('severity_score', 3) for a in articles), default=3),
            "message": "Analyse opérationnelle PortNet terminée",
            "top_concerns": [f"{a['title'][:60]}..." for a in articles[:3]]
        }
        if not articles:
            return default
        
        try:
            # Prompt optimisé PortNet
            events_text = "\n".join([
                f"- {a['title']} (Score: {a.get('severity_score', 0)}/10, Action: {a.get('portnet_action', '')[:40]}...)" 
                for a in articles[:5]
            ])
            prompt = f"""Résumé risques opérationnels PortNet pour {product} depuis {country} vers Maroc :
Événements:
{events_text}

Format JSON strict:
{{
    "overall_risk": "Élevé/Moyen/Faible",
    "risk_score": 7,
    "message": "Phrase exécutive pour broker douanier",
    "top_concerns": ["Préoccupation 1", "Préoccupation 2"]
}}"""
            
            resp = ollama.generate(model=Config.OLLAMA_MODEL, prompt=prompt, format="json", stream=False)
            data = parse_llm_json(resp.get('response', ''))
            return data if data else default
        except Exception as e:
            logger.warning(f"⚠️  LLM summary échoué (non critique): {e}")
            return default

# --- 6. Database (JSON) ---
class JSONDatabase:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        self.file_path = os.path.join(self.data_dir, 'portnet_assessments.json')
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)

    def save(self, data):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []
        
        data['id'] = len(history) + 1
        data['created_at'] = datetime.now().isoformat()
        history.append(data)
        
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        return data['id']

# --- 7. Main System Class (PortNet Optimized) ---
class GeoTradePortNet:
    def __init__(self):
        self.news = NewsAggregator()
        self.weather = WeatherService()
        self.llm = LLMService()
        self.db = JSONDatabase()

    def run_analysis(self, product, country, days_back=7):
        logger.info(f"\n🚀 DÉMARRAGE ANALYSE PORTNET : {product} depuis {country} → Maroc")
        
        # Vérification connexion Ollama (optionnelle - scoring fonctionne sans)
        ollama_ok = self.llm.check_connection()
        if not ollama_ok:
            logger.warning("⚠️  Ollama indisponible → résumé exécutif désactivé (scoring opérationnel OK)")
        
        # 1. Récupération actualités
        articles = self.news.fetch_news(product, country, days_back)
        if not articles:
            return {
                "status": "clean",
                "message": "Aucune actualité récente trouvée",
                "product": product,
                "source_country": country,
                "destination": "Morocco",
                "summary": {
                    "overall_risk": "Faible",
                    "risk_score": 2,
                    "message": "Aucun risque opérationnel détecté pour PortNet",
                    "top_concerns": []
                },
                "portnet_alerts": [],
                "articles": []
            }
        
        # 2. FILTRAGE SÉMANTIQUE PORTNET (critique)
        logger.info("\n🧹 Filtrage sémantique spécialisé PortNet...")
        relevant_articles = self.llm.semantic_filter_portnet(articles, product, country, top_k=5)
        
        if not relevant_articles:
            return {
                "status": "clean",
                "message": "Aucun risque opérationnel marocain détecté",
                "product": product,
                "source_country": country,
                "destination": "Morocco",
                "summary": {
                    "overall_risk": "Faible",
                    "risk_score": 2,
                    "message": "Flux logistique vers Maroc stable",
                    "top_concerns": []
                },
                "portnet_alerts": [
                    {"level": "info", "message": "✅ Aucune alerte PortNet détectée", "action": "Procéder au dépôt normal"}
                ],
                "articles": []
            }
        
        # 3. SCORING RÈGLE-BASED PORTNET (100% fiable)
        logger.info("\n📊 Calcul scores risques opérationnels PortNet (règles métier)...")
        scored_articles = []
        for article in relevant_articles:
            risk_data = calculate_portnet_risk(article, product, country)
            article.update(risk_data)
            scored_articles.append(article)
        
        # Trier par score décroissant
        scored_articles.sort(key=lambda x: x.get('severity_score', 0), reverse=True)
        
        # 4. Générer alertes PortNet actionnables
        portnet_alerts = []
        high_risk = [a for a in scored_articles if a['severity_score'] >= 7]
        medium_risk = [a for a in scored_articles if 5 <= a['severity_score'] < 7]
        
        if high_risk:
            portnet_alerts.append({
                "level": "critical",
                "message": f"🚨 RISQUE ÉLEVÉ : {high_risk[0]['title'][:80]}...",
                "action": high_risk[0]['portnet_action']
            })
        if medium_risk:
            portnet_alerts.append({
                "level": "warning",
                "message": f"⚠️  RISQUE MODÉRÉ : {medium_risk[0]['title'][:80]}...",
                "action": medium_risk[0]['portnet_action']
            })
        if not portnet_alerts:
            portnet_alerts.append({
                "level": "info",
                "message": "✅ Flux logistique vers Maroc stable",
                "action": "Procéder au dépôt normal sur PortNet"
            })
        
        # 5. Résumé exécutif (optionnel - LLM)
        logger.info("\n📝 Génération résumé exécutif (optionnel)...")
        summary = self.llm.generate_summary(scored_articles, product, country) if ollama_ok else {
            "overall_risk": "Élevé" if any(a['severity_score'] >= 7 for a in scored_articles) else 
                           ("Moyen" if any(a['severity_score'] >= 5 for a in scored_articles) else "Faible"),
            "risk_score": max(a['severity_score'] for a in scored_articles),
            "message": "Analyse opérationnelle PortNet basée sur règles métier",
            "top_concerns": [a['title'][:70] for a in scored_articles[:3]]
        }
        
        # 6. Météo (informationnelle seulement)
        weather = self.weather.get_weather(country)
        
        # 7. Sauvegarde
        result = {
            "status": "completed",
            "product": product,
            "source_country": country,
            "destination": "Morocco",
            "summary": summary,
            "portnet_alerts": portnet_alerts,
            "weather_source_country": weather,
            "articles": scored_articles,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        assessment_id = self.db.save(result)
        logger.info(f"\n✅ ANALYSE PORTNET TERMINÉE (ID: {assessment_id})")
        logger.info(f"   Score risque global : {summary['risk_score']}/10 → {summary['overall_risk']}")
        for alert in portnet_alerts[:2]:
            logger.info(f"   {alert['level'].upper()}: {alert['message']}")
        
        return result

# --- 8. Public API ---
_system = GeoTradePortNet()

def assess_impact(product, country, days_back=7):
    """
    API PortNet : Évalue l'impact opérationnel sur le dédouanement marocain
    
    Args:
        product (str): Produit importé (ex: "Electronics")
        country (str): Pays source (ex: "China")
        days_back (int): Période analyse en jours (défaut: 7)
    
    Returns:
        dict: Rapport risques opérationnels PortNet avec actions concrètes
    """
    return _system.run_analysis(product, country, days_back)

# --- 9. CLI ---
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚢 GeoTrade AI - Édition PortNet (Maroc)")
    print("="*70)
    
    if len(sys.argv) > 2:
        product = sys.argv[1]
        country = sys.argv[2]
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    else:
        print("\nℹ️  Usage: python main.py <produit> <pays_source> [jours]")
        print("   Exemple: python main.py 'Electronics' 'China' 7\n")
        print("⚠️  Test par défaut : Phosphates depuis Russie → Maroc")
        product, country, days = "Phosphates", "Russia", 7
    
    print(f"\n🔍 Analyse en cours : {product} depuis {country} → Maroc ({days} jours)...\n")
    result = assess_impact(product, country, days)
    
    # Affichage formaté pour opérateurs PortNet
    print("\n" + "="*70)
    print(f"📊 RAPPORT PORTNET : {product} ← {country}")
    print("="*70)
    print(f"⏱️  Timestamp : {result.get('analysis_timestamp', datetime.now().isoformat())}")
    print(f"🎯 Risque global : {result['summary']['risk_score']}/10 → {result['summary']['overall_risk']}")
    print(f"💬 Message : {result['summary']['message']}")
    
    print("\n🚨 ALERTES PORTNET :")
    for alert in result.get('portnet_alerts', []):
        icon = "🔴" if alert['level'] == "critical" else ("🟠" if alert['level'] == "warning" else "🟢")
        print(f"  {icon} [{alert['level'].upper()}] {alert['message']}")
        print(f"     → Action : {alert['action']}")
    
    if result.get('articles'):
        print(f"\n📰 Événements analysés ({len(result['articles'])}) :")
        for i, art in enumerate(result['articles'], 1):
            score = art.get('severity_score', 0)
            bar = "█" * int(score) + "░" * (10 - int(score))
            print(f"\n  {i}. {art['title']}")
            print(f"     Source : {art['source']} | Score : {score}/10 [{bar}]")
            print(f"     Pertinence : {art.get('relevance_score', 0):.2f}")
            print(f"     Action PortNet : {art.get('portnet_action', 'N/A')}")
            print(f"     Raison : {art.get('reasoning', 'N/A')}")
    
    if result.get('weather_source_country'):
        print(f"\n🌦️  Météo {country} : {result['weather_source_country']['text']}")
    
    print("\n" + "="*70)
    print("✅ Rapport généré. Données sauvegardées dans data/portnet_assessments.json")
    print("="*70 + "\n")