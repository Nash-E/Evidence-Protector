"""
Generate sample log files in every format supported by Evidence Protector.
Each file has:
  - ~500 lines
  - 3 injected gaps (LOW, HIGH, CRITICAL)
  - 5 malformed lines
  - 1 out-of-order timestamp
Run: python sample_logs/generate_all_samples.py
"""

import random
import os
from datetime import datetime, timedelta

random.seed(99)
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Shared gap/malform injection config ─────────────────────────────────────

GAP_1_LINE   = 120   # ~120s  → LOW
GAP_2_LINE   = 280   # ~1000s → HIGH
GAP_3_LINE   = 400   # ~5000s → CRITICAL
OOT_LINE     = 350
MALFORM_LINES = {30, 90, 175, 310, 460}
TOTAL_LINES  = 500
START_TIME   = datetime(2025, 3, 28, 8, 0, 0)


def next_ts(ts, line_num):
    if line_num == GAP_1_LINE:
        return ts + timedelta(seconds=120)
    elif line_num == GAP_2_LINE:
        return ts + timedelta(seconds=1000)
    elif line_num == GAP_3_LINE:
        return ts + timedelta(seconds=5000)
    return ts + timedelta(seconds=random.randint(1, 4))


# ── 1. HDFS format ──────────────────────────────────────────────────────────

def gen_hdfs():
    components = ['dfs.DataNode', 'dfs.FSNamesystem', 'hdfs.StateChange']
    messages = [
        'Received block blk_{} of size {} from /10.0.0.{}',
        'Served block blk_{} to /10.0.0.{}',
        'PacketResponder terminated for block blk_{}',
        'BLOCK* replicate blk_{} to datanode',
    ]
    levels = ['INFO', 'INFO', 'WARN', 'ERROR']

    lines = []
    ts = START_TIME
    for i in range(1, TOTAL_LINES + 1):
        ts = next_ts(ts, i)
        if i in MALFORM_LINES:
            lines.append(random.choice(['', 'CORRUPTED ENTRY \\x00\\xff', 'PacketResponder block_missing']))
            continue
        if i == OOT_LINE:
            oot = ts - timedelta(seconds=20)
            ts_str = oot.strftime('%y%m%d %H%M%S')
        else:
            ts_str = ts.strftime('%y%m%d %H%M%S')
        pid = random.randint(1000, 9999)
        lvl = random.choice(levels)
        comp = random.choice(components)
        msg = random.choice(messages).format(
            random.randint(10000, 99999), random.randint(512, 65536), random.randint(1, 254)
        )
        lines.append(f'{ts_str} {pid} {lvl} {comp}: {msg}')

    _write('hdfs_sample.log', lines)


# ── 2. ISO 8601 (T separator) ────────────────────────────────────────────────

def gen_iso8601():
    services = ['auth', 'api', 'worker', 'scheduler']
    levels   = ['INFO', 'INFO', 'WARN', 'ERROR', 'DEBUG']
    msgs     = [
        'Request processed in {}ms',
        'User {} authenticated successfully',
        'Cache miss for key session:{}',
        'Database query took {}ms',
        'Worker {} started processing job {}',
    ]

    lines = []
    ts = START_TIME
    for i in range(1, TOTAL_LINES + 1):
        ts = next_ts(ts, i)
        if i in MALFORM_LINES:
            lines.append(random.choice(['', '--- log rotation ---', 'null pointer exception at 0x0']))
            continue
        if i == OOT_LINE:
            oot = ts - timedelta(seconds=15)
            ts_str = oot.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            ts_str = ts.strftime('%Y-%m-%dT%H:%M:%S')
        lvl  = random.choice(levels)
        svc  = random.choice(services)
        msg  = random.choice(msgs).format(random.randint(1, 500), random.randint(1000, 9999), random.randint(1, 100))
        lines.append(f'{ts_str} [{lvl}] {svc}: {msg}')

    _write('iso8601_sample.log', lines)


# ── 3. ISO 8601 with space separator ────────────────────────────────────────

