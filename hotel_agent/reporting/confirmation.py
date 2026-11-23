"""Booking confirmations as plain text and as a printable HTML page."""
from html import escape
from typing import Dict, List, Optional

from hotel_agent.config import CHECK_IN_TIME, CHECK_OUT_TIME, HOTEL_NAME, format_money


def _service_total(orders: Optional[List[Dict]]) -> float:
    return sum(o["total_price"] for o in (orders or []) if o.get("status") != "Cancelled")


def build_confirmation_text(details: Dict, orders: Optional[List[Dict]] = None) -> str:
    orders = [o for o in (orders or []) if o.get("status") != "Cancelled"]
    lines = [
        "=" * 56, f"  {HOTEL_NAME.upper()} - BOOKING CONFIRMATION", "=" * 56,
        "-" * 56,
        f"Reference     : {details['reference']}",
        f"Status        : {details['status']}",
        f"Booked on     : {details['created_at']}", "",
        "GUEST",
        f"  Name        : {details['customer']}",
        f"  Email       : {details['email']}",
        f"  Phone       : {details['phone']}", "",
        "STAY",
        f"  Room        : {details['room_number']} - {details['room_name']} ({details['accommodation_type']})",
        f"  Location    : {details['location']}",
        f"  Check-in    : {details['check_in']} (from {CHECK_IN_TIME})",
        f"  Check-out   : {details['check_out']} (by {CHECK_OUT_TIME})",
        f"  Nights      : {details['nights']}",
        f"  Guests      : {details['guests']}",
        f"  Amenities   : {details['amenities']}", "",
        "CHARGES",
        f"  Room        : {details['nights']} x {format_money(details['price_per_night'])} = {format_money(details['total_price'])}",
    ]
    for o in orders:
        lines.append(f"  {o['service'][:22]:<22}: {o['quantity']} x = {format_money(o['total_price'])}")
    grand = details["total_price"] + _service_total(orders)
    lines += ["  " + "-" * 40, f"  TOTAL       : {format_money(grand)}", ""]
    if details.get("notes"):
        lines += [f"Notes: {details['notes']}", ""]
    lines += ["-" * 56, "=" * 56]
    return "\n".join(lines)


def build_confirmation_html(details: Dict, orders: Optional[List[Dict]] = None) -> str:
    orders = [o for o in (orders or []) if o.get("status") != "Cancelled"]
    e = escape
    rows = (f"<tr><td>Room {e(str(details['room_number']))} - {e(details['room_name'])}</td>"
            f"<td>{details['nights']} x {format_money(details['price_per_night'])}</td>"
            f"<td class='r'>{format_money(details['total_price'])}</td></tr>")
    for o in orders:
        rows += (f"<tr><td>{e(o['service'])}</td><td>{o['quantity']} x</td>"
                 f"<td class='r'>{format_money(o['total_price'])}</td></tr>")
    grand = details["total_price"] + _service_total(orders)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Booking {e(details['reference'])}</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;color:#1b2a2f;max-width:720px;margin:32px auto;padding:0 20px}}
h1{{font-family:Georgia,serif;color:#12403c;margin-bottom:4px}}
table{{width:100%;border-collapse:collapse;margin:14px 0}}
td,th{{padding:8px 6px;border-bottom:1px solid #d8e0e2;text-align:left}} .r{{text-align:right}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:6px 24px}} .k{{color:#5e6e73}}
.total{{font-size:1.25rem;font-weight:700;color:#12403c}} small{{color:#5e6e73}}
</style></head><body>
<h1>{e(HOTEL_NAME)}</h1><p>Booking confirmation</p>
<h2>{e(details['reference'])} &middot; {e(details['status'])}</h2>
<div class="grid">
<div><span class="k">Guest</span><br>{e(details['customer'])}<br>{e(details['email'])}<br>{e(details['phone'])}</div>
<div><span class="k">Room</span><br>{e(str(details['room_number']))} - {e(details['room_name'])}<br>{e(details['accommodation_type'])}, {e(details['location'])}</div>
<div><span class="k">Check-in</span><br>{e(details['check_in'])} (from {CHECK_IN_TIME})</div>
<div><span class="k">Check-out</span><br>{e(details['check_out'])} (by {CHECK_OUT_TIME})</div>
<div><span class="k">Guests</span><br>{details['guests']}</div>
<div><span class="k">Amenities</span><br>{e(details['amenities'])}</div>
</div>
<table><tr><th>Item</th><th>Quantity</th><th class="r">Amount</th></tr>{rows}</table>
<p class="total">Total: {format_money(grand)}</p>
</body></html>"""