from typing import List, Dict, Any
def overall_assessment(gaps: List[dict], metadata: dict) -> Dict[str, Any]:
    total_lines = metadata.get('total_lines', 0)
    malformed   = metadata.get('malformed_count', 0)
    oot_count   = metadata.get('out_of_order_count', 0)
    total_secs  = metadata.get('total_log_seconds', 0)
    critical = [g for g in gaps if g['severity_label'] == 'CRITICAL']
    high     = [g for g in gaps if g['severity_label'] == 'HIGH']
    medium   = [g for g in gaps if g['severity_label'] == 'MEDIUM']
    low      = [g for g in gaps if g['severity_label'] == 'LOW']
    total_gap_seconds = sum(g['duration_seconds'] for g in gaps)
    gap_pct = round((total_gap_seconds / total_secs * 100), 1) if total_secs > 0 else 0
    if not gaps:
        integrity = 100
    else:
        time_ratio = min(total_gap_seconds / total_secs, 1.0) if total_secs > 0 else 0
        penalty = (time_ratio * 50) + (len(critical) * 15) + (len(high) * 8) + (len(medium) * 3)
        integrity = max(0, round(100 - penalty))
    if integrity >= 90:
        verdict = 'HIGHLY INTACT'
        verdict_detail = 'No significant tampering indicators detected. Log appears complete and consistent.'
    elif integrity >= 70:
        verdict = 'MOSTLY INTACT'
        verdict_detail = 'Minor anomalies detected. Likely explainable by system events but should be verified.'
    elif integrity >= 40:
        verdict = 'SUSPICIOUS'
        verdict_detail = 'Multiple significant gaps detected. Log shows patterns consistent with selective deletion.'
    else:
        verdict = 'COMPROMISED'
        verdict_detail = 'Severe integrity failure. Log has lost a substantial portion of its time coverage. Treat as unreliable without corroboration.'
    findings = []
    if not gaps:
        findings.append("No suspicious time gaps detected within the configured sensitivity threshold.")
    else:
        findings.append(
            f"{len(gaps)} suspicious gap(s) detected, accounting for {gap_pct}% of the total log duration "
            f"({_fmt_duration(total_gap_seconds)} of unaccounted time)."
        )
    if critical:
        findings.append(
            f"{len(critical)} CRITICAL gap(s) found — these represent the highest-priority evidence of tampering."
        )
    if oot_count > 0:
        findings.append(
            f"{oot_count} out-of-order timestamp(s) detected — possible log insertion in addition to deletions."
        )
    if malformed > 0:
        malformed_pct = round(malformed / total_lines * 100, 1) if total_lines > 0 else 0
        if malformed_pct > 5:
            findings.append(
                f"High malformed line rate: {malformed} lines ({malformed_pct}%) could not be parsed. "
                f"This may indicate targeted corruption of specific log entries."
            )
        else:
            findings.append(
                f"{malformed} malformed line(s) ({malformed_pct}%) — within acceptable range for encoding issues."
            )
    if len(gaps) >= 3:
        findings.append(
            "Multiple gaps distributed across the log suggest systematic rather than accidental deletion."
        )
    mad_stats = metadata.get('mad_stats', {})
    median_interval = mad_stats.get('median_interval', None)
    return {
        'integrity_score': integrity,
        'verdict': verdict,
        'verdict_detail': verdict_detail,
        'gap_time_seconds': total_gap_seconds,
        'gap_time_human': _fmt_duration(total_gap_seconds),
        'gap_time_percent': gap_pct,
        'severity_counts': {
            'CRITICAL': len(critical),
            'HIGH': len(high),
            'MEDIUM': len(medium),
            'LOW': len(low),
        },
        'median_interval_seconds': median_interval,
        'findings': findings,
    }
def _fmt_duration(seconds: float) -> str:
    s = int(seconds)
    if s >= 3600:
        h = s // 3600
        m = (s % 3600) // 60
        return f"{h}h {m}m" if m else f"{h}h"
    elif s >= 60:
        m = s // 60
        rem = s % 60
        return f"{m}m {rem}s" if rem else f"{m}m"
    return f"{s}s"