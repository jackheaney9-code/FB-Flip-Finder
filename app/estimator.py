from typing import Optional, Dict

def estimate_profit(fb_price: Optional[float], ebay_avg: Optional[float], fee_rate: float = 0.13) -> Dict[str, Optional[float]]:
    if fb_price is None or ebay_avg is None:
        return {"profit": None, "roi_percent": None}
    net = ebay_avg * (1.0 - fee_rate)
    profit = net - fb_price
    roi = (profit / fb_price) * 100.0 if fb_price and fb_price > 0 else None
    return {"profit": round(profit, 2), "roi_percent": round(roi, 1) if roi is not None else None}

def decision_label(profit: Optional[float], roi: Optional[float]) -> str:
    if profit is None or roi is None:
        return "🤷 Not enough data"
    if profit >= 50 and roi >= 40:
        return "✅ Buy — strong flip potential"
    if profit >= 20 and roi >= 20:
        return "👍 Maybe — moderate upside"
    return "⚠️ Pass — weak margins"
