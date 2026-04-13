import re
from datetime import datetime
from typing import Generator, Optional, Tuple, Callable
def line_generator(filepath: str) -> Generator[Tuple[int, str], None, None]:
    try:
        m = compiled_rx.search(line)
        if m is None:
            return None
        return parse_fn(m.group(1))
    except Exception:
        return None