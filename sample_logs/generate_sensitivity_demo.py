"""
Generate a log specifically designed to demonstrate the sensitivity slider.

Normal interval: 20-40s  →  median ~30s, MAD ~5s, MAD_scaled ~7.4

Injected gaps (z-scores calculated from above baseline):
  Line 100 →  75s gap  → z ≈ 4.1  → visible at sensitivity ≤4, gone at 5
  Line 250 →  96s gap  → z ≈ 6.0  → visible at sensitivity ≤6, gone at 7
  Line 400 → 1800s gap → z ≈ 163  → always caught (CRITICAL)

Demo flow:
  Sensitivity 3  → 3 gaps shown
  Sensitivity 5  → 2 gaps (first borderline gap disappears)
  Sensitivity 7  → 1 gap  (second gap disappears, only CRITICAL remains)

Run: python sample_logs/generate_sensitivity_demo.py
"""

import random
import os
from datetime import datetime, timedelta

random.seed(77)
OUT_DIR    = os.path.dirname(os.path.abspath(__file__))
TOTAL      = 500
START_TIME = datetime(2025, 3, 28, 8, 0, 0)

GAPS = {
    100: 75,    # z ≈ 4.1  — borderline LOW
    250: 96,    # z ≈ 6.0  — borderline MEDIUM
    400: 1800,  # z ≈ 163  — always CRITICAL
}

MALFORM_LINES = {40, 130, 220, 320, 470}
OOT_LINE = 350

IPS     = [f"10.0.1.{i}" for i in range(1, 30)]
PATHS   = ["/api/v1/data", "/api/v1/users", "/health", "/metrics",
           "/api/v1/jobs", "/login", "/logout", "/api/v1/report"]
METHODS = ["GET", "GET", "GET", "POST", "POST", "PUT"]
CODES   = [200, 200, 200, 201, 304, 400, 404, 500]

def make_line(ts):
    ts_str = ts.strftime("%d/%b/%Y:%H:%M:%S")
    return (
        f"{random.choice(IPS)} - - [{ts_str} +0000] "
        f'"{random.choice(METHODS)} {random.choice(PATHS)} HTTP/1.1" '
        f"{random.choice(CODES)} {random.randint(200, 40000)}"
    )

MALFORM_POOL = ["", "::1 - - [] - -", "--- log rotation ---",
                "CORRUPTED ENTRY", "last message repeated 3 times"]

if __name__ == "__main__":
    lines = []
    ts = START_TIME

    for i in range(1, TOTAL + 1):
        if i in GAPS:
            ts += timedelta(seconds=GAPS[i])
        else:
            ts += timedelta(seconds=random.randint(20, 40))

        if i in MALFORM_LINES:
            lines.append(random.choice(MALFORM_POOL))
            continue

        if i == OOT_LINE:
            lines.append(make_line(ts - timedelta(seconds=45)))
            continue

        lines.append(make_line(ts))

    filename = "sensitivity_demo.log"
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    size_kb = os.path.getsize(path) / 1024
    print(f"Created {filename} ({TOTAL} lines, {size_kb:.1f} KB)")
    print()
    print("Expected z-scores (baseline: median~30s, MAD_scaled~7.4s):")
    print("  Line 100 |  75s gap | z ≈ 4.1  → disappears above sensitivity 4")
    print("  Line 250 |  96s gap | z ≈ 6.0  → disappears above sensitivity 6")
    print("  Line 400 | 1800s gap| z ≈ 163  → always caught")
    print()
    print("Demo:")
    print("  Sensitivity 3 → 3 gaps")
    print("  Sensitivity 5 → 2 gaps (first gap gone)")
    print("  Sensitivity 7 → 1 gap  (only CRITICAL remains)")
