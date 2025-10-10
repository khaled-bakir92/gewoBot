/**
 * GEWOBAG BOT - FRONTEND APPLICATION
 * Main JavaScript file for the web interface
 */

// ============================================================================
// GLOBAL VARIABLES & CONFIG
// ============================================================================

const API_BASE_URL = 'http://localhost:8080/api';
let statusUpdateInterval = null;
let availableBezirke = [];

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Gewobag Bot Frontend initialized');

    // Initialize navigation
    initNavigation();

    // Load initial data
    loadDashboard();
    loadUserData();
    loadFilterConfig();
    loadBezirke();

    // Setup form handlers
    setupFormHandlers();

    // Start status polling
    startStatusPolling();

    // Setup WBS checkbox toggle
    setupWBSToggle();
});

// ============================================================================
// NAVIGATION
// ============================================================================

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });
}

function switchTab(tabName) {
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');

    // Load tab-specific data
    if (tabName === 'dashboard') {
        loadDashboard();
    } else if (tabName === 'applications') {
        loadAllApplications();
    }
}

// ============================================================================
// DASHBOARD
// ============================================================================

async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/statistics`);
        const data = await response.json();

        // Update statistics
        document.getElementById('statTotal').textContent = data.stats.total;
        document.getElementById('statApplied').textContent = data.stats.applied;
        document.getElementById('statSuccess').textContent = data.stats.success;
        document.getElementById('statFailed').textContent = data.stats.failed;

        // Update recent applications
        displayRecentApplications(data.recent_applications);
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Fehler beim Laden des Dashboards', 'error');
    }
}

function displayRecentApplications(applications) {
    const container = document.getElementById('recentApplications');

    if (!applications || applications.length === 0) {
        container.innerHTML = '<p class="placeholder">Keine Bewerbungen vorhanden</p>';
        return;
    }

    container.innerHTML = applications.map(app => `
        <div class="application-item ${app.status}">
            <div class="application-header">
                <div>
                    <div class="application-title">${app.titel || 'Unbekannt'}</div>
                    <div class="application-address">${app.adresse || 'Keine Adresse'}</div>
                </div>
                <span class="application-badge ${app.status}">
                    ${app.status === 'success' ? '✓ Erfolgreich' : '✗ Fehlgeschlagen'}
                </span>
            </div>
            <div class="application-details">
                <span>📍 ${app.bezirk || '-'}</span>
                <span>🏠 ${app.zimmer || '-'}</span>
                <span>📐 ${app.flaeche || '-'}</span>
                <span>💰 ${app.miete || '-'}</span>
            </div>
            ${app.error ? `<div style="color: var(--danger-color); font-size: 0.875rem; margin-top: 0.5rem;">⚠️ ${app.error}</div>` : ''}
        </div>
    `).join('');
}

// ============================================================================
// USER DATA
// ============================================================================

async function loadUserData() {
    try {
        const response = await fetch(`${API_BASE_URL}/user-data`);
        const data = await response.json();

        // Populate form with data
        populateFormFromObject('userDataForm', data);

    } catch (error) {
        console.error('Error loading user data:', error);
        showNotification('Fehler beim Laden der Benutzerdaten', 'error');
    }
}

async function saveUserData(event) {
    event.preventDefault();

    try {
        const formData = getFormDataAsObject('userDataForm');

        const response = await fetch(`${API_BASE_URL}/user-data`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Benutzerdaten erfolgreich gespeichert', 'success');
        } else {
            showNotification('Fehler beim Speichern: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('Error saving user data:', error);
        showNotification('Fehler beim Speichern der Benutzerdaten', 'error');
    }
}

// ============================================================================
// FILTER CONFIG
// ============================================================================

async function loadBezirke() {
    try {
        const response = await fetch(`${API_BASE_URL}/bezirke`);
        const data = await response.json();

        availableBezirke = data.bezirke || [];
        displayBezirkeCheckboxes(availableBezirke);

    } catch (error) {
        console.error('Error loading bezirke:', error);
    }
}

function displayBezirkeCheckboxes(bezirke) {
    const container = document.getElementById('bezirkeCheckboxes');

    if (!bezirke || bezirke.length === 0) {
        container.innerHTML = '<p class="placeholder">Keine Bezirke verfügbar</p>';
        return;
    }

    // Gruppiere Bezirke nach Hauptbezirk
    const grouped = {};
    const seen = new Set();

    bezirke.forEach(bezirk => {
        const value = typeof bezirk === 'string' ? bezirk : bezirk.value;
        const name = typeof bezirk === 'string' ? bezirk : bezirk.name;
        const typ = typeof bezirk === 'object' ? bezirk.typ : '';

        // Duplikate vermeiden (case-insensitive)
        const uniqueKey = value.toLowerCase();
        if (seen.has(uniqueKey)) {
            return;
        }
        seen.add(uniqueKey);

        if (typ === 'Hauptbezirk') {
            // Hauptbezirk
            const hauptbezirkKey = name.trim();
            if (!grouped[hauptbezirkKey]) {
                grouped[hauptbezirkKey] = {
                    value: value,
                    name: name,
                    ortsteile: []
                };
            }
        } else if (typ === 'Ortsteil') {
            // Finde den Hauptbezirk
            const parts = value.split('-');
            const hauptbezirkSlug = parts[0];

            // Suche den passenden Hauptbezirk
            const hauptbezirkEntry = bezirke.find(b =>
                typeof b === 'object' &&
                b.typ === 'Hauptbezirk' &&
                b.value.toLowerCase().includes(hauptbezirkSlug.toLowerCase())
            );

            if (hauptbezirkEntry) {
                const hauptbezirkKey = hauptbezirkEntry.name.trim();
                if (!grouped[hauptbezirkKey]) {
                    grouped[hauptbezirkKey] = {
                        value: hauptbezirkEntry.value,
                        name: hauptbezirkEntry.name,
                        ortsteile: []
                    };
                }
                grouped[hauptbezirkKey].ortsteile.push({
                    value: value,
                    name: name
                });
            }
        }
    });

    // Erstelle HTML mit Hauptbezirken und Ortsteilen
    let html = '';

    Object.keys(grouped).sort().forEach(hauptbezirkName => {
        const bezirk = grouped[hauptbezirkName];

        html += `
            <div class="bezirk-group">
                <label class="bezirk-hauptbezirk">
                    <input type="checkbox" name="bezirk" value="${bezirk.value}" class="bezirk-checkbox hauptbezirk-checkbox" data-hauptbezirk="${bezirk.value}">
                    <strong>${bezirk.name}</strong>
                </label>
        `;

        // Ortsteile eingerückt anzeigen
        if (bezirk.ortsteile.length > 0) {
            bezirk.ortsteile.sort((a, b) => a.name.localeCompare(b.name)).forEach(ortsteil => {
                html += `
                    <label class="bezirk-ortsteil">
                        <input type="checkbox" name="bezirk" value="${ortsteil.value}" class="bezirk-checkbox ortsteil-checkbox" data-parent="${bezirk.value}">
                        ${ortsteil.name}
                    </label>
                `;
            });
        }

        html += '</div>';
    });

    container.innerHTML = html;

    // Event Listener für Hauptbezirke (selektiert alle Ortsteile)
    document.querySelectorAll('.hauptbezirk-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const hauptbezirkValue = this.getAttribute('data-hauptbezirk');
            const ortsteileCheckboxes = document.querySelectorAll(`.ortsteil-checkbox[data-parent="${hauptbezirkValue}"]`);
            ortsteileCheckboxes.forEach(cb => {
                cb.checked = this.checked;
            });
        });
    });
}

async function loadFilterConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/filter-config`);
        const data = await response.json();

        // Set simple fields
        document.getElementById('mieteVon').value = data.gesamtmiete_von || '';
        document.getElementById('mieteBis').value = data.gesamtmiete_bis || '';
        document.getElementById('flaecheVon').value = data.gesamtflaeche_von || '';
        document.getElementById('flaecheBis').value = data.gesamtflaeche_bis || '';
        document.getElementById('zimmerVon').value = data.zimmer_von || '';
        document.getElementById('zimmerBis').value = data.zimmer_bis || '';
        document.getElementById('wbsFilter').value = data.wbs || '';

        // Set bezirke checkboxes
        const selectedBezirke = data.gewuenschte_bezirke || [];

        // Warte kurz, damit die Checkboxen geladen sind
        setTimeout(() => {
            document.querySelectorAll('.bezirk-checkbox').forEach(checkbox => {
                // Prüfe ob der Wert in der Liste ist (case-insensitive)
                checkbox.checked = selectedBezirke.some(selected =>
                    selected.toLowerCase() === checkbox.value.toLowerCase()
                );
            });
        }, 100);

    } catch (error) {
        console.error('Error loading filter config:', error);
        showNotification('Fehler beim Laden der Filter-Konfiguration', 'error');
    }
}

