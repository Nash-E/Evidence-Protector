import os
import json
import csv
import io
from datetime import datetime
from flask import Blueprint, current_app, jsonify, Response

export_bp = Blueprint('export', __name__)

def _load_result(file_id: str):
    folder = current_app.config['UPLOAD_FOLDER']
    cache_path = os.path.join(folder, file_id + '.result.json')
    if not os.path.isfile(cache_path):
        return None
    with open(cache_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _fmt(iso):
    if not iso:
        return 'N/A'
    try:
        return datetime.fromisoformat(iso).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return iso

def _severity_color_hex(label):
    return {'CRITICAL': '#dc2626', 'HIGH': '#ea580c', 'MEDIUM': '#d97706', 'LOW': '#2563eb'}.get(label, '#6b7280')

def _severity_bg_hex(label):
    return {'CRITICAL': '#fee2e2', 'HIGH': '#ffedd5', 'MEDIUM': '#fef9c3', 'LOW': '#dbeafe'}.get(label, '#f3f4f6')

def _integrity_color(score):
    if score >= 90: return '#059669'
    if score >= 70: return '#4f46e5'
    if score >= 40: return '#d97706'
    return '#dc2626'
@export_bp.route('/api/export/<file_id>/json', methods=['GET'])
def export_json(file_id):
    result = _load_result(file_id)
    if result is None:
        return jsonify({'error': 'Result not found. Re-run analysis first.'}), 404

    output = json.dumps(result, indent=2)
    return Response(
        output,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=evidence_report_{file_id[:8]}.json'},
    )
@export_bp.route('/api/export/<file_id>/csv', methods=['GET'])
def export_csv(file_id):
    result = _load_result(file_id)
    if result is None:
        return jsonify({'error': 'Result not found. Re-run analysis first.'}), 404

    meta = result.get('metadata', {})
    assessment = result.get('assessment', {})
    gaps = result.get('gaps', [])
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    buf = io.StringIO()
    w = csv.writer(buf)

    w.writerow(['EVIDENCE PROTECTOR — FORENSIC LOG INTEGRITY REPORT'])
    w.writerow(['Generated', now])
    w.writerow(['Log Format', result.get('format_detected', 'Unknown')])
    w.writerow(['Sensitivity (MAD z-score)', result.get('sensitivity_used', 5.0)])
    w.writerow([])

    w.writerow(['INTEGRITY VERDICT'])
    w.writerow(['Score', f"{assessment.get('integrity_score', 'N/A')}%"])
    w.writerow(['Verdict', assessment.get('verdict', 'N/A')])
    w.writerow(['Detail', assessment.get('verdict_detail', '')])
    w.writerow([])

    w.writerow(['LOG FILE STATISTICS'])
    w.writerow(['Total Lines', meta.get('total_lines', 0)])
    w.writerow(['Valid Lines', meta.get('valid_lines', 0)])
    w.writerow(['Malformed Lines', meta.get('malformed_count', 0)])
    w.writerow(['Out-of-Order Timestamps', meta.get('out_of_order_count', 0)])
    w.writerow(['Time Range', f"{_fmt(meta.get('first_timestamp'))} to {_fmt(meta.get('last_timestamp'))}"])
    w.writerow(['Total Log Duration', assessment.get('gap_time_human', 'N/A')])
    w.writerow(['Total Gap Time', f"{assessment.get('gap_time_human','N/A')} ({assessment.get('gap_time_percent',0)}% of log)"])
    mad = meta.get('mad_stats', {})
    w.writerow(['Normal Log Interval (median)', f"{mad.get('median_interval', 'N/A')}s"])
    w.writerow(['Processing Time', f"{meta.get('processing_time_ms', 0)}ms"])
    w.writerow([])

    w.writerow(['KEY FINDINGS'])
    for i, finding in enumerate(assessment.get('findings', []), 1):
        w.writerow([f'Finding {i}', finding])
    w.writerow([])

    counts = assessment.get('severity_counts', {})
    w.writerow(['SEVERITY BREAKDOWN'])
    w.writerow(['CRITICAL', counts.get('CRITICAL', 0)])
    w.writerow(['HIGH', counts.get('HIGH', 0)])
    w.writerow(['MEDIUM', counts.get('MEDIUM', 0)])
    w.writerow(['LOW', counts.get('LOW', 0)])
    w.writerow([])

    w.writerow(['DETECTED GAPS — DETAILED'])
    w.writerow([
        'Gap #', 'Severity', 'Score /100', 'Z-Score',
        'Start Time', 'End Time', 'Duration',
        'Start Line', 'End Line',
    ])
    for g in gaps:
        w.writerow([
            g['id'],
            g['severity_label'],
            g['severity_score'],
            g['modified_z_score'],
            _fmt(g['start_time']),
            _fmt(g['end_time']),
            g['duration_human'],
            g['start_line'],
            g['end_line'],
        ])

    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=evidence_report_{file_id[:8]}.csv'},
    )
