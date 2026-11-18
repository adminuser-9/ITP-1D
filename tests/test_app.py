"""Exercise actual Streamlit reruns and state, without a browser."""

from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


class AppTests(unittest.TestCase):
    def test_capacity_updates_without_calculation_and_blocks_overflow(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        app.number_input(key="adults").set_value(19).run()
        self.assertTrue(any("1 place remaining" in c.value for c in app.caption))
        app.number_input(key="infants").set_value(1).run()
        self.assertTrue(any("Booking capacity reached" in s.value for s in app.success))
        app.number_input(key="children").set_value(3).run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Remove 3" in e.value for e in app.error))
        self.assertTrue(app.button(key="calculate").disabled)
        app.number_input(key="children").set_value(0).run()
        self.assertFalse(app.button(key="calculate").disabled)
        app.button(key="reset").click().run()
        self.assertTrue(any("20 places remaining" in c.value for c in app.caption))

    def test_receipt_download_matches_saved_calculation(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        app.number_input(key="adults").set_value(2)
        app.number_input(key="children").set_value(2)
        app.number_input(key="guides").set_value(2)
        with patch("streamlit.download_button") as download:
            app.button(key="calculate").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(download.call_args.kwargs["mime"], "text/plain")
            self.assertIn("TOTAL: $31.00", download.call_args.kwargs["data"])
            self.assertIn("Period: Peak", download.call_args.kwargs["data"])
        self.assertTrue(any("$26.00" in m.value for m in app.markdown))

    def test_submit_rerun_invalid_and_reset(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        self.assertFalse(app.exception)
        app.number_input(key="adults").set_value(2)
        app.number_input(key="children").set_value(2)
        app.number_input(key="guides").set_value(2)
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "$31.00")
        self.assertEqual(app.session_state["last_result"]["applied_offer"], "Family")
        app.run()
        self.assertEqual(app.metric[0].value, "$31.00")
        app.number_input(key="adults").set_value(3).run()
        self.assertEqual(app.metric[0].value, "$31.00")
        self.assertTrue(any("Inputs have changed" in w.value for w in app.warning))
        self.assertEqual(app.session_state["last_result"]["booking"]["adults"], 2)
        app.number_input(key="adults").set_value(2)
        app.radio(key="period").set_value("Off-Peak")
        app.button[0].click().run()
        self.assertEqual(app.metric[0].value, "$26.00")
        app.number_input(key="guides").set_value(5)
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)
        self.assertEqual(len(app.metric), 0)
        app.button[1].click().run()
        self.assertFalse(app.exception)
        for field in ("adults", "children", "seniors", "infants", "guides", "booklets"):
            self.assertEqual(app.number_input(key=field).value, 0)
        self.assertEqual(app.radio(key="period").value, "Peak")
        self.assertEqual(len(app.metric), 0)

    def test_group_and_free_infant_booking(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        app.number_input(key="adults").set_value(10)
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "$90.00")
        app.button[1].click().run()
        app.number_input(key="infants").set_value(1)
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "$0.00")
