import bisect
from typing import List, Dict, Any, Optional

TIER_THRESHOLDS = [30, 300, 900, 3600, 14400]

def severity_label(score: float) -> str:
    if score >= 75:
        return 'CRITICAL'
    if score >= 50:
        return 'HIGH'
    if score >= 25:
        return 'MEDIUM'
    return 'LOW'
def compute_density_drop(gap_start_ts, gap_end_ts, timestamps: list) -> float:
    if not timestamps or len(timestamps) < 2:
        return 0.0
    from datetime import timedelta
    import bisect as _bisect
    total_secs = (timestamps[-1] - timestamps[0]).total_seconds()
    if total_secs <= 0:
        return 0.0
    global_density = len(timestamps) / (total_secs / 60.0)
    window = timedelta(seconds=60)
    ts_floats = [t.timestamp() for t in timestamps]
    bs = (gap_start_ts - window).timestamp()
    gs = gap_start_ts.timestamp()
    ge = gap_end_ts.timestamp()
    ae = (gap_end_ts + window).timestamp()
    before_count = _bisect.bisect_right(ts_floats, gs) - _bisect.bisect_left(ts_floats, bs)
    after_count  = _bisect.bisect_right(ts_floats, ae) - _bisect.bisect_left(ts_floats, ge)
    local_density = (before_count + after_count) / 2.0
    if global_density <= 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - local_density / global_density))
def compute_time_of_day_score(gap_start_ts) -> float:
    hour = gap_start_ts.hour
    if   0  <= hour <  6:  return 1.0
    elif 6  <= hour <  9:  return 0.6
    elif 9  <= hour < 18:  return 0.1
    elif 18 <= hour < 22:  return 0.4
    else:                  return 0.8

def compute_day_of_week_score(gap_start_ts) -> float:
    return 0.8 if gap_start_ts.weekday() >= 5 else 0.1
def compute_position_score(gap_start_ts, log_start_ts, log_end_ts) -> float:
    total = (log_end_ts - log_start_ts).total_seconds()
    if total <= 0:
        return 0.0

    pos = (gap_start_ts - log_start_ts).total_seconds() / total
    edge_dist = min(pos, 1.0 - pos)
    if edge_dist <= 0.05:   return 1.0
    elif edge_dist <= 0.10: return 0.6
    elif edge_dist <= 0.20: return 0.3
    else:                   return 0.0
def compute_cluster_score(gap_start_ts, all_gap_starts: list) -> float:
    if len(all_gap_starts) <= 1:
        return 0.0

    WINDOW = 300
    gs = gap_start_ts.timestamp()
    neighbours = sum(
        1 for t in all_gap_starts
        if t is not gap_start_ts and abs(t.timestamp() - gs) <= WINDOW
    )
    if neighbours == 0: return 0.0
    if neighbours == 1: return 0.5
    return 1.0
def compute_severity_score(
    duration_seconds: float,
    modified_z_score: float,
    total_log_seconds: float,
    timestamps: list,
    gap_start_ts,
    gap_end_ts,
    log_start_ts=None,
    log_end_ts=None,
    all_gap_starts: Optional[list] = None,
) -> dict:
    factors = []

    z_norm = min(modified_z_score / 20.0, 1.0)

    if total_log_seconds > 0:
        prop_norm = min(duration_seconds / max(total_log_seconds * 0.5, 1.0), 1.0)
    else:
        prop_norm = 0.0

    tier_idx  = bisect.bisect(TIER_THRESHOLDS, duration_seconds)
    tier_norm = tier_idx / len(TIER_THRESHOLDS)

    density_drop = compute_density_drop(gap_start_ts, gap_end_ts, timestamps)
    if density_drop >= 0.6:
        factors.append('Activity drop')

    tod_score = compute_time_of_day_score(gap_start_ts)
    if tod_score >= 0.6:
        hour = gap_start_ts.hour
        if hour < 6:
            factors.append('Off-hours (night)')
        elif hour < 9:
            factors.append('Off-hours (early AM)')
        else:
            factors.append('Off-hours (late night)')

    dow_score = compute_day_of_week_score(gap_start_ts)
    if dow_score >= 0.5:
        factors.append('Weekend')

    pos_score = 0.0
    if log_start_ts and log_end_ts:
        pos_score = compute_position_score(gap_start_ts, log_start_ts, log_end_ts)
        if pos_score >= 0.6:
            mid = log_start_ts + (log_end_ts - log_start_ts) / 2
            factors.append('Near log start' if gap_start_ts < mid else 'Near log end')

    cluster_score = 0.0
    if all_gap_starts:
        cluster_score = compute_cluster_score(gap_start_ts, all_gap_starts)
        if cluster_score >= 0.5:
            factors.append('Clustered gaps')
    raw = (
        0.25 * z_norm        +
        0.15 * prop_norm     +
        0.15 * tier_norm     +
        0.10 * density_drop  +
        0.15 * tod_score     +
        0.05 * dow_score     +
        0.10 * pos_score     +
        0.05 * cluster_score
    )
    return {
        'score':   round(raw * 100, 1),
        'factors': factors,
    }
