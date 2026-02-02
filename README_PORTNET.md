# GeoTrade AI - PortNet Edition Documentation

The **PortNet Edition** (`main.py`) is a specialized monolithic tool designed for Moroccan importers and brokers. It focuses on operational risks within the PortNet ecosystem, specifically targeting customs clearance and Tanger Med port logistics.

## 🌟 Key Features

- **Rule-Based Scoring Engine**: A deterministic scoring system optimized for Moroccan regulations.
- **PortNet Specific Alerts**: Actionable alerts for brokers (e.g., "Vérifier ETA navire avant dépôt PortNet").
- **Semantic Filtering**: Uses local embeddings to filter out irrelevant news (noise from non-Morocco trade partners).
- **French/Arabic Context**: Prompts and logic tuned for the Moroccan business environment.

## 📊 Scoring Engine (How it works)

The `calculate_portnet_risk` function uses a three-step process:

1.  **Base Score (0-7)**: Assigned based on event type (Embargo, Strike, Customs change, Currency volatility).
2.  **Morocco Multiplier (×0.3 to ×2.0)**: Boosts relevance for Moroccan keywords (Tanger Med, Casablanca, Douane) and suppress irrelevant countries.
3.  **Urgency Factor (+0 to +3)**: Extra points for very recent news (less than 1-3 days old).

## 🚀 Usage

Run the analysis from the command line:

```bash
python main.py "Product Name" "Source Country" [days_back]
```

### Example:
```bash
python main.py "Electronics" "China" 7
```

## 📋 Output Fields

- **Severity Score**: 0-10 scale (10 being critical).
- **PortNet Action**: Concrete recommendation for the importer.
- **Impact on Clearance**: High/Medium/Low assessment for customs procedures.
- **PortNet Alerts**: Categorized alerts (Critical, Warning, Info).

## 🔧 Technical Details

- **Logs**: Saved to `geotrade_portnet.log`.
- **History**: Analyses are saved in `data/portnet_assessments.json`.
- **Dependencies**: `sentence-transformers` for embeddings, `ollama` for summary (optional).
