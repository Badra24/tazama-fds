document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadHistory();
    loadStats();
    setupEventListeners();
    startFraudAlertPolling();
});

const API = {
    checkHealth: '/api/health',
    stats: '/api/stats',
    pacs008: '/api/test/pacs008',
    fullTx: '/api/test/full-transaction',
    quickStatus: '/api/test/quick-status',
    batch: '/api/test/batch',
    velocity: '/api/test/velocity',
    creditor: '/api/test/velocity-creditor',
    attackScenario: '/api/test/attack-scenario',
    e2eFlow: '/api/test/e2e-flow',
    dbSummary: '/api/test/db-summary',
    logs: (container) => `/api/logs/${container}`,
    fraudAlerts: '/api/fraud-alerts',
    history: '/api/history'
};

function setupEventListeners() {
    // Velocity Test
    const velForm = document.getElementById('velocityTestForm');
    if (velForm) velForm.addEventListener('submit', (e) => handleAttackSimulation(e, API.velocity));

    // Creditor Test
    const credForm = document.getElementById('creditorTestForm');
    if (credForm) credForm.addEventListener('submit', (e) => handleAttackSimulation(e, API.creditor));

    // Advanced Attack
    const advForm = document.getElementById('advancedAttackForm');
    if (advForm) advForm.addEventListener('submit', (e) => {
        // Ensure scenario is set
        const select = document.getElementById('attackScenarioSelect');
        document.getElementById('hiddenScenarioInput').value = select.value;
        // Amount logic
        const amtInput = document.getElementById('adv_amount');
        // If empty, let backend handle it, else use value

        handleAttackSimulation(e, '/api/test/attack-scenario');
    });
}

// --- API Interactions ---

