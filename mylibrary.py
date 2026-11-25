from constants import (
    ADULT_PRICE, BOOKLET_PRICE, CHILD_PRICE, FAMILY_PRICE, GROUP_MINIMUM,
    GROUP_PERCENT, GUIDE_PRICE, MAX_BOOKLETS, MAX_VISITORS, OFF_PEAK_PERCENT,
    PERIODS, QUANTITY_FIELDS, VISITOR_CATEGORIES,
)


def validate_quantity(value):
    return type(value) is int and value >= 0


def calculate_total(adults, children):
    """Original assignment: return adult and child subtotals in dollars."""
    if not validate_quantity(adults) or not validate_quantity(children):
        raise ValueError("Quantities must be nonnegative whole numbers.")
    return adults * ADULT_PRICE // 100, children * CHILD_PRICE // 100


def audio_guides(items):
    """Original assignment: return the guide subtotal in dollars."""
    if not validate_quantity(items):
        raise ValueError("Quantity must be a nonnegative whole number.")
    return items * GUIDE_PRICE // 100


def percentage(amount, percent):
    """Round a nonnegative cent amount half up; avoid floating-point money."""
    return (amount * percent + 50) // 100


def period_price(price, period):
    if period == "Off-Peak":
        return percentage(price, OFF_PEAK_PERCENT)
    return price


def validate_booking(booking):
    """Return readable errors. Check types before calculating totals."""
    if not isinstance(booking, dict):
        return ["Please supply a booking dictionary."]
    errors = []
    for field in QUANTITY_FIELDS:
        if not validate_quantity(booking.get(field)):
            errors.append(f"{field.capitalize()} must be a nonnegative whole number.")
    if booking.get("period") not in PERIODS:
        errors.append("Choose Peak or Off-Peak.")
    if errors:
        return errors

    paying = booking["adults"] + booking["children"] + booking["seniors"]
    if not 1 <= paying + booking["infants"] <= MAX_VISITORS:
        errors.append(f"A booking must contain 1-{MAX_VISITORS} visitors, including infants.")
    if booking["guides"] > paying:
        errors.append("Audio guides cannot exceed the number of paying visitors.")
    if booking["booklets"] > MAX_BOOKLETS:
        errors.append(f"A booking can include at most {MAX_BOOKLETS} booklets.")
    if paying == 0 and (booking["guides"] or booking["booklets"]):
        errors.append("Extras require at least one paying visitor.")
    return errors


def line_item(label, quantity, unit_price):
    return {"label": label, "quantity": quantity, "unit_price_cents": unit_price,
            "subtotal_cents": quantity * unit_price}


def admission_items(booking):
    items = []
    for field, label, price in VISITOR_CATEGORIES:
        count = booking[field]
        if count:
            items.append(line_item(label, count, period_price(price, booking["period"])))
    return items


def subtotal(items):
    return sum(item["subtotal_cents"] for item in items)


def calculate_family_cost(booking):
    """For a validated booking, return Family admission details or None.

    Extras are excluded. Complete bundles repeat; remaining visitors pay
    the selected period's standard rates. Prices are integer cents.
    """
    bundles = min(booking["adults"] // 2, booking["children"] // 2)
    if bundles == 0:
        return None
    remaining = booking.copy()
    remaining["adults"] -= 2 * bundles
    remaining["children"] -= 2 * bundles
    items = [line_item("Family bundle (2 adults + 2 children)", bundles,
                       period_price(FAMILY_PRICE, booking["period"]))]
    items.extend(admission_items(remaining))
    return {"cost_cents": subtotal(items), "items": items,
            "explanation": f"{bundles} family bundle(s); remaining visitors pay period rates."}


def calculate_group_cost(booking):
    """For a validated booking, return Group admission details or None.

    Count paying visitors only. Apply the discount to period-adjusted
    standard admission, independently of Family pricing; exclude extras.
    """
    paying = booking["adults"] + booking["children"] + booking["seniors"]
    if paying < GROUP_MINIMUM:
        return None
    items = admission_items(booking)
    standard = subtotal(items)
    cost = percentage(standard, GROUP_PERCENT)
    discount = cost - standard
    items.append(line_item(f"Group discount ({100 - GROUP_PERCENT}%)", 1, discount))
    return {"cost_cents": cost, "items": items,
            "explanation": f"{100 - GROUP_PERCENT}% off standard admission for the selected period."}


def calculate_booking(booking):
    errors = validate_booking(booking)
    if errors:
        raise ValueError(" ".join(errors))
    booking = booking.copy()  # Form edits must not change a saved receipt.
    paying = booking["adults"] + booking["children"] + booking["seniors"]
    items = admission_items(booking)
    standard = subtotal(items)
    peak_standard = sum(booking[field] * price for field, _, price in VISITOR_CATEGORIES)
    admission = standard
    selected = "Standard"
    explanation = "Standard admission at the selected period's rates."
    offers = {"Standard": standard, "Family": None, "Group": None}

    family = calculate_family_cost(booking)
    if family is not None:
        offers["Family"] = family["cost_cents"]
        if family["cost_cents"] < admission:
            selected = "Family"
            admission = family["cost_cents"]
            items = family["items"]
            explanation = family["explanation"]

    group = calculate_group_cost(booking)
    if group is not None:
        offers["Group"] = group["cost_cents"]
        if group["cost_cents"] < admission:
            selected = "Group"
            admission = group["cost_cents"]
            items = group["items"]
            explanation = group["explanation"]

    extras = []
    if booking["guides"]:
        extras.append(line_item("Audio guides", booking["guides"], GUIDE_PRICE))
    if booking["booklets"]:
        extras.append(line_item("Souvenir booklets", booking["booklets"], BOOKLET_PRICE))
    extras_total = subtotal(extras)
    return {
        "booking": booking, "visitor_count": paying + booking["infants"], "paying_count": paying,
        "peak_standard_cents": peak_standard, "period_standard_cents": standard,
        "offer_prices_cents": offers, "applied_offer": selected, "explanation": explanation,
        "admission_items": items, "extras_items": extras, "admission_cents": admission,
        "offer_savings_cents": standard - admission,
        "period_savings_cents": peak_standard - standard,
        "extras_cents": extras_total, "total_cents": admission + extras_total,
    }
