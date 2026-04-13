'use strict';
const SEV_COLORS = {
    CRITICAL: '#ef4444',
    HIGH:     '#f97316',
    MEDIUM:   '#f59e0b',
    LOW:      '#0891b2',
};
function renderTimeline(gaps, metadata, containerId) {
    containerId = containerId || 'timeline-container';
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    const VB_W     = 900;
    const VB_H     = 120;
    const TRACK_Y  = 46;
    const TRACK_H  = 14;
    const LABEL_Y  = TRACK_Y + TRACK_H + 18;
    const MARGIN_X = 54;
    const USABLE_W = VB_W - MARGIN_X * 2;
    const ns = 'http:
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', `0 0 ${VB_W} ${VB_H}`);
    svg.setAttribute('xmlns', ns);
    svg.style.display = 'block';
    svg.style.width   = '100%';
    const bgRect = document.createElementNS(ns, 'rect');
    bgRect.setAttribute('width',  VB_W);
    bgRect.setAttribute('height', VB_H);
    bgRect.setAttribute('fill',   '#f9fafb');
    bgRect.setAttribute('rx',     '10');
    svg.appendChild(bgRect);
    const firstTs = metadata.first_timestamp ? new Date(metadata.first_timestamp).getTime() : null;
    const lastTs  = metadata.last_timestamp  ? new Date(metadata.last_timestamp).getTime()  : null;
    if (!firstTs || !lastTs || lastTs <= firstTs) {
        const text = document.createElementNS(ns, 'text');
        text.setAttribute('x',           VB_W / 2);
        text.setAttribute('y',           VB_H / 2 + 5);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill',        '#9ca3af');
        text.setAttribute('font-size',   '14');
        text.setAttribute('font-family', 'Inter, system-ui, sans-serif');
        text.textContent = 'No timestamp data available';
        svg.appendChild(text);
        container.appendChild(svg);
        return;
    }
    const totalMs = lastTs - firstTs;
    function timeToX(ts) {
        return MARGIN_X + ((ts - firstTs) / totalMs) * USABLE_W;
    }
    const track = document.createElementNS(ns, 'rect');
    track.setAttribute('x',      MARGIN_X);
    track.setAttribute('y',      TRACK_Y);
    track.setAttribute('width',  USABLE_W);
    track.setAttribute('height', TRACK_H);
    track.setAttribute('fill',   '#e5e7eb');
    track.setAttribute('rx',     '4');
    svg.appendChild(track);
    if (gaps.length === 0) {
        const fullSeg = document.createElementNS(ns, 'rect');
        fullSeg.setAttribute('x',      MARGIN_X);
        fullSeg.setAttribute('y',      TRACK_Y);
        fullSeg.setAttribute('width',  USABLE_W);
        fullSeg.setAttribute('height', TRACK_H);
        fullSeg.setAttribute('fill',   '#4f46e5');
        fullSeg.setAttribute('rx',     '4');
        svg.appendChild(fullSeg);
        const noGapText = document.createElementNS(ns, 'text');
        noGapText.setAttribute('x',           VB_W / 2);
        noGapText.setAttribute('y',           TRACK_Y - 12);
        noGapText.setAttribute('text-anchor', 'middle');
        noGapText.setAttribute('fill',        '#10b981');
        noGapText.setAttribute('font-size',   '11');
        noGapText.setAttribute('font-weight', '700');
        noGapText.setAttribute('font-family', 'Inter, system-ui, sans-serif');
        noGapText.textContent = '✓ No gaps detected — log appears continuous';
        svg.appendChild(noGapText);
    } else {
        const sortedGaps = [...gaps].sort(
            (a, b) => new Date(a.start_time) - new Date(b.start_time)
        );
        const segments = [];
        let segStart = firstTs;
        for (const g of sortedGaps) {
            const gs = new Date(g.start_time).getTime();
            const ge = new Date(g.end_time).getTime();
            if (segStart < gs) {
                segments.push([segStart, gs]);
            }
            segStart = ge;
        }
        if (segStart < lastTs) {
            segments.push([segStart, lastTs]);
        }
        for (const [s, e] of segments) {
            const x = timeToX(s);
            const w = Math.max(1, timeToX(e) - x);
            const seg = document.createElementNS(ns, 'rect');
            seg.setAttribute('x',      x);
            seg.setAttribute('y',      TRACK_Y);
            seg.setAttribute('width',  w);
            seg.setAttribute('height', TRACK_H);
            seg.setAttribute('fill',   '#4f46e5');
            seg.setAttribute('opacity', '0.85');
            svg.appendChild(seg);
        }
    }
    if (gaps.length > 0) {
        const sortedGaps = [...gaps].sort(
            (a, b) => new Date(a.start_time) - new Date(b.start_time)
        );
        const MIN_GAP_PX = 4;
        const MAX_GAP_H  = 36;
        for (const g of sortedGaps) {
            const gs    = new Date(g.start_time).getTime();
            const ge    = new Date(g.end_time).getTime();
            const x     = timeToX(gs);
            const rawW  = timeToX(ge) - x;
            const w     = Math.max(MIN_GAP_PX, rawW);
            const color = SEV_COLORS[g.severity_label] || '#4f46e5';
            const barH = Math.max(8, Math.min(MAX_GAP_H, (g.severity_score / 100) * MAX_GAP_H));
            const barY = TRACK_Y + TRACK_H / 2 - barH / 2;
            const rect = document.createElementNS(ns, 'rect');
            rect.setAttribute('x',       x);
            rect.setAttribute('y',       barY);
            rect.setAttribute('width',   w);
            rect.setAttribute('height',  barH);
            rect.setAttribute('fill',    color);
            rect.setAttribute('rx',      '3');
            rect.setAttribute('opacity', '0.92');
            rect.style.cursor     = 'pointer';
            rect.style.transition = 'opacity 0.15s';
            rect.addEventListener('mouseenter', () => {
                rect.setAttribute('opacity', '1');
                rect.style.filter = 'brightness(1.1)';
            });
            rect.addEventListener('mouseleave', () => {
                rect.setAttribute('opacity', '0.92');
                rect.style.filter = '';
            });
            rect.addEventListener('click', () => {
                const card = document.getElementById('gap-card-' + g.id);
                if (card) {
                    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    card.style.outline       = '2.5px solid ' + color;
                    card.style.outlineOffset = '2px';
                    setTimeout(() => {
                        card.style.outline       = '';
                        card.style.outlineOffset = '';
                    }, 1800);
                }
            });
            const titleEl = document.createElementNS(ns, 'title');
            titleEl.textContent = `Gap #${g.id} | ${g.severity_label} | ${g.duration_human} | Score: ${g.severity_score}`;
            rect.appendChild(titleEl);
            svg.appendChild(rect);
            if (w >= 20) {
                const lbl = document.createElementNS(ns, 'text');
                lbl.setAttribute('x',           x + w / 2);
                lbl.setAttribute('y',           LABEL_Y);
                lbl.setAttribute('text-anchor', 'middle');
                lbl.setAttribute('fill',        color);
                lbl.setAttribute('font-size',   '9');
                lbl.setAttribute('font-weight', '800');
                lbl.setAttribute('font-family', 'Inter, system-ui, sans-serif');
                lbl.textContent = g.severity_label.charAt(0);
                svg.appendChild(lbl);
            }
        }
    }
    function fmtTs(isoStr) {
        try {
            const d = new Date(isoStr);
            return d.toLocaleString(undefined, {
                month:  '2-digit', day:    '2-digit',
                hour:   '2-digit', minute: '2-digit', second: '2-digit',
                hour12: false,
            });
        } catch {
            return isoStr;
        }
    }
    const labelFill   = '#374151';
    const labelFamily = 'Consolas, Menlo, monospace';
    const startLabel = document.createElementNS(ns, 'text');
    startLabel.setAttribute('x',           MARGIN_X);
    startLabel.setAttribute('y',           VB_H - 5);
    startLabel.setAttribute('text-anchor', 'start');
    startLabel.setAttribute('fill',        labelFill);
    startLabel.setAttribute('font-size',   '9');
    startLabel.setAttribute('font-family', labelFamily);
    startLabel.textContent = fmtTs(metadata.first_timestamp);
    svg.appendChild(startLabel);
    const endLabel = document.createElementNS(ns, 'text');
    endLabel.setAttribute('x',           MARGIN_X + USABLE_W);
    endLabel.setAttribute('y',           VB_H - 5);
    endLabel.setAttribute('text-anchor', 'end');
    endLabel.setAttribute('fill',        labelFill);
    endLabel.setAttribute('font-size',   '9');
    endLabel.setAttribute('font-family', labelFamily);
    endLabel.textContent = fmtTs(metadata.last_timestamp);
    svg.appendChild(endLabel);
    container.appendChild(svg);
}