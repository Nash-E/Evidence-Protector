import random
import os
from datetime import datetime, timedelta
random.seed(42)
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
TOTAL_LINES = 500_000
START_TIME  = datetime(2025, 3, 1, 0, 0, 0)
GAPS = [
    (30000,   180,   "LOW"),
    (80000,   450,   "MEDIUM"),
    (120000,  1200,  "HIGH"),
    (180000,  320,   "MEDIUM"),
    (240000,  7200,  "CRITICAL"),
    (310000,  600,   "HIGH"),
    (400000,  14400, "CRITICAL"),
    (460000,  90,    "LOW"),
]
GAP_LINES = {g[0]: g[1] for g in GAPS}
OOT_LINES    = {150000, 275000, 420000}
MALFORM_LINES = set(random.sample(range(1, TOTAL_LINES), 50))
IPS = (
    [f"192.168.10.{i}" for i in range(1, 50)] +
    [f"10.0.0.{i}"     for i in range(1, 30)] +
    ["203.0.113.5", "198.51.100.22", "172.16.0.99"]
)
PATHS = [
    "/", "/index.html", "/login", "/logout", "/api/v1/users",
    "/api/v1/orders", "/api/v1/products", "/admin/dashboard",
    "/static/app.js", "/static/main.css", "/favicon.ico",
    "/api/v1/auth/token", "/health", "/metrics", "/api/v1/search",
]
METHODS = ["GET", "GET", "GET", "POST", "POST", "PUT", "DELETE"]
CODES   = [200, 200, 200, 200, 301, 304, 400, 401, 403, 404, 500, 502]
UAS     = [
    'Mozilla/5.0 (Windows NT 10.0)',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X)',
    'python-requests/2.28.0',
    'curl/7.68.0',
    'Go-http-client/1.1',
]
MALFORM_POOL = [
    "",
    "::1 - - [] - -",
    "server: restart sequence initiated",
    "CORRUPTED\\x00\\xff ENTRY",
    "last message repeated 5 times",
    "--- log rotation ---",
]
def interval(ts):
    hour = ts.hour
    if 2 <= hour < 6:
        return random.randint(3, 12)
    elif 9 <= hour < 18:
        return random.randint(1, 3)
    else:
        return random.randint(1, 6)
def make_line(ts):
    ts_str = ts.strftime("%d/%b/%Y:%H:%M:%S")
    return (
        f"{random.choice(IPS)} - - [{ts_str} +0000] "
        f'"{random.choice(METHODS)} {random.choice(PATHS)} HTTP/1.1" '
        f"{random.choice(CODES)} {random.randint(150, 80000)} "
        f'"-" "{random.choice(UAS)}"'
    )
if __name__ == "__main__":
    print(f"Generating {TOTAL_LINES:,} line Apache log...")
    filename = "large_demo_apache.log"
    path = os.path.join(OUT_DIR, filename)
    ts = START_TIME
    with open(path, "w", encoding="utf-8") as f:
        for i in range(1, TOTAL_LINES + 1):
            if i in GAP_LINES:
                ts += timedelta(seconds=GAP_LINES[i])
            else:
                ts += timedelta(seconds=interval(ts))
            if i in MALFORM_LINES:
                f.write(random.choice(MALFORM_POOL) + "\n")
            elif i in OOT_LINES:
                f.write(make_line(ts - timedelta(seconds=random.randint(30, 120))) + "\n")
            else:
                f.write(make_line(ts) + "\n")
            if i % 50000 == 0:
                print(f"  {i:>7,} / {TOTAL_LINES:,} lines written...")
    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"\nDone.")
    print(f"  File  : {filename}")
    print(f"  Lines : {TOTAL_LINES:,}")
    print(f"  Size  : {size_mb:.1f} MB")
    print(f"\nGaps injected:")
    for line_num, secs, label in GAPS:
        h, m = divmod(secs, 3600)
        m, s = divmod(m, 60)
        dur = f"{h}h {m}m {s}s" if h else f"{m}m {s}s"
        print(f"  Line {line_num:>7,} | {dur:>10} | {label}")
    print(f"\nUpload to http://localhost:5000")