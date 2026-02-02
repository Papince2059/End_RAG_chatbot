// ===== Configuration =====
const API_BASE_URL = 'http://localhost:8000';

// ===== DOM Elements =====
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const resultsSection = document.getElementById('resultsSection');
const resultsGrid = document.getElementById('resultsGrid');
const resultsCount = document.getElementById('resultsCount');
const queryTime = document.getElementById('queryTime');
const loadingState = document.getElementById('loadingState');
const emptyState = document.getElementById('emptyState');
const errorState = document.getElementById('errorState');
const errorMessage = document.getElementById('errorMessage');
const totalRemedies = document.getElementById('totalRemedies');
const statusIndicator = document.getElementById('status');
const suggestionChips = document.querySelectorAll('.suggestion-chip');

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    setupEventListeners();
});

// ===== Event Listeners =====
function setupEventListeners() {
    // Search button click
    searchButton.addEventListener('click', performSearch);

    // Enter key in search input
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // Suggestion chips
    suggestionChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.getAttribute('data-query');
            searchInput.value = query;
            performSearch();
        });
    });
}

// ===== Load Statistics =====
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`);

        if (!response.ok) {
            throw new Error('Failed to load stats');
        }

        const data = await response.json();

        // Update UI
        totalRemedies.textContent = data.total_remedies;
        statusIndicator.innerHTML = '<span class="status-dot"></span> Active';

    } catch (error) {
        console.error('Stats error:', error);
        totalRemedies.textContent = '688';
        statusIndicator.innerHTML = '<span class="status-dot" style="background: #ef4444;"></span> Offline';
    }
}

// ===== Perform Search =====
async function performSearch() {
    const query = searchInput.value.trim();

    // Validate input
    if (!query) {
        searchInput.focus();
        return;
    }

    // Show loading state
    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/api/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                top_k: 10
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Search failed');
        }

        const data = await response.json();

        // Display results
        displayResults(data);

    } catch (error) {
        console.error('Search error:', error);
        showError(error.message);
    }
}

// ===== Display Results =====
function displayResults(data) {
    // Hide all states
    hideAllStates();

    // Update metadata
    resultsCount.textContent = data.total_results;
    queryTime.textContent = data.query_time_ms.toFixed(0);

    // Clear previous results
    resultsGrid.innerHTML = '';

    // Check if we have results
    if (data.results.length === 0) {
        showEmpty();
        return;
    }

    // Create remedy cards
    data.results.forEach((remedy, index) => {
        const card = createRemedyCard(remedy, index);
        resultsGrid.appendChild(card);
    });

    // Show results section
    resultsSection.style.display = 'block';
}

// ===== Create Remedy Card =====
function createRemedyCard(remedy, index) {
    const card = document.createElement('div');
    card.className = 'remedy-card';
    card.style.animationDelay = `${index * 0.1}s`;

    const similarityPercent = (remedy.similarity * 100).toFixed(1);

    card.innerHTML = `
        <div class="remedy-header">
            <div>
                <h3 class="remedy-name">${escapeHtml(remedy.remedy_name)}</h3>
                ${remedy.alternative_names ? `<p class="remedy-alt-names">${escapeHtml(remedy.alternative_names)}</p>` : ''}
            </div>
            <div class="similarity-badge">${similarityPercent}%</div>
        </div>
        <p class="remedy-preview" id="preview-${index}">${escapeHtml(remedy.text_preview)}</p>
        <div class="remedy-full-text" id="full-${index}" style="display: none;">
            <div class="full-text-content">${escapeHtml(remedy.full_text)}</div>
        </div>
        <button class="expand-button" onclick="toggleExpand('${index}')" id="btn-${index}">Show More</button>
    `;

    return card;
}

// Global function for toggle
window.toggleExpand = (id) => {
    const full = document.getElementById(`full-${id}`);
    const preview = document.getElementById(`preview-${id}`);
    const btn = document.getElementById(`btn-${id}`);

    if (full.style.display === 'none') {
        full.style.display = 'block';
        preview.style.display = 'none';
        btn.textContent = 'Show Less';
    } else {
        full.style.display = 'none';
        preview.style.display = 'block';
        btn.textContent = 'Show More';
    }
};

// ===== State Management =====
function showLoading() {
    hideAllStates();
    loadingState.style.display = 'block';
}

function showEmpty() {
    hideAllStates();
    emptyState.style.display = 'block';
}

function showError(message) {
    hideAllStates();
    errorMessage.textContent = message;
    errorState.style.display = 'block';
}

function hideAllStates() {
    resultsSection.style.display = 'none';
    loadingState.style.display = 'none';
    emptyState.style.display = 'none';
    errorState.style.display = 'none';
}

// ===== Utility Functions =====
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== Health Check =====
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/`);
        const data = await response.json();

        if (data.status === 'healthy') {
            console.log('✓ Backend is healthy');
            return true;
        }
    } catch (error) {
        console.error('✗ Backend health check failed:', error);
        return false;
    }
}

// Run health check on load
checkBackendHealth();