async function saveFilterConfig(event) {
    event.preventDefault();

    try {
        // Get selected bezirke
        const selectedBezirke = Array.from(document.querySelectorAll('.bezirk-checkbox:checked'))
            .map(cb => cb.value);

        const filterData = {
            gewuenschte_bezirke: selectedBezirke,
            gesamtmiete_von: document.getElementById('mieteVon').value,
            gesamtmiete_bis: document.getElementById('mieteBis').value,
            gesamtflaeche_von: document.getElementById('flaecheVon').value,
            gesamtflaeche_bis: document.getElementById('flaecheBis').value,
            zimmer_von: document.getElementById('zimmerVon').value,
            zimmer_bis: document.getElementById('zimmerBis').value,
            wbs: document.getElementById('wbsFilter').value
        };

        const response = await fetch(`${API_BASE_URL}/filter-config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(filterData)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Filter erfolgreich gespeichert', 'success');
        } else {
            showNotification('Fehler beim Speichern: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('Error saving filter config:', error);
        showNotification('Fehler beim Speichern der Filter-Konfiguration', 'error');
    }
}

// ============================================================================
// BOT CONTROL
// ============================================================================

async function startBot() {
    try {
        const mode = document.getElementById('botModeSelect').value;
        const maxApplications = document.getElementById('maxApplications').value;

        const payload = {
            mode: mode
        };

        if (maxApplications) {
            payload.max_applications = parseInt(maxApplications);
        }

        const response = await fetch(`${API_BASE_URL}/bot/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Bot erfolgreich gestartet', 'success');
            updateBotControls(true, false);
        } else {
            showNotification('Fehler: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('Error starting bot:', error);
        showNotification('Fehler beim Starten des Bots', 'error');
    }
}

async function stopBot() {
    try {
        const response = await fetch(`${API_BASE_URL}/bot/stop`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Bot gestoppt', 'success');
            updateBotControls(false, false);
        } else {
            showNotification('Fehler: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('Error stopping bot:', error);
        showNotification('Fehler beim Stoppen des Bots', 'error');
    }
}

async function pauseBot() {
    try {
        const response = await fetch(`${API_BASE_URL}/bot/pause`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Bot pausiert', 'warning');
            updateBotControls(true, true);
        } else {
            showNotification('Fehler: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('Error pausing bot:', error);
        showNotification('Fehler beim Pausieren des Bots', 'error');
    }
}

async function resumeBot() {
    try {
        const response = await fetch(`${API_BASE_URL}/bot/resume`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Bot fortgesetzt', 'success');
            updateBotControls(true, false);
        } else {
            showNotification('Fehler: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('Error resuming bot:', error);
        showNotification('Fehler beim Fortsetzen des Bots', 'error');
    }
}

function updateBotControls(running, paused) {
    const pauseBtn = document.getElementById('pauseBtn');
    const resumeBtn = document.getElementById('resumeBtn');
    const stopBtn = document.getElementById('stopBtn');

    if (running && !paused) {
        pauseBtn.disabled = false;
        stopBtn.disabled = false;
        pauseBtn.style.display = 'inline-flex';
        resumeBtn.style.display = 'none';
    } else if (running && paused) {
        pauseBtn.style.display = 'none';
        resumeBtn.style.display = 'inline-flex';
        resumeBtn.disabled = false;
        stopBtn.disabled = false;
    } else {
        pauseBtn.disabled = true;
        resumeBtn.disabled = true;
        stopBtn.disabled = true;
        pauseBtn.style.display = 'inline-flex';
        resumeBtn.style.display = 'none';
    }
}

// ============================================================================
// STATUS POLLING
// ============================================================================

function startStatusPolling() {
    // Initial update
    updateBotStatus();

    // Poll every 2 seconds
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
    }
    statusUpdateInterval = setInterval(updateBotStatus, 2000);
}

async function updateBotStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/bot/status`);
        const data = await response.json();

        // Update status indicator
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = statusIndicator.querySelector('.status-text');

        statusIndicator.className = 'status-indicator';

        if (data.status.running && !data.status.paused) {
            statusIndicator.classList.add('running');
            statusText.textContent = data.status.message || 'Bot läuft';
        } else if (data.status.paused) {
            statusIndicator.classList.add('paused');
            statusText.textContent = 'Bot pausiert';
        } else {
            statusText.textContent = 'Bot gestoppt';
        }

        // Update bot status card
        document.getElementById('botStatusText').textContent =
            data.status.running ? (data.status.paused ? 'Pausiert' : 'Läuft') : 'Gestoppt';
        document.getElementById('botMode').textContent =
            data.status.mode || '-';
        document.getElementById('botStarted').textContent =
            data.status.started_at ? formatDateTime(data.status.started_at) : '-';
        document.getElementById('botLastActivity').textContent =
            data.status.last_activity ? formatDateTime(data.status.last_activity) : '-';

        // Update controls
        updateBotControls(data.status.running, data.status.paused);

        // Update stats if on dashboard OR control tab
        const isDashboardActive = document.getElementById('dashboard').classList.contains('active');
        const isControlActive = document.getElementById('control').classList.contains('active');

        if (isDashboardActive || isControlActive) {
            document.getElementById('statTotal').textContent = data.stats.total;
            document.getElementById('statApplied').textContent = data.stats.applied;
            document.getElementById('statSuccess').textContent = data.stats.success;
            document.getElementById('statFailed').textContent = data.stats.failed;

            // Update control tab stats
            if (isControlActive) {
                document.getElementById('statTotalControl').textContent = data.stats.total;
                document.getElementById('statAppliedControl').textContent = data.stats.applied;
                document.getElementById('statSuccessControl').textContent = data.stats.success;
                document.getElementById('statPendingControl').textContent = data.stats.pending || 0;

                // Load recent findings if bot is running or just finished
                if (data.status.running || (!data.status.running && window.lastBotRunning)) {
                    loadRecentFindings();
                }
            }

            // Reload dashboard if bot just finished running
            if (isDashboardActive && !data.status.running && window.lastBotRunning) {
                loadDashboard(); // Reload recent applications
            }
        }

        // Store last running state
        window.lastBotRunning = data.status.running;

    } catch (error) {
        console.error('Error updating status:', error);
    }
}

// ============================================================================
// RECENT FINDINGS (for Control Tab)
// ============================================================================

async function loadRecentFindings() {
    try {
        const response = await fetch(`${API_BASE_URL}/applications/recent?limit=10`);
        const applications = await response.json();

        displayRecentFindings(applications);

    } catch (error) {
        console.error('Error loading recent findings:', error);
    }
}

function displayRecentFindings(applications) {
    const container = document.getElementById('recentFindings');

    if (!applications || applications.length === 0) {
        container.innerHTML = '<p class="placeholder">Keine neuen Wohnungen gefunden</p>';
        return;
    }

    // Zeige die neuesten Wohnungen (nicht nur die beworbenen)
    // Hole alle Wohnungen sortiert nach Datum
    fetch(`${API_BASE_URL}/applications/all`)
        .then(response => response.json())
        .then(allApps => {
            // Sortiere nach ID (neueste zuerst)
            const recentApps = allApps.slice(0, 10);

            container.innerHTML = recentApps.map(app => {
                const statusClass = app.applied ? (app.status === 'success' ? 'success' : 'failed') : '';
                const statusBadge = app.applied
                    ? `<span class="application-badge ${app.status}">${app.status === 'success' ? '✓ Beworben' : '✗ Fehler'}</span>`
                    : '<span class="application-badge" style="background: #fef3c7; color: #92400e;">Neu gefunden</span>';

                return `
                    <div class="application-item ${statusClass}">
                        <div class="application-header">
                            <div>
                                <div class="application-title">${app.titel || 'Unbekannt'}</div>
                                <div class="application-address">${app.adresse || 'Keine Adresse'}</div>
                            </div>
                            ${statusBadge}
                        </div>
                        <div class="application-details">
                            <span>📍 ${app.bezirk || '-'}</span>
                            <span>🏠 ${app.zimmer || '-'}</span>
                            <span>📐 ${app.flaeche || '-'}</span>
                            <span>💰 ${app.miete || '-'}</span>
                        </div>
                    </div>
                `;
            }).join('');
        })
        .catch(error => {
            console.error('Error loading all applications:', error);
            container.innerHTML = '<p class="placeholder">Fehler beim Laden der Wohnungen</p>';
        });
}

// ============================================================================
// APPLICATIONS TABLE
// ============================================================================

async function loadAllApplications() {
    try {
        const response = await fetch(`${API_BASE_URL}/applications/all`);
        const applications = await response.json();

        displayApplicationsTable(applications);

    } catch (error) {
        console.error('Error loading applications:', error);
        showNotification('Fehler beim Laden der Bewerbungen', 'error');
    }
}

function displayApplicationsTable(applications) {
    const tbody = document.querySelector('#applicationsTable tbody');

    if (!applications || applications.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="placeholder">Keine Wohnungen gefunden</td></tr>';
        return;
    }

    tbody.innerHTML = applications.map(app => `
        <tr>
            <td>${app.titel || '-'}</td>
            <td>${app.adresse || '-'}</td>
            <td>${app.bezirk || '-'}</td>
            <td>${app.zimmer || '-'}</td>
            <td>${app.flaeche || '-'}</td>
            <td>${app.miete || '-'}</td>
            <td>
                ${app.applied
                    ? `<span class="status-badge ${app.status}">${getStatusText(app.status)}</span>`
                    : '<span class="status-badge pending">Nicht beworben</span>'
                }
            </td>
            <td>${app.timestamp ? formatDateTime(app.timestamp) : '-'}</td>
        </tr>
    `).join('');
}

function getStatusText(status) {
    switch(status) {
        case 'success': return '✓ Erfolgreich';
        case 'failed': return '✗ Fehlgeschlagen';
        default: return 'Ausstehend';
    }
}

// ============================================================================
// FORM HELPERS
// ============================================================================

function setupFormHandlers() {
    document.getElementById('userDataForm').addEventListener('submit', saveUserData);
    document.getElementById('filterForm').addEventListener('submit', saveFilterConfig);
}

function setupWBSToggle() {
    const wbsCheckbox = document.getElementById('wbsVorhanden');
    const wbsDetails = document.getElementById('wbsDetails');

    wbsCheckbox.addEventListener('change', function() {
        wbsDetails.style.display = this.checked ? 'grid' : 'none';
    });
}

function getFormDataAsObject(formId) {
    const form = document.getElementById(formId);
    const formData = new FormData(form);
    const result = {};

    for (const [key, value] of formData.entries()) {
        setNestedProperty(result, key, value);
    }

    // Handle checkboxes
    const checkboxes = form.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        const key = checkbox.name;
        const value = checkbox.checked;
        setNestedProperty(result, key, value);
    });

    return result;
}

function populateFormFromObject(formId, data) {
    const form = document.getElementById(formId);

    // Helper to set form field value
    function setFieldValue(name, value) {
        const elements = form.querySelectorAll(`[name="${name}"]`);
        elements.forEach(element => {
            if (element.type === 'checkbox') {
                element.checked = value;
                // Trigger change event for WBS toggle
                if (element.id === 'wbsVorhanden') {
                    element.dispatchEvent(new Event('change'));
                }
            } else if (element.type === 'radio') {
                element.checked = element.value === value;
            } else {
                element.value = value;
            }
        });
    }

    // Recursively populate fields
    function populateFields(obj, prefix = '') {
        for (const [key, value] of Object.entries(obj)) {
            const fieldName = prefix ? `${prefix}.${key}` : key;

            if (value && typeof value === 'object' && !Array.isArray(value)) {
                populateFields(value, fieldName);
            } else {
                setFieldValue(fieldName, value);
            }
        }
    }

    populateFields(data);
}

function setNestedProperty(obj, path, value) {
    const keys = path.split('.');
    let current = obj;

    for (let i = 0; i < keys.length - 1; i++) {
        const key = keys[i];
        if (!current[key] || typeof current[key] !== 'object') {
            current[key] = {};
        }
        current = current[key];
    }

    const lastKey = keys[keys.length - 1];

    // Convert string numbers to actual numbers
    if (!isNaN(value) && value !== '') {
        current[lastKey] = Number(value);
    } else {
        current[lastKey] = value;
    }
}

// ============================================================================
// NOTIFICATIONS
// ============================================================================

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;

    const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : type === 'warning' ? '⚠' : 'ℹ';
    const title = type === 'success' ? 'Erfolg' : type === 'error' ? 'Fehler' : type === 'warning' ? 'Warnung' : 'Info';

    notification.innerHTML = `
        <div class="notification-icon">${icon}</div>
        <div class="notification-content">
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
        </div>
    `;

    container.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// ============================================================================
// BEZIRKE SELECTION HELPERS
// ============================================================================

function selectAllBezirke() {
    document.querySelectorAll('.bezirk-checkbox').forEach(checkbox => {
        checkbox.checked = true;
    });
    showNotification('Alle Bezirke ausgewählt', 'success');
}

function deselectAllBezirke() {
    document.querySelectorAll('.bezirk-checkbox').forEach(checkbox => {
        checkbox.checked = false;
    });
    showNotification('Alle Bezirke abgewählt', 'info');
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function formatDateTime(dateString) {
    if (!dateString) return '-';

    try {
        const date = new Date(dateString);
        return date.toLocaleString('de-DE', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        return dateString;
    }
}

// ============================================================================
// CLEANUP
// ============================================================================

window.addEventListener('beforeunload', function() {
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
    }
});
