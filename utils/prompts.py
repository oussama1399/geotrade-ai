"""
LLM Prompt Templates for GeoTrade AI
Updated for Morocco-specific import context
"""

RELEVANCE_ASSESSMENT_PROMPT = """You are an expert geopolitical analyst assessing risks for an importer based in MOROCCO.

Product: {product}
Source Country: {country}
Destination Country: Morocco

News Article:
Title: {title}
Content: {content}

Analyze if this news article is relevant to importing operations from {country} to MOROCCO.

Consider:
- Direct impact on product availability or pricing in Morocco
- Trade relations between {country} and Morocco
- Shipping routes (Mediterranean, Strait of Gibraltar, Atlantic)
- Regional stability affecting North African supply chains
- Moroccan import regulations or customs issues

Respond in JSON format:
{{
    "is_relevant": true/false,
    "relevance_score": 0-10,
    "reasoning": "brief explanation focused on Morocco impact",
    "key_factors": ["factor1", "factor2"]
}}"""

SEVERITY_SCORING_PROMPT = """You are an expert risk analyst assessing supply chain severity for a MOROCCAN client.

Product: {product}
Source Country: {country}
Destination Country: Morocco

Event Information:
{event_details}

Assess the severity of this event's impact on importing {product} from {country} to MOROCCO.

Consider:
- Logistics: Does this affect shipping routes to major Moroccan ports (Tangier Med, Casablanca, Agadir)?
- Time & Cost: Will this increase transit time or cost for Moroccan importers?
- Alternatives: Can the product be sourced elsewhere easily by Morocco?
- Bilateral Impact: Specific diplomatic or trade effects between Source and Morocco.

Respond in JSON format:
{{
    "severity_score": 1-10,
    "category": "supply_chain|regulatory|economic|security|weather",
    "impact_type": "short_term|medium_term|long_term",
    "confidence": 0-100,
    "reasoning": "detailed explanation of impact on Moroccan operations",
    "recommendations": ["action1", "action2"]
}}"""

SUMMARY_PROMPT = """You are a strategic advisor for a Moroccan import business.

Product: {product}
Source Country: {country}
Destination Country: Morocco

Analyzed Events:
{events_summary}

Create a comprehensive risk assessment summary specifically for the Moroccan market context.

Respond in JSON format:
{{
    "overall_risk": "low|medium|high|critical",
    "risk_score": 1-10,
    "message": "Executive summary for the Moroccan importer",
    "top_concerns": ["concern1", "concern2", "concern3"],
    "recommended_actions": ["action1", "action2"],
    "timeline": "description of when impacts may occur"
}}"""