def gen_iso_space():
    lines = []
    ts = START_TIME
    for i in range(1, TOTAL_LINES + 1):
        ts = next_ts(ts, i)
        if i in MALFORM_LINES:
            lines.append(random.choice(['', 'system: boot complete', 'ERR missing timestamp']))
            continue
        if i == OOT_LINE:
            oot = ts - timedelta(seconds=10)
            ts_str = oot.strftime('%Y-%m-%d %H:%M:%S')
        else:
            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
        lvl = random.choice(['INFO', 'INFO', 'WARN', 'ERROR'])
        lines.append(f'{ts_str} {lvl} app.server: Handled request {random.randint(1, 9999)} in {random.randint(1, 200)}ms')

    _write('iso_space_sample.log', lines)


# ── 4. Apache / Nginx access log ─────────────────────────────────────────────

def gen_apache():
    ips     = [f'192.168.1.{i}' for i in range(1, 20)]
    paths   = ['/index.html', '/api/v1/users', '/api/v1/login', '/static/app.js', '/favicon.ico']
    methods = ['GET', 'GET', 'POST', 'GET', 'DELETE']
    codes   = [200, 200, 200, 301, 404, 500]

    lines = []
    ts = START_TIME
    for i in range(1, TOTAL_LINES + 1):
        ts = next_ts(ts, i)
        if i in MALFORM_LINES:
            lines.append(random.choice(['', '::1 - - [] "-" 400 0', 'server restart']))
            continue
        if i == OOT_LINE:
            oot = ts - timedelta(seconds=25)
            ts_str = oot.strftime('%d/%b/%Y:%H:%M:%S')
        else:
            ts_str = ts.strftime('%d/%b/%Y:%H:%M:%S')
        ip     = random.choice(ips)
        method = random.choice(methods)
        path   = random.choice(paths)
        code   = random.choice(codes)
        size   = random.randint(200, 50000)
        lines.append(f'{ip} - - [{ts_str} +0000] "{method} {path} HTTP/1.1" {code} {size}')

    _write('apache_sample.log', lines)


# ── 5. Syslog ────────────────────────────────────────────────────────────────

def gen_syslog():
    hosts    = ['webserver01', 'dbserver02', 'proxy03']
    procs    = ['sshd', 'cron', 'kernel', 'systemd', 'sudo']
    msgs     = [
        'Accepted publickey for user{} from 10.0.0.{} port {}',
        'pam_unix(sshd:session): session opened for user{}',
        'CRON[{}]: (root) CMD (/usr/bin/backup.sh)',
        'UFW BLOCK IN=eth0 OUT= MAC SRC=10.0.0.{} DST=10.0.0.{} PROTO=TCP',
        'sudo: user{} : TTY=pts/{} ; PWD=/home ; USER=root ; COMMAND=/bin/ls',
    ]

    lines = []
    ts = START_TIME
    for i in range(1, TOTAL_LINES + 1):
        ts = next_ts(ts, i)
        if i in MALFORM_LINES:
            lines.append(random.choice(['', 'kernel: [    0.000000] BIOS-provided physical RAM', 'last message repeated 3 times']))
            continue
        if i == OOT_LINE:
            oot = ts - timedelta(seconds=12)
            # Syslog format: "Mar 15 08:03:45" — no year
            ts_str = oot.strftime('%b %d %H:%M:%S')
        else:
            ts_str = ts.strftime('%b %d %H:%M:%S')
        host = random.choice(hosts)
        proc = random.choice(procs)
        pid  = random.randint(100, 9999)
        msg  = random.choice(msgs).format(
            random.randint(1, 99), random.randint(1, 254), random.randint(1024, 65535)
        )
        lines.append(f'{ts_str} {host} {proc}[{pid}]: {msg}')

    _write('syslog_sample.log', lines)


# ── helpers ──────────────────────────────────────────────────────────────────

def _write(filename, lines):
    path = os.path.join(OUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'  Created {filename} ({len(lines)} lines)')


if __name__ == '__main__':
    print('Generating sample log files...')
    gen_hdfs()
    gen_iso8601()
    gen_iso_space()
    gen_apache()
    gen_syslog()
    print(f'\nAll files saved to: {OUT_DIR}')
    print('Each file has 3 gaps (LOW ~120s, HIGH ~1000s, CRITICAL ~5000s), 5 malformed lines, 1 out-of-order timestamp.')
    print('\nUpload any of them to http://localhost:5000')
