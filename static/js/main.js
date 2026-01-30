// GeoTrade AI - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Check Ollama status on load
    checkOllamaStatus();
    
    // Form submission
    const form = document.getElementById('assessmentForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
});

async function checkOllamaStatus() {
    try {
        const response = await fetch('/api/check-ollama');
        const data = await response.json();
        
        const indicator = document.getElementById('ollamaIndicator');
        const statusLink = document.getElementById('ollamaStatus');
        
        if (data.status === 'connected') {
            indicator.className = 'bi bi-circle-fill text-success';
            statusLink.title = `Connected: ${data.model}`;
        } else if (data.status === 'model_not_found') {
            indicator.className = 'bi bi-circle-fill text-warning';
            statusLink.title = data.message;
        } else {
            indicator.className = 'bi bi-circle-fill text-danger';
            statusLink.title = data.message;
        }
    } catch (error) {
        console.error('Error checking Ollama status:', error);
        const indicator = document.getElementById('ollamaIndicator');
        indicator.className = 'bi bi-circle-fill text-danger';
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const product = document.getElementById('product').value.trim();
    const country = document.getElementById('country').value.trim();
    const daysBack = parseInt(document.getElementById('daysBack').value);
    
    if (!product || !country) {
        alert('Please enter both product and country');
        return;
    }
    
    // Show loading
    showLoading();
    hideResults();
    
    // Scroll to loading section
    document.getElementById('loadingSection').scrollIntoView({ behavior: 'smooth' });
    
    try {
        const response = await fetch('/api/assess', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product: product,
                country: country,
                days_back: daysBack
            })
        });
        
        const result = await response.json();
        
        hideLoading();
        
        if (result.status === 'success' || result.status === 'warning') {
            displayResults(result.data);
        } else {
            alert('Error: ' + result.message);
        }
        
    } catch (error) {
        hideLoading();
        console.error('Error:', error);
        alert('An error occurred while analyzing. Please check console for details.');
    }
}

function showLoading() {
    document.getElementById('loadingSection').style.display = 'block';
    document.getElementById('submitBtn').disabled = true;
    
    // Animate loading text
    const texts = [
        'Fetching news articles...',
        'Filtering with AI...',
        'Scoring severity...',
        'Analyzing weather impact...',
        'Generating summary...'
    ];
    
    let index = 0;
    window.loadingInterval = setInterval(() => {
        document.getElementById('loadingText').textContent = texts[index];
        index = (index + 1) % texts.length;
    }, 3000);
}

function hideLoading() {
    document.getElementById('loadingSection').style.display = 'none';
    document.getElementById('submitBtn').disabled = false;
    if (window.loadingInterval) {
        clearInterval(window.loadingInterval);
    }
}

function hideResults() {
    document.getElementById('resultsSection').style.display = 'none';
}

