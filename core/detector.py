import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from core.formats import detect_format
from core.parser import line_generator, parse_line
from core.scorer import compute_severity_score, severity_label
from core.suggestions import overall_assessment
from config import MIN_GAP_ABSOLUTE_SECONDS, DEFAULT_SENSITIVITY
@dataclass
class GapRecord:
    id: int
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    start_line: int
    end_line: int
    modified_z_score: float
    severity_score: float
    severity_label: str
    risk_factors: list
def format_duration(seconds: float) -> str:
    s = int(seconds)
    if s >= 3600:
        h = s // 3600
        m = (s % 3600) // 60
        rem = s % 60
        parts = [f"{h}h"]
        if m: parts.append(f"{m}m")
        if rem: parts.append(f"{rem}s")
        return ' '.join(parts)
    elif s >= 60:
        m = s // 60
        rem = s % 60
        return f"{m}m {rem}s" if rem else f"{m}m"
    return f"{s}s"
def run_analysis(filepath: str, sensitivity: float = DEFAULT_SENSITIVITY) -> Dict[str, Any]:
    t_start = time.time()
    log_format = detect_format(filepath)
    compiled_rx = re.compile(log_format.pattern)
    intervals: List[Tuple[float, int, int, datetime, datetime]] = []
    all_timestamps: List[datetime] = []
    out_of_order: List[dict] = []
    prev_time: Optional[datetime] = None
    prev_line_num: int = 0
    total_lines = 0
    valid_lines = 0
    malformed_count = 0
    first_timestamp: Optional[datetime] = None
    last_timestamp: Optional[datetime] = None
    for line_num, line in line_generator(filepath):
        total_lines += 1
        curr_time = parse_line(line, compiled_rx, log_format.parse_fn)
        if curr_time is None:
            malformed_count += 1
            continue
        valid_lines += 1
        all_timestamps.append(curr_time)
        if first_timestamp is None:
            first_timestamp = curr_time
        last_timestamp = curr_time
        if prev_time is None:
            prev_time = curr_time
            prev_line_num = line_num
            continue
        delta = (curr_time - prev_time).total_seconds()
        if delta >= 0:
            intervals.append((delta, prev_line_num, line_num, prev_time, curr_time))
        else:
            out_of_order.append({
                'line': line_num,
                'timestamp': curr_time.isoformat(),
                'previous': prev_time.isoformat(),
                'delta_seconds': delta,
            })
        prev_time = curr_time
        prev_line_num = line_num
    if len(intervals) < 2:
        gaps = []
        mad_stats = {'median': 0, 'mad': 0, 'mad_scaled': 1.0}
    else:
        values = sorted(iv[0] for iv in intervals)
        n = len(values)
        median = values[n // 2]
        abs_devs = sorted(abs(v - median) for v in values)
        mad = abs_devs[n // 2]
        mad_scaled = max(mad * 1.4826, 1.0)
        mad_stats = {
            'median_interval': round(median, 3),
            'mad': round(mad, 3),
            'mad_scaled': round(mad_scaled, 3),
        }
        total_log_seconds = (
            (last_timestamp - first_timestamp).total_seconds()
            if first_timestamp and last_timestamp else 0.0
        )
        raw_gaps = []
        for delta, from_line, to_line, from_ts, to_ts in intervals:
            modified_z = 0.6745 * (delta - median) / mad_scaled
            if modified_z > sensitivity and delta >= MIN_GAP_ABSOLUTE_SECONDS:
                raw_gaps.append((delta, from_line, to_line, from_ts, to_ts, modified_z))
        all_gap_starts = [g[3] for g in raw_gaps]
        gaps: List[GapRecord] = []
        for gap_id, (delta, from_line, to_line, from_ts, to_ts, modified_z) in enumerate(raw_gaps, 1):
            result = compute_severity_score(
                duration_seconds=delta,
                modified_z_score=modified_z,
                total_log_seconds=total_log_seconds,
                timestamps=all_timestamps,
                gap_start_ts=from_ts,
                gap_end_ts=to_ts,
                log_start_ts=first_timestamp,
                log_end_ts=last_timestamp,
                all_gap_starts=all_gap_starts,
            )
            score   = result['score']
            factors = result['factors']
            gaps.append(GapRecord(
                id=gap_id,
                start_time=from_ts,
                end_time=to_ts,
                duration_seconds=delta,
                start_line=from_line,
                end_line=to_line,
                modified_z_score=round(modified_z, 2),
                severity_score=score,
                severity_label=severity_label(score),
                risk_factors=factors,
            ))
    gaps.sort(key=lambda g: g.severity_score, reverse=True)
    processing_time_ms = int((time.time() - t_start) * 1000)
    metadata = {
        'total_lines': total_lines,
        'valid_lines': valid_lines,
        'malformed_count': malformed_count,
        'out_of_order_count': len(out_of_order),
        'out_of_order': out_of_order[:20],
        'first_timestamp': first_timestamp.isoformat() if first_timestamp else None,
        'last_timestamp': last_timestamp.isoformat() if last_timestamp else None,
        'total_log_seconds': (last_timestamp - first_timestamp).total_seconds() if first_timestamp and last_timestamp else 0,
        'processing_time_ms': processing_time_ms,
        'mad_stats': mad_stats if len(intervals) >= 2 else {},
    }
    gaps_serialized = [
        {
            'id': g.id,
            'start_time': g.start_time.isoformat(),
            'end_time': g.end_time.isoformat(),
            'duration_seconds': g.duration_seconds,
            'duration_human': format_duration(g.duration_seconds),
            'start_line': g.start_line,
            'end_line': g.end_line,
            'modified_z_score': g.modified_z_score,
            'severity_score': g.severity_score,
            'severity_label': g.severity_label,
            'risk_factors': g.risk_factors,
        }
        for g in gaps
    ]
    assessment = overall_assessment(gaps_serialized, metadata)
    return {
        'format_detected': log_format.display_name,
        'format_name': log_format.name,
        'sensitivity_used': sensitivity,
        'assessment': assessment,
        'metadata': metadata,
        'gaps': gaps_serialized,
    }