// Global State
const API_BASE = document.getElementById("api-url").value;
let currentView = "scrapers";
let activeScraperId = null;

// DOM Elements
const mainContent = document.getElementById("main-content");
const connectionStatus = document.getElementById("connection-status");
const refreshBtn = document.getElementById("refresh-btn");
const pageTitle = document.getElementById("page-title");
const apiUrlInput = document.getElementById("api-url");

// Listeners
document.getElementById("nav-scrapers").addEventListener("click", () => loadView("scrapers"));
// document.getElementById("nav-runs").addEventListener("click", () => loadView("runs"));
// document.getElementById("nav-alerts").addEventListener("click", () => loadView("alerts"));
refreshBtn.addEventListener("click", () => loadView(currentView));
apiUrlInput.addEventListener("change", () => loadView(currentView));

// Utility: Fetch with error handling
async function fetchApi(endpoint) {
    const baseUrl = apiUrlInput.value.replace(/\/$/, ""); // remove trailing slash
    try {
        const response = await fetch(`${baseUrl}/api/v1${endpoint}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        updateStatus(true);
        return data;
    } catch (e) {
        console.error("Fetch error:", e);
        updateStatus(false);
        return null;
    }
}

function updateStatus(connected) {
    if (connected) {
        connectionStatus.textContent = "Connected";
        connectionStatus.className = "px-2 py-1 text-xs rounded-full bg-green-100 text-green-800";
    } else {
        connectionStatus.textContent = "Error";
        connectionStatus.className = "px-2 py-1 text-xs rounded-full bg-red-100 text-red-800";
    }
}

// Views
async function loadView(view, id = null) {
    currentView = view;
    mainContent.innerHTML = '<div class="text-center text-gray-500 mt-20">Loading...</div>';

    if (view === "scrapers") {
        pageTitle.textContent = "Scrapers";
        const scrapers = await fetchApi("/scrapers");
        renderScrapersTable(scrapers);
    } else if (view === "scraper_details") {
        activeScraperId = id;
        pageTitle.textContent = "Scraper Details";
        const scraper = await fetchApi(`/scrapers/${id}`);
        const runs = await fetchApi(`/scrapers/${id}/runs`);
        const alerts = await fetchApi(`/scrapers/${id}/alerts`);
        renderScraperDetails(scraper, runs, alerts);
    }
}

function renderScrapersTable(scrapers) {
    if (!scrapers || scrapers.length === 0) {
        mainContent.innerHTML = '<div class="text-center text-gray-500 mt-20">No scrapers found. Run the demo script first!</div>';
        return;
    }

    let html = `
        <div class="bg-white shadow rounded-lg overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Target URL</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created At</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
    `;

    scrapers.forEach(scraper => {
        html += `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${scraper.config.name}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${scraper.config.target_url}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${new Date(scraper.created_at).toLocaleString()}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onclick="loadView('scraper_details', '${scraper.id}')" class="text-indigo-600 hover:text-indigo-900">View Details</button>
                </td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    mainContent.innerHTML = html;
}

function renderScraperDetails(scraper, runs, alerts) {
    if (!scraper) {
        mainContent.innerHTML = '<div class="text-red-500">Failed to load scraper details.</div>';
        return;
    }

    let html = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <!-- Scraper Info -->
            <div class="bg-white shadow rounded-lg p-6">
                <h3 class="text-lg font-medium text-gray-900 mb-2">Configuration</h3>
                <dl class="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
                    <div class="sm:col-span-1">
                        <dt class="text-sm font-medium text-gray-500">Name</dt>
                        <dd class="mt-1 text-sm text-gray-900">${scraper.config.name}</dd>
                    </div>
                    <div class="sm:col-span-1">
                        <dt class="text-sm font-medium text-gray-500">Target URL</dt>
                        <dd class="mt-1 text-sm text-gray-900">${scraper.config.target_url}</dd>
                    </div>
                    <div class="sm:col-span-2">
                        <dt class="text-sm font-medium text-gray-500">Selectors</dt>
                        <dd class="mt-1 text-sm text-gray-900"><pre class="bg-gray-100 p-2 rounded text-xs">${JSON.stringify(scraper.config.selectors, null, 2)}</pre></dd>
                    </div>
                </dl>
            </div>

            <!-- Alerts Summary -->
            <div class="bg-white shadow rounded-lg p-6">
                <h3 class="text-lg font-medium text-gray-900 mb-2">Recent Alerts</h3>
                <div class="overflow-y-auto max-h-48">
                    ${renderAlertsList(alerts)}
                </div>
            </div>
        </div>

        <!-- Runs Table -->
        <div class="bg-white shadow rounded-lg overflow-hidden">
            <div class="px-4 py-5 sm:px-6 bg-gray-50 border-b border-gray-200">
                <h3 class="text-lg leading-6 font-medium text-gray-900">Run History</h3>
            </div>
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Items</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Error</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    ${runs && runs.map(run => `
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${new Date(run.timestamp).toLocaleString()}</td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${run.status === 'SUCCESS' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                                    ${run.status}
                                </span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${run.duration_ms.toFixed(0)}ms</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${run.items_extracted}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-red-500 truncate max-w-xs">${run.error_message || '-'}</td>
                        </tr>
                    `).join('') || '<tr><td colspan="5" class="text-center py-4 text-gray-500">No runs found</td></tr>'}
                </tbody>
            </table>
        </div>
    `;

    mainContent.innerHTML = html;
}

function renderAlertsList(alerts) {
    if (!alerts || alerts.length === 0) {
        return '<p class="text-sm text-gray-500">No alerts detected.</p>';
    }

    return alerts.map(alert => `
        <div class="mb-3 p-3 bg-red-50 border-l-4 border-red-500 rounded">
            <div class="flex justify-between">
                <span class="text-xs font-bold text-red-800 uppercase">${alert.type}</span>
                <span class="text-xs text-gray-500">${new Date(alert.timestamp).toLocaleTimeString()}</span>
            </div>
            <p class="text-sm text-red-700 mt-1">${alert.message}</p>
        </div>
    `).join('');
}

// Initial Load
loadView("scrapers");
