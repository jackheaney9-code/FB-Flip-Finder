import re
from decimal import Decimal

def parse_price(text: str):
    if not text:
        return None, "CAD"
    t = text.strip()
    if "free" in t.lower():
        return 0.0, "CAD"
    nums = re.findall(r"[\d,]+(?:\.\d{1,2})?", t.replace(",", ""))
    if not nums:
        return None, "CAD"
    # convert to float so it is always JSON-serializable
    return float(Decimal(nums[0])), "CAD"
