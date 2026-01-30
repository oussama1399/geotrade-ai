# GeoTrade AI - Quick Setup Guide

## Step 1: Get API Keys

### 1. NewsAPI (Free)
1. Visit [https://newsapi.org/](https://newsapi.org/)
2. Click "Get API Key"
3. Sign up for free account
4. Copy your API key
5. Add to `.env`: `NEWSAPI_KEY="your_key_here"`

### 2. GNews API (Free)
1. Visit [https://gnews.io/](https://gnews.io/)
2. Click "Sign Up"
3. Create free account
4. Copy API key from dashboard
5. Add to `.env`: `GNEWS_API_KEY="your_key_here"`

### 3. WeatherAPI (Free)
1. Visit [https://www.weatherapi.com/](https://www.weatherapi.com/)
2. Click "Sign Up Free"
3. Create free account
4. Go to your dashboard
5. Copy your API key
6. Add to `.env`: `WEATHERAPI_KEY="your_key_here"`

## Step 2: Install Ollama

### Windows
1. Download from [https://ollama.ai/download](https://ollama.ai/download)
2. Run the installer
3. Open PowerShell and run:
   ```powershell
   ollama pull llama3.2
   ```
4. Verify it's running:
   ```powershell
   ollama list
   ```

## Step 3: Run the Application

1. Make sure you're in the project directory and virtual environment is activated:
   ```powershell
   cd "c:\Users\najib\Desktop\geotrade ai"
   .\.venv\Scripts\activate
   ```

2. Start the Flask application:
   ```powershell
   python app.py
   ```

3. Open your browser and go to:
   ```
   http://localhost:5000
   ```

## Step 4: Test the System

1. Enter a product (e.g., "Electronics")
2. Enter a country (e.g., "China")
3. Select analysis period (e.g., "Last 7 days")
4. Click "Analyze Risk"
5. Wait for the AI to process (may take 1-2 minutes)
6. Review the results!

## Troubleshooting

### Ollama Not Connected
- Make sure Ollama is running in the background
- Check that the model is installed: `ollama list`
- Verify the URL in `.env` is `http://localhost:11434`

### No News Found
- Check your API keys are correct in `.env`
- Free tier limits: NewsAPI (100/day), GNews (100/day)
- Try a different product/country combination

### Slow Performance
- Use a smaller model: `ollama pull phi3`
- Update `.env`: `OLLAMA_MODEL=phi3`
- Reduce analysis period to 3 days

## Free Tier Limits

- **NewsAPI**: 100 requests/day, 1 month historical data
- **GNews**: 100 requests/day
- **WeatherAPI**: 1 million calls/month (more than enough!)
- **Ollama**: Unlimited (runs locally)

Enjoy using GeoTrade AI! 🚀
