import unittest
from datetime import date, time

from streamlit_app import _application_status_label, home_visit_payload


class StreamlitApplicationHelpersTest(unittest.TestCase):
    def test_home_visit_payload_includes_italian_timezone_offset(self):
        payload = home_visit_payload("  Ada Rossi  ", date(2026, 1, 15), time(17, 30), "  Prima visita  ")

        self.assertEqual(payload["evaluator_name"], "Ada Rossi")
        self.assertEqual(payload["scheduled_date"], "2026-01-15T17:30:00+01:00")
        self.assertEqual(payload["report_notes"], "Prima visita")

    def test_application_statuses_have_italian_labels(self):
        self.assertEqual(_application_status_label("HOME_VISIT"), "Visita pre-affido programmata")
        self.assertEqual(_application_status_label("APPROVED"), "Approvata")


if __name__ == "__main__":
    unittest.main()