async function checkHealth() {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const statusBar = document.querySelector('.status-bar');

    // Get the button that triggered this (assuming it has onclick="checkHealth()")
    // Note: Since we call this on load too, we need to find it safely.
    const checkBtn = document.querySelector('button[onclick="checkHealth()"]');

    // 1. Vibration/Shake Effect
    if (checkBtn) {
        checkBtn.classList.remove('btn-shake'); // Reset
        void checkBtn.offsetWidth; // Trigger reflow
        checkBtn.classList.add('btn-shake');

        // 2. Aesthetic Loading State
        const originalContent = checkBtn.innerHTML;
        checkBtn.disabled = true;
        checkBtn.classList.add('btn-loading');
        checkBtn.innerHTML = `<span class="btn-spinner"></span> Checking...`;

        // Artificial delay (min 800ms) to show off the aesthetic loading
        // because sometimes localhost is too fast!
        await new Promise(r => setTimeout(r, 800));

        try {
            const response = await fetch(API.checkHealth);
            const data = await response.json();

            if (data.status === 'success') {
                statusDot.className = 'status-dot online';
                statusBar.classList.remove('status-error');

                // Handle both HTTP response and Docker container check
                let statusMessage = 'TMS Service Active';
                if (data.response_time_ms) {
                    statusMessage += ` • Response: ${data.response_time_ms.toFixed(0)}ms`;
                } else if (data.container_status) {
                    statusMessage = `Container ${data.container_status}`;
                } else if (data.message) {
                    statusMessage = data.message;
                }

                statusText.innerHTML = `
                    <div class="status-content">
                        <span class="status-main">System Online</span>
                        <span class="status-sub">${statusMessage}</span>
                    </div>
                `;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            statusDot.className = 'status-dot offline';
            statusBar.classList.add('status-error');

            statusText.innerHTML = `
                <div class="status-content">
                    <span class="status-main">Your Tazama Local Docker Is Offline</span>
                    <span class="status-sub">Action Required: Please run <code>tazama local</code> to start services</span>
                </div>
            `;
        } finally {
            // Restore button state
            if (checkBtn) {
                checkBtn.classList.remove('btn-loading');
                checkBtn.disabled = false;
                checkBtn.innerHTML = originalContent;
            }
        }
    }
}

async function loadDbSummary() {
    const content = document.getElementById('dbSummaryContent');
    const historyContent = document.getElementById('dbHistoryContent');
    const toggleIcon = document.getElementById('dbHistoryToggleIcon');

    // Auto-expand when loading
    if (historyContent) {
        historyContent.style.display = 'block';
        if (toggleIcon) toggleIcon.textContent = '▼';
    }

    content.innerHTML = '<em style="color: #94a3b8;">Loading...</em>';

    try {
        const response = await fetch(API.dbSummary);
        const data = await response.json();

        if (data.status === 'success') {
            let html = `<div style="margin-bottom: 0.75rem; color: #fff;"><strong>Total Transaksi: ${data.total_transactions}</strong></div>`;

            // Debtors table
            html += `<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">`;
            html += `<div>`;
            html += `<div style="font-weight: 600; margin-bottom: 0.5rem; color: #f87171;">👤 Debtor (Pengirim)</div>`;
            if (data.debtors && data.debtors.length > 0) {
                html += `<table style="width: 100%; font-size: 0.85rem; border-collapse: collapse;">`;
                html += `<tr style="background: rgba(255,255,255,0.1);"><th style="padding: 6px; text-align: left; color: #e2e8f0;">Account</th><th style="padding: 6px; text-align: right; color: #e2e8f0;">Tx</th></tr>`;
                data.debtors.forEach(d => {
                    const bgColor = d.tx_count >= 3 ? 'rgba(239, 68, 68, 0.2)' : 'transparent';
                    html += `<tr style="background: ${bgColor};"><td style="padding: 5px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #cbd5e1;">${d.account}</td><td style="padding: 5px; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1); color: #cbd5e1; font-weight: ${d.tx_count >= 3 ? '700' : '400'};">${d.tx_count}</td></tr>`;
                });
                html += `</table>`;
            } else {
                html += `<em style="color: #94a3b8;">Tidak ada data</em>`;
            }
            html += `</div>`;

            // Creditors table
            html += `<div>`;
            html += `<div style="font-weight: 600; margin-bottom: 0.5rem; color: #34d399;">🏦 Creditor (Penerima)</div>`;
            if (data.creditors && data.creditors.length > 0) {
                html += `<table style="width: 100%; font-size: 0.85rem; border-collapse: collapse;">`;
                html += `<tr style="background: rgba(255,255,255,0.1);"><th style="padding: 6px; text-align: left; color: #e2e8f0;">Account</th><th style="padding: 6px; text-align: right; color: #e2e8f0;">Tx</th></tr>`;
                data.creditors.forEach(c => {
                    const bgColor = c.tx_count >= 3 ? 'rgba(239, 68, 68, 0.2)' : 'transparent';
                    html += `<tr style="background: ${bgColor};"><td style="padding: 5px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #cbd5e1;">${c.account}</td><td style="padding: 5px; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1); color: #cbd5e1; font-weight: ${c.tx_count >= 3 ? '700' : '400'};">${c.tx_count}</td></tr>`;
                });
                html += `</table>`;
            } else {
                html += `<em style="color: #94a3b8;">Tidak ada data</em>`;
            }
            html += `</div></div>`;

            // Add hint
            html += `<div style="margin-top: 0.75rem; padding: 0.5rem; background: rgba(251, 191, 36, 0.1); border-radius: 6px; font-size: 0.8rem; color: #fbbf24;">💡 Highlight merah = sudah ≥3 transaksi (potensi trigger Rule 901/902)</div>`;

            content.innerHTML = html;
        } else {
            content.innerHTML = `<span style="color: #f87171;">Error: ${data.message}</span>`;
        }
    } catch (error) {
        content.innerHTML = `<span style="color: #f87171;">Error: ${error.message}</span>`;
    }
}

function toggleDbHistory() {
    const content = document.getElementById('dbHistoryContent');
    const icon = document.getElementById('dbHistoryToggleIcon');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.textContent = '▼';
    } else {
        content.style.display = 'none';
        icon.textContent = '▶';
    }
}

