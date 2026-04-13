import re
from datetime import datetime
from typing import Optional, List, Callable, NamedTuple
class LogFormat(NamedTuple):
    name: str
    pattern: str
    parse_fn: Callable[[str], Optional[datetime]]
    display_name: str
def _safe(fn):
    def wrapper(raw: str) -> Optional[datetime]:
        try:
            return fn(raw)
        except Exception:
            return None
    return wrapper

@_safe
def _parse_hdfs(raw: str) -> Optional[datetime]:
    return datetime.strptime(raw, '%y%m%d %H%M%S')

@_safe
def _parse_iso8601(raw: str) -> Optional[datetime]:
    s = raw.split('+')[0].split('Z')[0].replace('T', ' ')
    if '.' in s:
        s = s[:s.index('.')]
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

@_safe
def _parse_apache(raw: str) -> Optional[datetime]:
    return datetime.strptime(raw, '%d/%b/%Y:%H:%M:%S')

@_safe
def _parse_syslog(raw: str) -> Optional[datetime]:
    year = datetime.now().year
    normalized = ' '.join(raw.split())
    dt = datetime.strptime(f"{year} {normalized}", '%Y %b %d %H:%M:%S')
    return dt

@_safe
def _parse_epoch(raw: str) -> Optional[datetime]:
    return datetime.fromtimestamp(float(raw))

@_safe
def _parse_iso_date_space(raw: str) -> Optional[datetime]:
    s = raw
    if '.' in s:
        s = s[:s.index('.')]
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

@_safe
def _parse_common_log(raw: str) -> Optional[datetime]:
    return datetime.strptime(raw, '%d/%b/%Y:%H:%M:%S')

FORMATS: List[LogFormat] = [
    LogFormat('hdfs',         r'\b(\d{6} \d{6})\b',                                    _parse_hdfs,         'HDFS / Android'),
    LogFormat('iso8601',      r'\b(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',              _parse_iso8601,      'ISO 8601'),
    LogFormat('iso_space',    r'\b(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',              _parse_iso_date_space, 'ISO 8601 (space)'),
    LogFormat('apache',       r'\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})',              _parse_apache,       'Apache / Nginx'),
    LogFormat('syslog',       r'\b([A-Z][a-z]{2}\s{1,2}\d{1,2} \d{2}:\d{2}:\d{2})\b', _parse_syslog,       'Syslog'),
    LogFormat('epoch',        r'\b(1[0-9]{9}(?:\.\d+)?)\b',                             _parse_epoch,        'Unix Epoch'),
]

PROBE_LINES = 100

def detect_format(filepath: str) -> LogFormat:
    scores = {fmt.name: 0 for fmt in FORMATS}
    compiled = [(fmt, re.compile(fmt.pattern)) for fmt in FORMATS]
    with open(filepath, encoding='utf-8', errors='replace') as fh:
        for i, line in enumerate(fh):
            if i >= PROBE_LINES:
                break
            line = line.strip()
            if not line:
                continue
            for fmt, rx in compiled:
                m = rx.search(line)
                if m and fmt.parse_fn(m.group(1)) is not None:
                    scores[fmt.name] += 1
    best = max(FORMATS, key=lambda f: scores[f.name])
    if scores[best.name] == 0:
        raise ValueError('No recognizable timestamp format found in the first 100 lines. Supported formats: HDFS, ISO 8601, Apache/Nginx, Syslog, Unix Epoch.')
    return best