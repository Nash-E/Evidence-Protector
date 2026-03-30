import bisect
from typing import List, Dict, Any

TIER_THRESHOLDS = [30, 300, 900, 3600, 14400]  # 30s, 5m, 15m, 1h, 4h

def severity_label(score: float) -> str:
    if score >= 75:
        return 'CRITICAL'
    if score >= 50:
        return 'HIGH'
    if score >= 25:
        return 'MEDIUM'
    return 'LOW'

def compute_density_drop(gap_start_ts, gap_end_ts, timestamps: list) -> float:
    """
    Compare log density in 60s windows before/after gap to global average.
    timestamps: sorted list of datetime objects
    Returns a value 0.0 (no drop) to 1.0 (complete silence).
    """
    if not timestamps or len(timestamps) < 2:
        return 0.0

    from datetime import timedelta

    total_secs = (timestamps[-1] - timestamps[0]).total_seconds()
    if total_secs <= 0:
        return 0.0

    global_density = len(timestamps) / (total_secs / 60.0)  # lines per 60s

    window = timedelta(seconds=60)
    before_start = gap_start_ts - window

    # Use bisect for O(log n) range queries
    import bisect as _bisect

    # Convert to float timestamps for bisect
    ts_floats = [t.timestamp() for t in timestamps]

    bs = before_start.timestamp()
    gs = gap_start_ts.timestamp()
    ge = gap_end_ts.timestamp()
    ae = (gap_end_ts + window).timestamp()

    before_count = _bisect.bisect_right(ts_floats, gs) - _bisect.bisect_left(ts_floats, bs)
    after_count = _bisect.bisect_right(ts_floats, ae) - _bisect.bisect_left(ts_floats, ge)

    local_density = (before_count + after_count) / 2.0

    if global_density <= 0:
        return 0.0

    density_ratio = local_density / global_density
    return max(0.0, min(1.0, 1.0 - density_ratio))


def compute_severity_score(
    duration_seconds: float,
    modified_z_score: float,
    total_log_seconds: float,
    timestamps: list,
    gap_start_ts,
    gap_end_ts,
) -> float:
    """
    Composite 0-100 severity score.
    Weights: z-score 35%, proportion 25%, absolute tier 25%, density drop 15%
    """
    # A: Z-score component
    z_norm = min(modified_z_score / 20.0, 1.0)

    # B: Proportion of total log duration
    if total_log_seconds > 0:
        prop_norm = min(duration_seconds / max(total_log_seconds * 0.5, 1.0), 1.0)
    else:
        prop_norm = 0.0

    # C: Absolute duration tier
    tier_idx = bisect.bisect(TIER_THRESHOLDS, duration_seconds)
    tier_norm = tier_idx / len(TIER_THRESHOLDS)

    # D: Log density drop
    density_drop = compute_density_drop(gap_start_ts, gap_end_ts, timestamps)

    raw = (
        0.35 * z_norm +
        0.25 * prop_norm +
        0.25 * tier_norm +
        0.15 * density_drop
    )
    return round(raw * 100, 1)
