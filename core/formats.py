import re
from datetime import datetime
from typing import Optional, List, Callable, NamedTuple
class LogFormat(NamedTuple):
    name: str
    pattern: str
    parse_fn: Callable[[str], Optional[datetime]]
    display_name: str
def _safe(fn):
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