async function testPacs008() {
    const formData = new FormData();
    const acc = document.getElementById('debtorAccount008').value;
    const credAcc = document.getElementById('creditorAccount008').value;
    const amt = document.getElementById('amount008').value;

    if (acc) formData.append('debtor_account', acc);
    if (credAcc) formData.append('creditor_account', credAcc);
    if (amt) formData.append('amount', amt);

    await handleSimpleTest(API.pacs008, formData, 'response008', (data) => {
        if (data.payload_sent?.GrpHdr?.MsgId) {
            document.getElementById('messageId002').value = data.payload_sent.GrpHdr.MsgId;
        }
        // Always update fraud alerts (even if empty to clear old alerts)
        updateFraudAlerts(data.fraud_alerts || [], data.request_summary);
    });
}

async function testPacs002() {
    const msgId = document.getElementById('messageId002').value;
    if (!msgId) {
        alert('Please provide a Message ID first (run pacs.008 test)');
        return;
    }

    const formData = new FormData();
    formData.append('message_id', msgId);
    formData.append('status_code', document.getElementById('statusCode002').value);

    await handleSimpleTest(API.pacs002, formData, 'response002');
}

async function testFullTransaction() {
    const formData = new FormData();
    const acc = document.getElementById('debtorAccountFull').value;
    const amt = document.getElementById('amountFull').value;

    if (acc) formData.append('debtor_account', acc);
    if (amt) formData.append('amount', amt);

    await handleSimpleTest(API.fullTx, formData, 'responseFull');
}

async function testQuickStatus(statusCode) {
    const formData = new FormData();
    formData.append('status_code', statusCode);

    const amt = document.getElementById('quickAmount').value;
    if (amt) formData.append('amount', amt);

    await handleSimpleTest(API.quickStatus, formData, 'responseQuick');
}

async function testE2EFlow() {
    const progressBox = document.getElementById('e2eProgressBox');
    const responseBox = document.getElementById('responseE2E');
    const steps = ['step1', 'step2', 'step3', 'step4'];

    // Reset steps
    steps.forEach(stepId => {
        const stepEl = document.getElementById(stepId);
        if (stepEl) stepEl.querySelector('.step-icon').textContent = '⏳';
    });

    progressBox.style.display = 'block';
    responseBox.style.display = 'none';

    const formData = new FormData();
    formData.append('debtor_account', document.getElementById('e2eDebtorAccount').value);
    formData.append('creditor_account', document.getElementById('e2eCreditorAccount').value);
    formData.append('amount', document.getElementById('e2eAmount').value);
    formData.append('final_status', document.getElementById('e2eFinalStatus').value);

    showLoading(true);

    try {
        const response = await fetch(API.e2eFlow, { method: 'POST', body: formData });
        const data = await response.json();

        // Update step indicators based on results
        if (data.steps) {
            data.steps.forEach((step, index) => {
                const stepEl = document.getElementById(`step${index + 1}`);
                if (stepEl) {
                    const icon = stepEl.querySelector('.step-icon');
                    if (step.skipped) {
                        icon.textContent = '⏭️';
                    } else if (step.success) {
                        icon.textContent = '✅';
                    } else {
                        icon.textContent = '❌';
                    }
                }
            });
        }

        responseBox.style.display = 'block';
        responseBox.querySelector('pre').textContent = JSON.stringify(data, null, 2);

        loadHistory();
        loadStats();

    } catch (error) {
        responseBox.style.display = 'block';
        responseBox.querySelector('pre').textContent = `Error: ${error.message}`;
    } finally {
        showLoading(false);
    }
}