function displayResults(data) {
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    // Update summary cards
    const summary = data.summary || {};
    
    // Overall risk
    const overallRisk = summary.overall_risk || 'unknown';
    const riskElement = document.getElementById('overallRisk');
    riskElement.textContent = overallRisk.toUpperCase();
    riskElement.className = 'mb-0 text-' + getRiskColor(overallRisk);
    
    // Risk icon
    const riskIcon = document.getElementById('riskIcon');
    riskIcon.className = 'bi bi-exclamation-triangle-fill fs-1 mb-2 text-' + getRiskColor(overallRisk);
    
    // Risk score
    const riskScore = summary.risk_score || 0;
    document.getElementById('riskScore').textContent = riskScore.toFixed(1) + '/10';
    
    // Events count
    document.getElementById('eventsCount').textContent = summary.total_events || 0;
    
    // Weather impact
    const weather = data.weather || {};
    if (weather.status === 'success' && weather.impact) {
        const weatherImpact = weather.impact.impact_level || 'unknown';
        document.getElementById('weatherImpact').textContent = weatherImpact.toUpperCase();
    } else {
        document.getElementById('weatherImpact').textContent = 'N/A';
    }
    
    // Top concerns
    const concernsList = document.getElementById('topConcerns');
    concernsList.innerHTML = '';
    const concerns = summary.top_concerns || [];
    concerns.forEach(concern => {
        const li = document.createElement('li');
        li.className = 'mb-2';
        li.innerHTML = `<i class="bi bi-arrow-right-circle-fill text-danger me-2"></i>${concern}`;
        concernsList.appendChild(li);
    });
    
    // Recommendations
    const recommendationsList = document.getElementById('recommendations');
    recommendationsList.innerHTML = '';
    const recommendations = summary.recommended_actions || [];
    recommendations.forEach(action => {
        const li = document.createElement('li');
        li.className = 'mb-2';
        li.innerHTML = `<i class="bi bi-check-circle-fill text-success me-2"></i>${action}`;
        recommendationsList.appendChild(li);
    });
    
    // Articles
    const articlesList = document.getElementById('articlesList');
    articlesList.innerHTML = '';
    const articles = data.articles || [];
    
    if (articles.length === 0) {
        articlesList.innerHTML = '<p class="text-muted">No detailed events to display.</p>';
    } else {
        articles.forEach((article, index) => {
            const articleCard = createArticleCard(article, index + 1);
            articlesList.appendChild(articleCard);
        });
    }
}

function createArticleCard(article, index) {
    const card = document.createElement('div');
    card.className = 'card mb-3 border-start border-4 border-' + getSeverityColor(article.severity_score);
    
    const severityBadge = getSeverityBadge(article.severity_score);
    const categoryBadge = `<span class="badge bg-secondary">${article.category || 'unknown'}</span>`;
    
    card.innerHTML = `
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h6 class="card-title mb-0">${index}. ${article.title || 'Untitled'}</h6>
                <div>
                    ${severityBadge}
                    ${categoryBadge}
                </div>
            </div>
            <p class="text-muted small mb-2">
                <i class="bi bi-building"></i> ${article.source || 'Unknown'} | 
                <i class="bi bi-calendar"></i> ${formatDate(article.published_at)}
            </p>
            <p class="card-text">${article.description || 'No description available'}</p>
            <div class="row g-2 mb-2">
                <div class="col-md-6">
                    <small class="text-muted">
                        <i class="bi bi-graph-up"></i> Relevance: ${article.relevance_score || 0}/10
                    </small>
                </div>
                <div class="col-md-6">
                    <small class="text-muted">
                        <i class="bi bi-clock"></i> Impact: ${article.impact_type || 'unknown'}
                    </small>
                </div>
            </div>
            ${article.severity_reasoning ? `
                <div class="alert alert-light mb-2">
                    <strong>Analysis:</strong> ${article.severity_reasoning}
                </div>
            ` : ''}
            ${article.recommendations && article.recommendations.length > 0 ? `
                <div class="mb-2">
                    <strong class="small">Recommendations:</strong>
                    <ul class="small mb-0">
                        ${article.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            <a href="${article.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                <i class="bi bi-box-arrow-up-right"></i> Read Full Article
            </a>
        </div>
    `;
    
    return card;
}

function getRiskColor(risk) {
    const riskLower = (risk || '').toLowerCase();
    if (riskLower === 'critical' || riskLower === 'high') return 'danger';
    if (riskLower === 'medium') return 'warning';
    if (riskLower === 'low') return 'success';
    return 'secondary';
}

function getSeverityColor(score) {
    if (score >= 8) return 'danger';
    if (score >= 6) return 'warning';
    if (score >= 3) return 'info';
    return 'success';
}

function getSeverityBadge(score) {
    const color = getSeverityColor(score);
    let label = 'Low';
    if (score >= 8) label = 'Critical';
    else if (score >= 6) label = 'High';
    else if (score >= 3) label = 'Medium';
    
    return `<span class="badge bg-${color}">${label} (${score}/10)</span>`;
}

function formatDate(dateStr) {
    if (!dateStr) return 'Unknown';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch {
        return dateStr;
    }
}
