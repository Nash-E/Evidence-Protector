'use strict';
let currentAnalysisFileId = null;

function calcIntegrityScore(gaps, metadata) {
    if (!gaps || gaps.length === 0) return 100;
    const totalSec = metadata.total_log_seconds;
    if (!totalSec || totalSec === 0) return 100;
    const gapTimeSec = gaps.reduce((s, g) => s + g.duration_seconds, 0);
    const timeRatio = Math.min(gapTimeSec / totalSec, 1.0);

    const criticalCount = gaps.filter(g => g.severity_label === 'CRITICAL').length;
    const highCount     = gaps.filter(g => g.severity_label === 'HIGH').length;
    const medCount      = gaps.filter(g => g.severity_label === 'MEDIUM').length;
    const penalty = (timeRatio * 50) + (criticalCount * 15) + (highCount * 8) + (medCount * 3);
    return Math.max(0, Math.round(100 - penalty));
}

function renderGauge(score) {
    const color = score >= 90 ? '#10b981'
                : score >= 70 ? '#4f46e5'
                : score >= 40 ? '#f59e0b'
                : '#ef4444';
    const label = score >= 90 ? 'Highly Intact'
                : score >= 70 ? 'Mostly Intact'
                : score >= 40 ? 'Suspicious'
                : 'Compromised';

    const cx = 120, cy = 110, r = 80;
    const strokeWidth = 16;

    const angle = (score / 100) * 180;
    const rad   = (angle - 180) * Math.PI / 180;
    const x = cx + r * Math.cos(rad);
    const y = cy + r * Math.sin(rad);
    const largeArc = angle > 180 ? 1 : 0;

    const scorePath = score === 0
        ? ''
        : `<path d="M ${cx - r} ${cy} A ${r} ${r} 0 ${largeArc} 1 ${x} ${y}"
                 fill="none" stroke="${color}" stroke-width="${strokeWidth}"
                 stroke-linecap="round" style="transition: stroke-dashoffset 0.8s ease;"/>`;
    const svg = `
<svg viewBox="0 0 240 130" width="240" height="130" xmlns="http://www.w3.org/2000/svg">
  <path d="M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}"
        fill="none" stroke="#e5e7eb" stroke-width="${strokeWidth}" stroke-linecap="round"/>
  ${scorePath}
  <text x="${cx}" y="${cy - 10}" text-anchor="middle"
        font-size="30" font-weight="800"
        fill="${color}"
        font-family="Inter, system-ui, sans-serif">${score}%</text>
  <text x="${cx}" y="${cy + 12}" text-anchor="middle"
        font-size="12" font-weight="600"
        fill="#6b7280"
        font-family="Inter, system-ui, sans-serif">${label}</text>
</svg>`;
    const container = document.getElementById('gauge-container');
    if (container) {
        container.innerHTML = svg;
    }

    const labelEl = document.getElementById('integrity-label');
    if (labelEl) {
        labelEl.innerHTML = `
            <span style="display:inline-block;background:${color}1a;color:${color};
                         padding:4px 14px;border-radius:999px;font-weight:700;font-size:12px;
                         border:1px solid ${color}33;letter-spacing:0.04em;text-transform:uppercase;">
                ${label}
            </span>
        `;
    }
}

function renderStatCard(id, icon, number, label) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = `
        <div class="stat-icon">${icon}</div>
        <div class="stat-number">${number}</div>
        <div class="stat-label">${label}</div>
    `;
}

function renderSeverityPills(gaps) {
    const container = document.getElementById('severity-pills');
    if (!container) return;
    const counts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    gaps.forEach(g => {
        if (counts[g.severity_label] !== undefined) counts[g.severity_label]++;
    });
    if (gaps.length === 0) {
        container.innerHTML = `
            <span class="pill pill-ok">
                ✓ No suspicious gaps detected
            </span>
        `;
        return;
    }
    const order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
    const classMap = {
        CRITICAL: 'pill-critical',
        HIGH:     'pill-high',
        MEDIUM:   'pill-medium',
        LOW:      'pill-low',
    };
    container.innerHTML = order
        .filter(lv => counts[lv] > 0)
        .map(lv => `
            <span class="pill ${classMap[lv]}">
                ${lv}
                <span class="pill-count-badge">${counts[lv]}</span>
            </span>
        `).join('');
}