async function runFraudSimulation() {
    const progressBox = document.getElementById('fraudSimProgress');
    const summaryBox = document.getElementById('fraudSimSummary');
    const responseBox = document.getElementById('fraudSimResponse');
    const simSteps = document.querySelectorAll('#fraudSimSteps .sim-step');

    // Reset UI
    simSteps.forEach(step => {
        step.querySelector('.sim-icon').textContent = '⏳';
    });
    progressBox.style.display = 'block';
    summaryBox.style.display = 'none';
    responseBox.style.display = 'none';

    const formData = new FormData();
    formData.append('account_id', document.getElementById('simAccountId').value);
    formData.append('rule', document.getElementById('simRule').value);
    formData.append('attack_count', document.getElementById('simAttackCount').value);

    showLoading(true);

    try {
        const response = await fetch('/api/test/fraud-simulation', { method: 'POST', body: formData });
        const data = await response.json();

        // Update step icons based on results
        if (data.steps) {
            data.steps.forEach(step => {
                const stepEl = document.querySelector(`#fraudSimSteps .sim-step[data-step="${step.step}"]`);
                if (stepEl) {
                    stepEl.querySelector('.sim-icon').textContent = step.icon || (step.success ? '✅' : '❌');
                }
            });
        }

        // Show summary
        if (data.summary) {
            const summaryHtml = `
                <div style="margin-bottom: 0.5rem;"><strong>Rule:</strong> ${data.summary.rule_triggered || 'N/A'}</div>
                <div style="margin-bottom: 0.5rem;"><strong>Fraud Detected:</strong> ${data.fraud_detected ? '🚨 YES' : '👀 No'}</div>
                <div style="margin-bottom: 0.5rem;"><strong>Alerts:</strong> ${data.summary.alerts_count || 0}</div>
                <div style="margin-bottom: 0.5rem;"><strong>Status:</strong> ${data.summary.final_status || 'N/A'}</div>
                <div style="margin-top: 0.75rem; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.2);">
                    <strong>Condition:</strong> ${data.summary.trigger_condition || 'N/A'}
                </div>
                <div style="margin-top: 0.5rem;">
                    <strong>Recommendation:</strong> ${data.summary.recommendation || 'N/A'}
                </div>
            `;
            document.getElementById('fraudSummaryContent').innerHTML = summaryHtml;
            summaryBox.style.display = 'block';
        }

        // Show full response
        responseBox.style.display = 'block';
        responseBox.querySelector('pre').textContent = JSON.stringify(data, null, 2);

        // Also update the Fraud Activity Detected section with alerts
        if (data.fraud_alerts && data.fraud_alerts.length > 0) {
            updateFraudAlerts(data.fraud_alerts, { scenario: data.target_rule, account_id: data.account_id });
        }

        loadHistory();
        loadStats();

    } catch (error) {
        responseBox.style.display = 'block';
        responseBox.querySelector('pre').textContent = `Error: ${error.message}`;
    } finally {
        showLoading(false);
    }
}

// --- Generic Handlers ---

async function handleSimpleTest(url, formData, responseElemId, onSuccess) {
    showLoading(true);
    try {
        const response = await fetch(url, { method: 'POST', body: formData });
        const data = await response.json();

        displayJson(responseElemId, data);
        if (onSuccess) onSuccess(data);
        loadHistory();
    } catch (error) {
        displayJson(responseElemId, { error: error.message });
    } finally {
        showLoading(false);
    }
}

