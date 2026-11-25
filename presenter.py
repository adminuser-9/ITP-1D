from constants import (
    BOOKLET_PRICE, FAMILY_PRICE, GROUP_MINIMUM, GROUP_PERCENT, GUIDE_PRICE,
    MAX_BOOKLETS, MAX_VISITORS, OFF_PEAK_PERCENT, PERIODS, QUANTITY_FIELDS, VISITOR_CATEGORIES,
)
from mylibrary import calculate_booking, period_price, validate_booking


def submit_booking(values):
    """Return (receipt, errors); the view decides how to display them."""
    booking = {field: values.get(field) for field in (*QUANTITY_FIELDS, "period")}
    errors = validate_booking(booking)
    if errors:
        return None, errors
    return calculate_booking(booking), []


def reset_booking(state):
    for field in QUANTITY_FIELDS:
        state[field] = 0
    state["period"] = "Peak"
    state.pop("last_result", None)


def money(cents):
    sign = "-" if cents < 0 else ""
    dollars, remainder = divmod(abs(cents), 100)
    return f"{sign}${dollars:,}.{remainder:02d}"


def build_receipt_text(result):
    booking = result["booking"]
    lines = ["Tales of Lanfang — Ticket Receipt", "All amounts in SGD",
             f"Period: {booking['period']}",
             f"Visitors: {result['visitor_count']} ({booking['adults']} adults, "
             f"{booking['children']} children, {booking['seniors']} seniors, {booking['infants']} infants)",
             f"Selected offer: {result['applied_offer']}", result["explanation"], ""]
    for item in result["admission_items"] + result["extras_items"]:
        lines.append(f"{item['label']}: {item['quantity']} x {money(item['unit_price_cents'])}"
                     f" = {money(item['subtotal_cents'])}")
    for label, field in (
        ("Admission", "admission_cents"), ("Extras", "extras_cents"), ("TOTAL", "total_cents"),
        ("Standard admission for this period", "period_standard_cents"),
        ("Offer savings against this period", "offer_savings_cents"),
        ("Period savings against Peak standard", "period_savings_cents"),
    ):
        lines.append(f"{label}: {money(result[field])}")
    return "\n".join(lines)


def offer_comparison(result):
    lines = []
    for name, price in result["offer_prices_cents"].items():
        if price is not None:
            if name == result["applied_offer"]:
                reason = "Selected — cheapest eligible admission; ties prefer Standard, Family, then Group."
            elif price == result["admission_cents"]:
                reason = "Same price as the selected offer; the tie rule applies."
            else:
                reason = f"Eligible, but costs {money(price - result['admission_cents'])} more."
            lines.append(f"{name}: {money(price)} — {reason}")
        elif name == "Family":
            lines.append("Family: not eligible — requires 2 adults and 2 children.")
        else:
            lines.append(f"Group: not eligible — requires {GROUP_MINIMUM} paying visitors.")
    return lines


def capacity_status(values):
    """Capacity is per booking and includes free infants, not venue availability."""
    total = sum(values.get(field, 0) for field, _, _ in VISITOR_CATEGORIES)
    remaining = max(0, MAX_VISITORS - total)
    excess = max(0, total - MAX_VISITORS)
    if excess:
        message = f"Remove {excess} visitor(s) to continue."
    elif remaining == 0:
        message = "Booking capacity reached."
    else:
        place = "place" if remaining == 1 else "places"
        message = f"{remaining} {place} remaining in this booking."
    return {"total": total, "remaining": remaining, "excess": excess,
            "progress": min(total / MAX_VISITORS, 1.0), "message": message}


def booking_changed(values, result):
    return any(values.get(field) != result["booking"][field]
               for field in (*QUANTITY_FIELDS, "period"))


def receipt_table(result):
    rows = ["| Item | Quantity | Unit price | Amount |", "| --- | ---: | ---: | ---: |"]
    for item in result["admission_items"] + result["extras_items"]:
        rows.append(f"| {item['label']} | {item['quantity']} | {money(item['unit_price_cents'])} "
                    f"| {money(item['subtotal_cents'])} |")
    rows.append(f"| **Total (SGD)** | | | **{money(result['total_cents'])}** |")
    return "\n".join(rows)


def compare_periods(result):
    comparisons = []
    for period in PERIODS:
        booking = result["booking"].copy()
        booking["period"] = period
        comparisons.append(calculate_booking(booking))
    return comparisons


def pricing_guide():
    lines = ["All prices are in SGD. Choose the visit period manually."]
    for _, label, price in VISITOR_CATEGORIES:
        lines.append(f"{label}: {money(price)}")
    lines.extend([
        f"Audio guide: {money(GUIDE_PRICE)}; souvenir booklet: {money(BOOKLET_PRICE)}.",
        f"Off-Peak: {100 - OFF_PEAK_PERCENT}% off admission, including family bundles.",
        f"Family: 2 adults + 2 children for {money(FAMILY_PRICE)} Peak or "
        f"{money(period_price(FAMILY_PRICE, 'Off-Peak'))} Off-Peak; repeat bundles allowed.",
        f"Group: {GROUP_MINIMUM}+ paying visitors receive {100 - GROUP_PERCENT}% off period admission.",
        "Family and Group do not stack. Extras are never discounted. "
        "Ties prefer Standard, then Family, then Group.",
        f"Bookings allow 1-{MAX_VISITORS} visitors including infants, at most one guide per "
        f"paying visitor, and up to {MAX_BOOKLETS} booklets. Extras require a paying visitor.",
    ])
    return lines