function renderGapCard(gap, index) {
    const colors   = { CRITICAL: '#ef4444', HIGH: '#f97316', MEDIUM: '#f59e0b', LOW: '#0891b2' };
    const bgColors = { CRITICAL: '#fee2e2', HIGH: '#ffedd5', MEDIUM: '#fef9c3', LOW: '#cffafe' };
    const color = colors[gap.severity_label]   || '#0891b2';
    const bg    = bgColors[gap.severity_label] || '#dbeafe';
    const startTime = gap.start_time ? gap.start_time.replace('T', ' ') : '—';
    const endTime   = gap.end_time   ? gap.end_time.replace('T', ' ')   : '—';
    const factors = gap.risk_factors || [];
    const factorTags = factors.length > 0
        ? `<div class="gap-factors-row">
               ${factors.map(f => `<span class="gap-factor-tag">${f}</span>`).join('')}
           </div>`
        : '';
    return `
<div class="gap-card ${gap.severity_label}" id="gap-card-${gap.id}">
    <div class="gap-header">
        <div class="gap-header-left">
            <span class="gap-index">#${index + 1}</span>
            <span class="gap-severity-badge"
                  style="background:${bg};color:${color};">${gap.severity_label}</span>
        </div>
        <span class="gap-duration-text" style="color:${color}">${gap.duration_human}</span>
    </div>
    <div class="score-bar-wrap">
        <div class="score-bar" style="width:${gap.severity_score}%;background:${color}"></div>
    </div>
    <div class="gap-meta-row">
        <span class="gap-meta-item">
            Score: <strong style="color:${color}">${gap.severity_score}/100</strong>
        </span>
        <span class="gap-meta-item">
            🕐 ${startTime} → ${endTime}
        </span>
        <span class="gap-meta-item">
            Lines ${gap.start_line.toLocaleString()}–${gap.end_line.toLocaleString()}
        </span>
        <span class="gap-meta-item">
            z-score: ${gap.modified_z_score}
        </span>
    </div>
    ${factorTags}
</div>`;
}

function formatTimeRange(metadata) {
    const first = metadata.first_timestamp;
    const last  = metadata.last_timestamp;
    if (!first || !last) return 'N/A';
    const totalSec = metadata.total_log_seconds || 0;
    if (totalSec > 0) return humanDuration(totalSec);

    try {
        const d1 = new Date(first);
        const d2 = new Date(last);
        const diffMs  = d2 - d1;
        const diffSec = diffMs / 1000;
        return humanDuration(diffSec);
    } catch {
        return 'N/A';
    }
}

function runAnalysis(fileId) {
    const slider      = document.getElementById('sensitivity-slider');
    const sensitivity = parseFloat(slider.value);
    showLoading(true);
    hideError();
    hideResults();
    fetch('/api/analyze', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ file_id: fileId, sensitivity: sensitivity }),
    })
        .then(res => res.json().then(data => ({ ok: res.ok, status: res.status, data })))
        .then(({ ok, status, data }) => {
            showLoading(false);
            if (!ok) {
                showError(data.error || 'Analysis failed (HTTP ' + status + ')');
                return;
            }
            currentAnalysisFileId = fileId;
            renderResults(data);
        })
        .catch(err => {
            showLoading(false);
            showError('Network error: ' + err.message);
        });
}

