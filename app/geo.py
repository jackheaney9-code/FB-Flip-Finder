import re
from typing import Optional
_dist_re = re.compile(r"Within\s+(\d+)\s*km", re.I)

def parse_fb_distance_km(location_text: str | None) -> Optional[float]:
    if not location_text:
        return None
    m = _dist_re.search(location_text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None
