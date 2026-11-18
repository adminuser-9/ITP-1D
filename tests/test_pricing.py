import unittest

from constants import QUANTITY_FIELDS
from mylibrary import (
    calculate_booking, calculate_family_cost, calculate_group_cost, percentage, validate_booking,
)
from presenter import (
    booking_changed, build_receipt_text, capacity_status, compare_periods, money,
    offer_comparison, receipt_table, reset_booking, submit_booking,
)


def booking_data(**changes):
    booking = dict.fromkeys(QUANTITY_FIELDS, 0)
    booking["period"] = "Peak"
    booking.update(changes)
    return booking


class PricingTests(unittest.TestCase):
    def test_separate_family_and_group_costs(self):
        self.assertIsNone(calculate_family_cost(booking_data(adults=2, children=1)))
        self.assertIsNone(calculate_group_cost(booking_data(adults=9, infants=1)))
        for period, family_cost, group_cost in (("Peak", 6700, 6480), ("Off-Peak", 5360, 5184)):
            booking = booking_data(adults=2, children=2, seniors=6, guides=3, period=period)
            original = booking.copy()
            family = calculate_family_cost(booking)
            group = calculate_group_cost(booking)
            self.assertEqual(family["cost_cents"], family_cost)
            self.assertEqual(group["cost_cents"], group_cost)
            self.assertEqual(sum(i["subtotal_cents"] for i in family["items"]), family_cost)
            self.assertEqual(sum(i["subtotal_cents"] for i in group["items"]), group_cost)
            self.assertEqual(booking, original)
        repeated = calculate_family_cost(booking_data(adults=5, children=4))
        self.assertEqual(repeated["cost_cents"], 6000)

    def test_live_capacity_includes_infants_and_handles_overflow(self):
        for values, total, remaining, excess in (
            (booking_data(), 0, 20, 0),
            (booking_data(adults=2, children=4, infants=2), 8, 12, 0),
            (booking_data(adults=19, infants=1), 20, 0, 0),
            (booking_data(adults=20, infants=3), 23, 0, 3),
        ):
            with self.subTest(total=total):
                status = capacity_status(values)
                self.assertEqual((status["total"], status["remaining"], status["excess"]),
                                 (total, remaining, excess))
                self.assertLessEqual(status["progress"], 1)
                self.assertGreaterEqual(status["progress"], 0)
        self.assertIn("Remove 3", capacity_status(booking_data(adults=20, infants=3))["message"])

    def test_period_comparison_uses_submitted_booking_and_keeps_extras(self):
        result = calculate_booking(booking_data(adults=2, children=2, guides=2))
        peak, off_peak = compare_periods(result)
        self.assertEqual((peak["total_cents"], off_peak["total_cents"]), (3100, 2600))
        self.assertEqual(peak["extras_cents"], off_peak["extras_cents"])
        self.assertEqual(result["booking"]["period"], "Peak")
        infant = calculate_booking(booking_data(infants=1))
        self.assertEqual([r["total_cents"] for r in compare_periods(infant)], [0, 0])

    def test_receipt_explanations_and_changed_inputs(self):
        values = booking_data(adults=4, children=12)
        result = calculate_booking(values)
        self.assertFalse(booking_changed(values, result))
        values["guides"] = 1
        self.assertTrue(booking_changed(values, result))
        comparison = "\n".join(offer_comparison(result))
        self.assertIn("Selected", comparison)
        self.assertIn("Same price", comparison)
        self.assertIn("$10.00 more", comparison)
        self.assertIn("**$90.00**", receipt_table(result))
        ineligible = "\n".join(offer_comparison(calculate_booking(booking_data(adults=1))))
        self.assertIn("requires 2 adults and 2 children", ineligible)
        self.assertIn("requires 10 paying visitors", ineligible)

    def test_hand_calculated_examples(self):
        examples = [
            (booking_data(adults=1, children=1), "Standard", 1500, 0),
            (booking_data(adults=2, children=2, guides=2), "Family", 2500, 600),
            (booking_data(adults=2, children=2, guides=2, period="Off-Peak"), "Family", 2000, 600),
            (booking_data(adults=3, children=2, booklets=1), "Family", 3500, 400),
            (booking_data(adults=4, children=4), "Family", 5000, 0),
            (booking_data(adults=10), "Group", 9000, 0),
            (booking_data(adults=10, period="Off-Peak"), "Group", 7200, 0),
            (booking_data(adults=2, children=2, seniors=6), "Group", 6480, 0),
            (booking_data(seniors=1, infants=1, guides=1, period="Off-Peak"), "Standard", 560, 300),
            (booking_data(infants=1), "Standard", 0, 0),
            (booking_data(adults=2, children=2, seniors=7), "Group", 7110, 0),
            (booking_data(adults=4, children=12), "Family", 9000, 0),
        ]
        for booking, offer, admission, extras in examples:
            with self.subTest(booking=booking):
                result = calculate_booking(booking)
                self.assertEqual(result["applied_offer"], offer)
                self.assertEqual(result["admission_cents"], admission)
                self.assertEqual(result["extras_cents"], extras)
                self.assertEqual(result["total_cents"], admission + extras)

    def test_eligibility_boundaries(self):
        cases = [
            (booking_data(adults=9, infants=1), "Group", False),
            (booking_data(adults=10), "Group", True),
            (booking_data(adults=1, children=2), "Family", False),
            (booking_data(adults=2, children=1), "Family", False),
            (booking_data(adults=2, children=2), "Family", True),
        ]
        for booking, name, eligible in cases:
            with self.subTest(booking=booking):
                price = calculate_booking(booking)["offer_prices_cents"][name]
                self.assertEqual(price is not None, eligible)

    def test_validation_boundaries(self):
        for booking in (booking_data(adults=20, guides=20, booklets=20), booking_data(infants=20)):
            self.assertEqual(validate_booking(booking), [])
            calculate_booking(booking)
        invalid = [booking_data(), booking_data(adults=21), booking_data(adults=20, infants=1),
                   booking_data(adults=1, guides=2), booking_data(adults=1, booklets=21),
                   booking_data(infants=1, booklets=1), booking_data(infants=1, guides=1),
                   booking_data(adults=1, period="Holiday"), booking_data(adults=1, period=None)]
        for field in ("adults", "children", "seniors", "infants", "guides", "booklets"):
            invalid.extend(booking_data(**{"adults": 1, field: value})
                           for value in (-1, True, 1.5, "1", None))
        for booking in invalid:
            with self.subTest(booking=booking):
                self.assertTrue(validate_booking(booking))
                with self.assertRaises(ValueError) as error:
                    calculate_booking(booking)
                self.assertTrue(str(error.exception))
        with self.assertRaises(ValueError):
            calculate_booking({"adults": 1})

    def test_family_wins_tie_with_group(self):
        result = calculate_booking(booking_data(adults=4, children=12))
        self.assertEqual(result["offer_prices_cents"]["Family"], 9000)
        self.assertEqual(result["offer_prices_cents"]["Group"], 9000)
        self.assertEqual(result["applied_offer"], "Family")

    def test_extras_are_not_discounted_and_savings_are_separate(self):
        for period, total in (("Peak", 3100), ("Off-Peak", 2600)):
            result = calculate_booking(booking_data(adults=2, children=2, guides=2, period=period))
            self.assertEqual(result["total_cents"], total)
            self.assertEqual(result["extras_cents"], 600)
        result = calculate_booking(booking_data(adults=2, children=2, period="Off-Peak"))
        self.assertEqual(result["period_savings_cents"], 600)
        self.assertEqual(result["offer_savings_cents"], 400)

    def test_receipts_reconcile_across_valid_baskets(self):
        for adults in range(0, 11):
            for children in range(0, 7):
                for seniors in (0, 1, 6):
                    if not 1 <= adults + children + seniors <= 20:
                        continue
                    for period in ("Peak", "Off-Peak"):
                        booking = booking_data(adults=adults, children=children, seniors=seniors,
                                          guides=1, booklets=2, period=period)
                        result = calculate_booking(booking)
                        with self.subTest(booking=booking):
                            self.assertEqual(result, calculate_booking(booking))
                            self.assertIs(type(result["total_cents"]), int)
                            self.assertGreaterEqual(result["total_cents"], 0)
                            self.assertEqual(result["admission_cents"],
                                             min(price for price in result["offer_prices_cents"].values() if price is not None))
                            self.assertLessEqual(result["admission_cents"], result["period_standard_cents"])
                            self.assertEqual(sum(i["subtotal_cents"] for i in result["admission_items"]),
                                             result["admission_cents"])
                            self.assertEqual(sum(i["subtotal_cents"] for i in result["extras_items"]), result["extras_cents"])
                            self.assertEqual(result["total_cents"], result["admission_cents"] + result["extras_cents"])
                            for item in (*result["admission_items"], *result["extras_items"]):
                                self.assertEqual(item["quantity"] * item["unit_price_cents"], item["subtotal_cents"])

    def test_form_edits_do_not_change_saved_receipt(self):
        booking = booking_data(adults=2)
        result = calculate_booking(booking)
        booking["adults"] = 3
        self.assertEqual(result["booking"]["adults"], 2)
        self.assertEqual(result["total_cents"], 2000)

    def test_presenter_submission_and_reset(self):
        state = booking_data(adults=2, children=2, guides=2)
        result, errors = submit_booking(state)
        self.assertEqual(errors, [])
        self.assertEqual(result["total_cents"], 3100)
        state["last_result"] = result
        state["guides"] = 5
        result, errors = submit_booking(state)
        self.assertIsNone(result)
        self.assertTrue(errors)
        reset_booking(state)
        self.assertNotIn("last_result", state)
        self.assertEqual(state, booking_data())

    def test_rounding_and_receipt_formatting(self):
        self.assertEqual(percentage(5, 90), 5)  # 4.5 cents rounds up
        self.assertEqual(percentage(4, 90), 4)
        self.assertEqual(money(-12345), "-$123.45")
        self.assertEqual(money(0), "$0.00")
        result = calculate_booking(booking_data(adults=10, guides=1, booklets=1, period="Off-Peak"))
        receipt = build_receipt_text(result)
        for text in ("Period: Off-Peak", "Selected offer: Group", "TOTAL: $79.00",
                     "Group discount (10%): 1 x -$8.00 = -$8.00", "Extras: $7.00"):
            self.assertIn(text, receipt)
