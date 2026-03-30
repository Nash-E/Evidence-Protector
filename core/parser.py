import re
from datetime import datetime
from typing import Generator, Optional, Tuple, Callable

def line_generator(filepath: str) -> Generator[Tuple[int, str], None, None]:
    """Yield (1-indexed line_number, stripped line) one at a time. Never loads full file."""
    with open(filepath, encoding='utf-8', errors='replace') as fh:
        for line_num, line in enumerate(fh, start=1):
            yield line_num, line.rstrip('\n')

def parse_line(line: str, compiled_rx, parse_fn: Callable[[str], Optional[datetime]]) -> Optional[datetime]:
    """Extract and parse a timestamp from a line. Returns None on any failure, never raises."""
    try:
        m = compiled_rx.search(line)
        if m is None:
            return None
        return parse_fn(m.group(1))
    except Exception:
        return None