async function handleAttackSimulation(e, url) {
    e.preventDefault();
    const form = e.target;
    const btn = form.querySelector('button[type="submit"]');
    const responseBox = form.querySelector('.response-box');

    // UI Loading State
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border"></span> Simulating Attack...`;

    responseBox.style.display = 'block';
    responseBox.querySelector('pre').textContent = '🚀 Launching attack simulation... this may take a moment...';

    try {
        const formData = new FormData(form);
        const response = await fetch(url, { method: 'POST', body: formData });
        const data = await response.json();

        // Handle Fraud Alerts with request summary
        updateFraudAlerts(data.fraud_alerts, data.request_summary);

        // Display Summary
        const successCount = data.results ? data.results.filter(r => r.status === 200).length : 0;
        const total = data.total_sent || 0;

        let summary = {
            status: data.status,
            summary: `Sent ${total} transactions. Success: ${successCount}`,
            details: data.results
        };

        responseBox.querySelector('pre').textContent = JSON.stringify(summary, null, 2);
        loadHistory();

    } catch (error) {
        responseBox.querySelector('pre').textContent = `Error: ${error.message}`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// --- Helper Functions ---

function updateFraudAlerts(alerts, requestSummary) {
    const panel = document.getElementById('fraudAlertsPanel');
    const content = document.getElementById('fraudAlertsContent');

    if (!alerts || alerts.length === 0) {
        panel.style.display = 'none';
        return;
    }

    panel.style.display = 'block';

    // Store alerts globally for modal access
    window.currentFraudAlerts = alerts;
    window.currentRequestSummary = requestSummary;

    content.innerHTML = alerts.map((alert, index) => `
        <div class="fraud-alert-card" style="margin-bottom: 1rem; border: 2px solid #f59e0b; border-radius: 8px; padding: 1rem; background: #fffbeb;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                <div>
                    <div style="font-weight: bold; color: #b45309; font-size: 1.1em; margin-bottom: 0.25rem;">
                        ${alert.rule_id ? 'Rule ' + alert.rule_id : ''} ${alert.title}
                    </div>
                    <div style="color: #92400e; font-size: 0.95em;">${alert.desc}</div>
                </div>
                <span style="background: #dc2626; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold;">
                    ALERT
                </span>
            </div>
            
            ${alert.rule_detail ? `
            <div style="background: #fef3c7; padding: 0.75rem; border-radius: 6px; margin-bottom: 0.75rem;">
                <div style="font-weight: 600; color: #92400e; margin-bottom: 0.5rem;">Kenapa Ini Trigger:</div>
                <div style="color: #78350f; font-size: 0.9em;">${alert.rule_detail.why_triggered}</div>
            </div>
            ` : ''}
            
            ${alert.request_context ? `
            <div style="background: #e0f2fe; padding: 0.75rem; border-radius: 6px; margin-bottom: 0.75rem;">
                <div style="font-weight: 600; color: #0369a1; margin-bottom: 0.5rem;">Request Anda:</div>
                <div style="color: #0c4a6e; font-size: 0.9em;">
                    Debtor: ${alert.request_context.debtor_account || alert.request_context.debtor_name || '-'}<br>
                    ${alert.request_context.creditor_account ? 'Creditor: ' + alert.request_context.creditor_account + '<br>' : ''}
                    Amount: Rp ${(alert.request_context.amount_per_transaction || alert.request_context.amount_requested || 0).toLocaleString('id-ID')}<br>
                    Total Transaksi: ${alert.request_context.total_transactions || '-'}
                </div>
            </div>
            ` : ''}
            
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button onclick="showFraudAlertModal(${index})" 
                    style="background: #0891b2; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.85em;">
                    Lihat Detail Lengkap
                </button>
                <button onclick="toggleLogSnippet(${index})" 
                    style="background: #6b7280; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.85em;">
                    Lihat Log Container
                </button>
            </div>
            
            <div id="logSnippet${index}" style="display: none; margin-top: 0.75rem; background: #1f2937; color: #10b981; padding: 0.75rem; border-radius: 6px; font-family: monospace; font-size: 0.8em; overflow-x: auto;">
                ${alert.log_snippet || alert.raw}
            </div>
        </div>
    `).join('');
}

function toggleLogSnippet(index) {
    const snippet = document.getElementById('logSnippet' + index);
    snippet.style.display = snippet.style.display === 'none' ? 'block' : 'none';
}

function showFraudAlertModal(index) {
    const alert = window.currentFraudAlerts[index];
    const requestSummary = window.currentRequestSummary || alert.request_context;

    // Create modal if not exists
    let modal = document.getElementById('fraudAlertModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'fraudAlertModal';
        modal.className = 'fraud-modal-overlay';
        document.body.appendChild(modal);
    }

    const ruleDetail = alert.rule_detail || {};
    const config = ruleDetail.config || {};

    modal.innerHTML = `
        <div class="fraud-modal-content">
            <div class="fraud-modal-header">
                <h3 style="margin: 0; color: #dc2626;">Detail Alert: ${alert.title}</h3>
                <button onclick="closeFraudAlertModal()" style="background: none; border: none; font-size: 1.5em; cursor: pointer; color: #6b7280;">&times;</button>
            </div>
            
            <div class="fraud-modal-body">
                <div class="fraud-modal-section">
                    <h4 style="color: #0369a1; margin-bottom: 0.5rem;">Ringkasan</h4>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 6px 0; border-bottom: 1px solid #e5e7eb; color: #6b7280;">Rule ID</td><td style="padding: 6px 0; border-bottom: 1px solid #e5e7eb; font-weight: 600;">${alert.rule_id || '-'}</td></tr>
                        <tr><td style="padding: 6px 0; border-bottom: 1px solid #e5e7eb; color: #6b7280;">Nama Rule</td><td style="padding: 6px 0; border-bottom: 1px solid #e5e7eb; font-weight: 600;">${ruleDetail.name || alert.title}</td></tr>
                        <tr><td style="padding: 6px 0; border-bottom: 1px solid #e5e7eb; color: #6b7280;">Kondisi Trigger</td><td style="padding: 6px 0; border-bottom: 1px solid #e5e7eb;">${ruleDetail.trigger_condition || alert.desc}</td></tr>
                    </table>
                </div>
                
                <div class="fraud-modal-section" style="background: #fef3c7; padding: 1rem; border-radius: 8px;">
                    <h4 style="color: #b45309; margin-bottom: 0.5rem;">Kenapa Request Anda Mentrigger Alert Ini?</h4>
                    <p style="color: #78350f; margin: 0; line-height: 1.6;">${ruleDetail.why_triggered || 'Transaksi Anda sesuai dengan pola yang mencurigakan berdasarkan konfigurasi rule.'}</p>
                </div>
                
                ${requestSummary ? `
                <div class="fraud-modal-section" style="background: #e0f2fe; padding: 1rem; border-radius: 8px;">
                    <h4 style="color: #0369a1; margin-bottom: 0.5rem;">Detail Request Anda</h4>
                    <pre style="background: #0c4a6e; color: #7dd3fc; padding: 1rem; border-radius: 6px; overflow-x: auto; margin: 0; font-size: 0.85em;">${JSON.stringify(requestSummary, null, 2)}</pre>
                </div>
                ` : ''}
                
                <div class="fraud-modal-section" style="background: #f3f4f6; padding: 1rem; border-radius: 8px;">
                    <h4 style="color: #374151; margin-bottom: 0.5rem;">Konfigurasi Rule</h4>
                    <pre style="background: #1f2937; color: #10b981; padding: 1rem; border-radius: 6px; overflow-x: auto; margin: 0; font-size: 0.85em;">${JSON.stringify(config, null, 2)}</pre>
                </div>
                
                <div class="fraud-modal-section" style="background: #1f2937; padding: 1rem; border-radius: 8px;">
                    <h4 style="color: #10b981; margin-bottom: 0.5rem;">Log Container</h4>
                    <pre style="color: #d1d5db; margin: 0; font-size: 0.8em; white-space: pre-wrap; word-break: break-all;">${alert.log_snippet || alert.raw}</pre>
                </div>
                
                ${ruleDetail.recommendation ? `
                <div class="fraud-modal-section" style="background: #fce7f3; padding: 1rem; border-radius: 8px;">
                    <h4 style="color: #be185d; margin-bottom: 0.5rem;">Rekomendasi</h4>
                    <p style="color: #9d174d; margin: 0;">${ruleDetail.recommendation}</p>
                </div>
                ` : ''}
            </div>
        </div>
    `;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeFraudAlertModal() {
    const modal = document.getElementById('fraudAlertModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Close modal on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeFraudAlertModal();
});


async function loadHistory() {
    try {
        const response = await fetch(API.history);
        const data = await response.json();
        const container = document.getElementById('historyContainer');
        const msgIdInput = document.getElementById('messageId002');

        // Auto-populate Message ID from last successful pacs.008 (if input exists)
        if (msgIdInput && data.history && data.history.length > 0) {
            // Find last successful pacs.008
            const lastPacs008 = data.history.slice().reverse().find(
                item => item.type === 'pacs.008' && item.success && item.message_id
            );

            if (lastPacs008 && !msgIdInput.value) {
                msgIdInput.value = lastPacs008.message_id;
                msgIdInput.title = "Auto-filled from last successful transaction";
                msgIdInput.style.borderColor = 'var(--secondary-color)';
            }
        }

        if (!data.history || data.history.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted); text-align: center;">No tests run yet</p>';
            return;
        }

        container.innerHTML = data.history.slice().reverse().map(item => `
            <div class="history-item ${item.success ? 'success' : 'error'}">
                <div class="history-header">
                    <strong>${item.type}</strong>
                    <span class="badge ${item.success ? 'badge-success' : 'badge-error'}">
                        ${item.success ? 'SUCCESS' : 'FAILED'}
                    </span>
                </div>
                <div class="history-meta">
                    <span>ID: ${item.message_id || 'N/A'}</span>
                    <span>${item.response_time_ms ? item.response_time_ms.toFixed(1) + 'ms' : '-'}</span>
                    <span>${new Date(item.timestamp).toLocaleTimeString()}</span>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed to load history', e);
    }
}

async function clearHistory() {
    if (confirm('Are you sure you want to clear the test history?')) {
        await fetch(API.history, { method: 'DELETE' });
        loadHistory();
    }
}

async function checkInternalLogs(container, boxId, textId) {
    const box = document.getElementById(boxId);
    const text = document.getElementById(textId);

    box.style.display = 'block';
    text.textContent = 'Fetching logs...';

    try {
        const response = await fetch(API.logs(container));
        const data = await response.json();

        text.textContent = data.status === 'success' ? data.logs : `Error: ${data.message}`;
    } catch (error) {
        text.textContent = `Failed to fetch logs: ${error.message}`;
    }
}

function displayJson(elemId, data) {
    const box = document.getElementById(elemId);
    box.style.display = 'block';
    box.querySelector('pre').textContent = JSON.stringify(data, null, 2);
}

function showLoading(show) {
    document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
}

function updateScenarioDesc() {
    const select = document.getElementById('attackScenarioSelect');
    const desc = document.getElementById('scenarioDescription');
    const amountInput = document.getElementById('adv_amount');
    const amountHint = document.getElementById('amountHint');
    const countInput = document.getElementById('adv_count');
    const val = select.value;

    if (val === 'rule_006') {
        desc.innerHTML = "ℹ️ <strong>Structuring/Smurfing:</strong> Mengirim beberapa transaksi dengan nominal mirip untuk menghindari threshold audit.<br>" +
            "<span style='color:#dc2626;'>⚠️ Konfigurasi saat ini: tolerance 20%, minimal 5 transaksi mirip untuk trigger.</span>";
        amountInput.placeholder = "9500000";
        amountHint.innerHTML = "💡 Recommended: <strong>9,500,000</strong> (nominal sama untuk trigger structuring)";
        countInput.value = "6";
    } else if (val === 'rule_018') {
        desc.innerHTML = "ℹ️ <strong>High Value Transfer:</strong> Mendeteksi transaksi yang melebihi 1.5x rata-rata historical.<br>" +
            "<span style='color:#dc2626;'>⚠️ PENTING: Rule ini MEMBUTUHKAN historical data! Minimal 6 transaksi (5 kecil + 1 besar).</span><br>" +
            "<span style='color:#0369a1;'>📊 Sistem akan menghitung rata-rata dari 5 transaksi pertama, lalu membandingkan dengan transaksi ke-6.</span>";
        amountInput.placeholder = "500000000";
        amountHint.innerHTML = "💡 Recommended: <strong>500,000,000</strong> (500 juta - transaksi besar sebagai trigger)";
        countInput.value = "6";
    } else if (val === 'rule_901') {
        desc.innerHTML = "ℹ️ <strong>Velocity Check (Debtor):</strong> Mendeteksi debtor yang mengirim terlalu banyak transaksi dalam 1 hari.<br>" +
            "<span style='color:#0369a1;'>📊 Threshold: 3 atau lebih transaksi per hari dari debtor yang sama.</span>";
        amountInput.placeholder = "500000";
        amountHint.innerHTML = "💡 Amount bervariasi otomatis untuk menghindari trigger Rule 006";
        countInput.value = "5";
    } else if (val === 'rule_902') {
        desc.innerHTML = "ℹ️ <strong>Money Mule (Creditor):</strong> Mendeteksi creditor yang menerima dana dari banyak pengirim berbeda.<br>" +
            "<span style='color:#0369a1;'>📊 Threshold: 3 atau lebih transaksi dari debtor berbeda ke creditor yang sama.</span>";
        amountInput.placeholder = "500000";
        amountHint.innerHTML = "💡 Amount bervariasi otomatis untuk menghindari trigger Rule 006";
        countInput.value = "5";
    }
}

// Initialize Scenario Desc
document.addEventListener('DOMContentLoaded', updateScenarioDesc);

// --- Stats Dashboard ---
async function loadStats() {
    try {
        const response = await fetch(API.stats);
        const data = await response.json();

        document.getElementById('statTotal').textContent = data.total_tests || 0;
        document.getElementById('statSuccess').textContent = data.success_count || 0;
        document.getElementById('statFailed').textContent = data.failure_count || 0;
        document.getElementById('statRate').textContent = (data.success_rate || 0) + '%';
        document.getElementById('statAvgTime').textContent = Math.round(data.avg_response_time_ms || 0) + 'ms';
    } catch (e) {
        console.error('Failed to load stats', e);
    }
}

// --- Batch Testing ---
async function runBatchTest() {
    const scenarios = [];

    if (document.getElementById('batch_quick_accc')?.checked) scenarios.push('quick_accc');
    if (document.getElementById('batch_quick_acsc')?.checked) scenarios.push('quick_acsc');
    if (document.getElementById('batch_quick_rjct')?.checked) scenarios.push('quick_rjct');
    if (document.getElementById('batch_rule_901')?.checked) scenarios.push('rule_901');
    if (document.getElementById('batch_rule_902')?.checked) scenarios.push('rule_902');
    if (document.getElementById('batch_rule_006')?.checked) scenarios.push('rule_006');
    if (document.getElementById('batch_rule_018')?.checked) scenarios.push('rule_018');

    if (scenarios.length === 0) {
        alert('Please select at least one scenario');
        return;
    }

    const resultsBox = document.getElementById('batchResults');
    resultsBox.style.display = 'block';
    resultsBox.querySelector('pre').textContent = '🚀 Running batch test... This may take a moment...';

    showLoading(true);

    try {
        const formData = new FormData();
        formData.append('scenarios', scenarios.join(','));

        const response = await fetch(API.batch, { method: 'POST', body: formData });
        const data = await response.json();

        resultsBox.querySelector('pre').textContent = JSON.stringify(data, null, 2);
        loadHistory();
        loadStats();
    } catch (e) {
        resultsBox.querySelector('pre').textContent = 'Error: ' + e.message;
    } finally {
        showLoading(false);
    }
}

// --- Auto-refresh Fraud Alerts (DISABLED) ---
// This was overwriting detailed alerts with basic ones from separate endpoint
// Keeping code for reference but not using it

let fraudAlertInterval = null;

function startFraudAlertPolling() {
    // DISABLED: This was causing detailed alerts to be replaced by basic ones
    // The issue is that API.fraudAlerts returns alerts without request_context
    // So the detailed explanation gets lost

    // Original code (disabled):
    // fraudAlertInterval = setInterval(async () => {
    //     try {
    //         const response = await fetch(API.fraudAlerts);
    //         const data = await response.json();
    //         if (data.fraud_alerts && data.fraud_alerts.length > 0) {
    //             updateFraudAlerts(data.fraud_alerts);
    //         }
    //     } catch (e) {
    //         // Silent fail
    //     }
    // }, 10000);
}

function stopFraudAlertPolling() {
    if (fraudAlertInterval) {
        clearInterval(fraudAlertInterval);
        fraudAlertInterval = null;
    }
}