function renderResults(data) {
    const resultsEl = document.getElementById('results');
    if (resultsEl) resultsEl.classList.remove('hidden');
    const gaps   = data.gaps     || [];
    const meta   = data.metadata || {};
    const fmt    = data.format_detected || 'Unknown';
    const fileId = currentAnalysisFileId;

    const score = calcIntegrityScore(gaps, meta);
    renderGauge(score);

    const criticalCount = gaps.filter(g => g.severity_label === 'CRITICAL').length;
    const totalGaps     = gaps.length;
    const gapsLabel     = totalGaps === 0 ? '0' : (criticalCount > 0 ? criticalCount + ' crit' : totalGaps + ' found');
    renderStatCard('stat-gaps',   '🔍', totalGaps,
                   totalGaps === 0 ? 'No Gaps Found' : 'Gaps Detected');
    renderStatCard('stat-lines',  '📄', (meta.valid_lines || 0).toLocaleString(),
                   'Lines Processed');
    renderStatCard('stat-range',  '⏱️', formatTimeRange(meta),
                   'Log Duration');
    renderStatCard('stat-format', '📋', fmt,
                   'Format Detected');

    const gapsNum = document.querySelector('#stat-gaps .stat-number');
    if (gapsNum) {
        if (totalGaps === 0)       gapsNum.style.color = '#10b981';
        else if (criticalCount > 0) gapsNum.style.color = '#ef4444';
        else                        gapsNum.style.color = '#f59e0b';
    }

    renderSeverityPills(gaps);

    const timelineBadge = document.getElementById('timeline-badge');
    if (timelineBadge) {
        timelineBadge.textContent = gaps.length + ' gaps';
        if (gaps.length === 0) {
            timelineBadge.className = 'badge badge-success';
            timelineBadge.textContent = 'No gaps';
        }
    }

    renderTimeline(gaps, meta, 'timeline-container');

    const gapListEl = document.getElementById('gap-list');
    if (gapListEl) {
        if (gaps.length === 0) {
            gapListEl.innerHTML = `
                <div class="no-gaps-msg">
                    <span class="no-gaps-icon">✅</span>
                    <div class="no-gaps-title">No gaps detected</div>
                    <div class="no-gaps-sub">The log file appears continuous within your sensitivity threshold.</div>
                </div>
            `;
        } else {
            gapListEl.innerHTML = gaps.map((g, i) => renderGapCard(g, i)).join('');
        }
    }

    renderStatsGrid(meta, data);

    const ootCard  = document.getElementById('oot-card');
    const ootList  = document.getElementById('oot-list');
    const ootItems = meta.out_of_order || [];
    if (ootCard && ootList) {
        if (ootItems.length > 0) {
            ootCard.classList.remove('hidden');
            ootList.innerHTML = ootItems.map(o => `
                <div class="oot-row">
                    <span class="oot-line">Line ${o.line}</span>
                    <span>${o.timestamp}</span>
                    <span class="text-muted">prev: ${o.previous}</span>
                    <span class="oot-delta">${o.delta_seconds.toFixed(1)}s backward</span>
                </div>
            `).join('');
            if (meta.out_of_order_count > ootItems.length) {
                ootList.innerHTML += `
                    <div class="oot-row" style="color:var(--text-dim)">
                        …and ${meta.out_of_order_count - ootItems.length} more
                    </div>
                `;
            }
        } else {
            ootCard.classList.add('hidden');
        }
    }

    const btnCsv  = document.getElementById('btn-export-csv');
    const btnJson = document.getElementById('btn-export-json');
    const btnHtml = document.getElementById('btn-export-html');
    if (fileId) {
        if (btnCsv)  btnCsv.onclick  = () => { window.location.href = '/api/export/' + fileId + '/csv';  };
        if (btnJson) btnJson.onclick = () => { window.location.href = '/api/export/' + fileId + '/json'; };
        if (btnHtml) btnHtml.onclick = () => { window.location.href = '/api/export/' + fileId + '/html'; };
    }

    if (resultsEl) resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderStatsGrid(metadata, data) {
    const container = document.getElementById('stats-grid');
    if (!container) return;
    const mad = metadata.mad_stats || {};
    const items = [
        ['Total Lines',      (metadata.total_lines || 0).toLocaleString()],
        ['Valid Lines',      (metadata.valid_lines  || 0).toLocaleString()],
        ['Malformed Lines',  (metadata.malformed_count || 0).toLocaleString()],
        ['Out-of-Order',     (metadata.out_of_order_count || 0).toLocaleString()],
        ['Median Interval',  mad.median_interval != null ? mad.median_interval + 's' : 'N/A'],
        ['MAD',              mad.mad        != null ? mad.mad        + 's' : 'N/A'],
        ['MAD (scaled)',     mad.mad_scaled != null ? mad.mad_scaled + 's' : 'N/A'],
        ['Sensitivity Used', (data.sensitivity_used || 5.0).toFixed(1)],
        ['Format Detected',  data.format_detected || '—'],
        ['Processing Time',  (metadata.processing_time_ms || 0) + 'ms'],
    ];
    container.innerHTML = items.map(([label, value]) => `
        <div class="stats-item">
            <span class="stats-item-label">${label}</span>
            <span class="stats-item-value">${value}</span>
        </div>
    `).join('');
}

function humanDuration(seconds) {
    const s = Math.round(seconds);
    if (s < 60)    return s + 's';
    if (s < 3600) {
        const m   = Math.floor(s / 60);
        const rem = s % 60;
        return rem ? `${m}m ${rem}s` : `${m}m`;
    }
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return m ? `${h}h ${m}m` : `${h}h`;
}
function formatDateTime(isoStr) {
    if (!isoStr) return '—';
    try {
        const d = new Date(isoStr);
        return d.toLocaleString(undefined, {
            year:   'numeric', month:  '2-digit', day:    '2-digit',
            hour:   '2-digit', minute: '2-digit', second: '2-digit',
            hour12: false,
        });
    } catch {
        return isoStr;
    }
}
function formatShortDate(isoStr) {
    if (!isoStr) return '—';
    try {
        const d = new Date(isoStr);
        return d.toLocaleString(undefined, {
            month: '2-digit', day:    '2-digit',
            hour:  '2-digit', minute: '2-digit',
            hour12: false,
        });
    } catch {
        return isoStr;
    }
}

function showLoading(visible) {
    const el = document.getElementById('loading');
    if (el) el.classList.toggle('hidden', !visible);
}
function showError(msg) {
    const el = document.getElementById('error-box');
    if (el) {
        el.textContent = msg;
        el.classList.remove('hidden');
    }
}
function hideError() {
    const el = document.getElementById('error-box');
    if (el) el.classList.add('hidden');
}
function hideResults() {
    const el = document.getElementById('results');
    if (el) el.classList.add('hidden');
}