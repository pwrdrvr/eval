import tempfile
import unittest
from pathlib import Path
from ledger import Ledger


class BudgetTests(unittest.TestCase):
    def test_resume_and_uncertain_spend_cannot_release_budget(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'ledger.sqlite'
            a = Ledger(path, 10)
            a.reserve('one', 7)
            b = Ledger(path, 10)
            with self.assertRaises(ValueError): b.reserve('two', 4)
            with self.assertRaises(ValueError): b.reserve('one', 1)
            b.settle('one', 0, uncertain=True)
            self.assertEqual(a.snapshot()['remaining_usd'], 3)
            with self.assertRaises(ValueError): a.reserve('three', 4)

    def test_settlement_releases_only_known_unused_reservation(self):
        with tempfile.TemporaryDirectory() as d:
            a = Ledger(Path(d)/'ledger.sqlite', 10)
            a.reserve('one', 7)
            with self.assertRaises(ValueError): a.settle('one', 8)
            a.settle('one', 2)
            a.reserve('two', 8)
            self.assertEqual(a.snapshot()['remaining_usd'], 0)

    def test_reconciliation_requires_uncertain_status_and_keeps_audit(self):
        with tempfile.TemporaryDirectory() as d:
            a=Ledger(Path(d)/'ledger.sqlite',10)
            a.reserve('one',7);a.settle('one',0,uncertain=True)
            with self.assertRaises(ValueError):a.reconcile('one',8,'counter proof')
            a.reconcile('one',2,'matching terminal + provider counters')
            self.assertEqual(a.snapshot()['remaining_usd'],8)
            self.assertEqual(a.snapshot()['reconciliations'][0]['prior_charge_micros'],7_000_000)
            with self.assertRaises(ValueError):a.reconcile('one',0,'second mutation')


if __name__ == '__main__': unittest.main()