@export_bp.route('/api/export/<file_id>/html', methods=['GET'])
def export_html(file_id):
    result = _load_result(file_id)
    if result is None:
        return jsonify({'error': 'Result not found. Re-run analysis first.'}), 404

    meta = result.get('metadata', {})
    assessment = result.get('assessment', {})
    gaps = result.get('gaps', [])
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    integrity = assessment.get('integrity_score', 100)
    verdict = assessment.get('verdict', 'N/A')
    icolor = _integrity_color(integrity)
    mad = meta.get('mad_stats', {})
    counts = assessment.get('severity_counts', {})

    gap_rows_html = ''
    for g in gaps:
        sc = _severity_color_hex(g['severity_label'])
        bg = _severity_bg_hex(g['severity_label'])
        bar_w = min(g['severity_score'], 100)

        gap_rows_html += f"""
        <div class="gap-card" style="border-left:4px solid {sc}">
          <div class="gap-card-header">
            <div class="gap-left">
              <span class="gap-num">Gap #{g['id']}</span>
              <span class="badge" style="background:{bg};color:{sc}">{g['severity_label']}</span>
              <span class="gap-duration">{g['duration_human']}</span>
            </div>
            <div class="gap-score" style="color:{sc}">{g['severity_score']}<span style="font-size:13px;font-weight:500;color:#6b7280">/100</span></div>
          </div>
          <div class="score-bar-wrap">
            <div class="score-bar" style="width:{bar_w}%;background:{sc}"></div>
          </div>
          <div class="gap-meta">
            <span>🕐 {_fmt(g['start_time'])} → {_fmt(g['end_time'])}</span>
            <span>📄 Lines {g['start_line']}–{g['end_line']}</span>
            <span>📊 z-score: {g['modified_z_score']}</span>
          </div>
        </div>"""

    findings_html = ''.join(f'<li>{f}</li>' for f in assessment.get('findings', []))

    pills_html = ''
    for label, color, bg in [
        ('CRITICAL', '#dc2626', '#fee2e2'),
        ('HIGH', '#ea580c', '#ffedd5'),
        ('MEDIUM', '#d97706', '#fef9c3'),
        ('LOW', '#2563eb', '#dbeafe'),
    ]:
        n = counts.get(label, 0)
        if n > 0:
            pills_html += f'<span class="pill" style="background:{bg};color:{color}">{n} {label}</span>'

    oot_html = ''
    if meta.get('out_of_order_count', 0) > 0:
        oot_items = ''.join(
            f"<li>Line {o['line']}: {_fmt(o['timestamp'])} appears after {_fmt(o['previous'])}</li>"
            for o in meta.get('out_of_order', [])
        )
        oot_html = f"""
        <div class="card warn-card">
          <div class="card-title">⚠ Out-of-Order Timestamps — Possible Log Insertion</div>
          <p style="color:#92400e;margin:0 0 10px">
            {meta['out_of_order_count']} timestamp(s) appear earlier than the preceding entry.
            This is a signature of log insertion attacks where fabricated entries are added to a past window.
          </p>
          <ul class="oot-list">{oot_items}</ul>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Evidence Protector — Forensic Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f5f6fa; color: #111827; font-size: 14px; }}
  a {{ color: #4f46e5; }}

  .report-header {{ background: linear-gradient(135deg,#4f46e5,#7c3aed); color: white; padding: 32px 48px; }}
  .report-header h1 {{ font-size: 26px; font-weight: 800; margin-bottom: 4px; }}
  .report-header p {{ opacity: 0.85; font-size: 13px; }}
  .report-meta {{ display: flex; gap: 32px; margin-top: 16px; font-size: 12px; opacity: 0.9; }}
  .report-meta span b {{ display: block; font-size: 13px; }}

  .container {{ max-width: 960px; margin: 0 auto; padding: 32px 24px; }}
  .card {{ background: white; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,0.07); padding: 24px; margin-bottom: 20px; }}
  .card-title {{ font-size: 16px; font-weight: 700; color: #111827; margin-bottom: 16px; }}
  .warn-card {{ background: #fffbeb; border: 1px solid #fde68a; }}

  .verdict-row {{ display: flex; align-items: center; gap: 32px; }}
  .gauge-box {{ text-align: center; }}
  .integrity-num {{ font-size: 52px; font-weight: 800; line-height: 1; }}
  .integrity-label {{ font-size: 13px; font-weight: 600; margin-top: 4px; }}
  .verdict-text h2 {{ font-size: 20px; font-weight: 700; margin-bottom: 8px; }}
  .verdict-text p {{ color: #4b5563; line-height: 1.6; }}

  .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }}
  .stat {{ background: #f9fafb; border-radius: 10px; padding: 14px 16px; text-align: center; }}
  .stat-num {{ font-size: 24px; font-weight: 800; color: #4f46e5; }}
  .stat-lbl {{ font-size: 11px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px; }}

  .pills {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }}
  .pill {{ padding: 5px 14px; border-radius: 999px; font-size: 12px; font-weight: 700; }}

  .findings-list, .actions-list {{ padding-left: 0; list-style: none; }}
  .findings-list li {{ padding: 9px 0; border-bottom: 1px solid #f3f4f6; color: #374151; line-height: 1.5; }}
  .findings-list li:last-child {{ border-bottom: none; }}
  .actions-list li {{ display: flex; align-items: flex-start; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6; color: #374151; line-height: 1.5; }}
  .actions-list li:last-child {{ border-bottom: none; }}
  .action-num {{ background: #4f46e5; color: white; border-radius: 50%; width: 22px; height: 22px; min-width: 22px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; }}

  .gap-card {{ background: #f9fafb; border-radius: 12px; padding: 18px 20px; margin-bottom: 14px; }}
  .gap-card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
  .gap-left {{ display: flex; align-items: center; gap: 10px; }}
  .gap-num {{ font-weight: 700; font-size: 15px; }}
  .badge {{ padding: 3px 12px; border-radius: 999px; font-size: 11px; font-weight: 800; letter-spacing: 0.04em; }}
  .gap-duration {{ font-size: 14px; font-weight: 600; color: #374151; }}
  .gap-score {{ font-size: 28px; font-weight: 800; }}
  .score-bar-wrap {{ background: #e5e7eb; border-radius: 999px; height: 6px; margin: 8px 0 12px; }}
  .score-bar {{ height: 6px; border-radius: 999px; }}
  .gap-meta {{ display: flex; gap: 20px; font-size: 12px; color: #6b7280; margin-bottom: 14px; flex-wrap: wrap; }}
  .suggestions {{ background: white; border-radius: 8px; padding: 12px 16px; border: 1px solid #e5e7eb; }}
  .suggestions-title {{ font-size: 12px; font-weight: 700; color: #374151; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }}
  .suggestions ul {{ padding-left: 18px; color: #374151; line-height: 1.7; font-size: 13px; }}

  .oot-list {{ padding-left: 18px; color: #92400e; line-height: 1.8; font-size: 13px; }}

  .meta-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  .meta-table td {{ padding: 8px 12px; border-bottom: 1px solid #f3f4f6; }}
  .meta-table td:first-child {{ color: #6b7280; width: 220px; }}
  .meta-table td:last-child {{ font-weight: 600; color: #111827; }}

  .report-footer {{ text-align: center; color: #9ca3af; font-size: 12px; padding: 24px; margin-top: 8px; }}

  @media print {{
    body {{ background: white; }}
    .card {{ box-shadow: none; border: 1px solid #e5e7eb; }}
  }}
</style>
</head>
<body>

<div class="report-header">
  <h1>🛡 Evidence Protector — Forensic Log Integrity Report</h1>
  <p>Automated log tampering analysis using MAD-based statistical gap detection</p>
  <div class="report-meta">
    <span><b>Generated</b>{now}</span>
    <span><b>Log Format</b>{result.get('format_detected','Unknown')}</span>
    <span><b>Sensitivity</b>{result.get('sensitivity_used',5.0)} (MAD z-score)</span>
    <span><b>Time Range</b>{_fmt(meta.get('first_timestamp'))} → {_fmt(meta.get('last_timestamp'))}</span>
  </div>
</div>

<div class="container">

  <div class="card">
    <div class="card-title">Log Integrity Verdict</div>
    <div class="verdict-row">
      <div class="gauge-box">
        <div class="integrity-num" style="color:{icolor}">{integrity}%</div>
        <div class="integrity-label" style="color:{icolor}">{verdict}</div>
      </div>
      <div class="verdict-text">
        <h2 style="color:{icolor}">{verdict}</h2>
        <p>{assessment.get('verdict_detail','')}</p>
        <p style="margin-top:10px;color:#6b7280;font-size:13px">
          {assessment.get('gap_time_human','0s')} of unaccounted time
          ({assessment.get('gap_time_percent',0)}% of total log duration)
        </p>
      </div>
    </div>
  </div>

  <div class="stats-grid" style="margin-bottom:20px">
    <div class="stat">
      <div class="stat-num">{len(gaps)}</div>
      <div class="stat-lbl">Gaps Detected</div>
    </div>
    <div class="stat">
      <div class="stat-num">{meta.get('total_lines',0):,}</div>
      <div class="stat-lbl">Lines Processed</div>
    </div>
    <div class="stat">
      <div class="stat-num">{meta.get('malformed_count',0)}</div>
      <div class="stat-lbl">Malformed Lines</div>
    </div>
    <div class="stat">
      <div class="stat-num">{meta.get('out_of_order_count',0)}</div>
      <div class="stat-lbl">Out-of-Order</div>
    </div>
  </div>

  <div class="pills">{pills_html if pills_html else '<span style="color:#6b7280;font-size:13px">No gaps detected</span>'}</div>

  <div class="card">
    <div class="card-title">Key Findings</div>
    <ul class="findings-list">{findings_html}</ul>
  </div>

  {oot_html}

  <div class="card">
    <div class="card-title">Detected Gaps — Detail & Analyst Notes</div>
    {gap_rows_html if gap_rows_html else '<p style="color:#6b7280">No suspicious gaps detected at the current sensitivity threshold.</p>'}
  </div>

  <div class="card">
    <div class="card-title">Technical Analysis Parameters</div>
    <table class="meta-table">
      <tr><td>Median log interval</td><td>{mad.get('median_interval','N/A')}s</td></tr>
      <tr><td>MAD (raw)</td><td>{mad.get('mad','N/A')}s</td></tr>
      <tr><td>MAD scaled (×1.4826)</td><td>{mad.get('mad_scaled','N/A')}s</td></tr>
      <tr><td>Sensitivity threshold</td><td>{result.get('sensitivity_used',5.0)} (modified z-score)</td></tr>
      <tr><td>Total log duration</td><td>{int(meta.get('total_log_seconds',0))}s ({assessment.get('gap_time_human','N/A')} gap time)</td></tr>
      <tr><td>Processing time</td><td>{meta.get('processing_time_ms',0)}ms</td></tr>
      <tr><td>Detection method</td><td>MAD-based modified z-score (Iglewicz & Hoaglin, 1993)</td></tr>
    </table>
  </div>

</div>

<div class="report-footer">
  Evidence Protector · Generated {now} · For investigative use only
</div>

</body>
</html>"""

    return Response(
        html,
        mimetype='text/html',
        headers={'Content-Disposition': f'attachment; filename=evidence_report_{file_id[:8]}.html'},
    )
