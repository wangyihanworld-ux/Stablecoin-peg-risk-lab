import unittest
from datetime import date,timedelta
from decimal import Decimal
from analyze import summarize,lagged_alerts,load_prices
from unittest.mock import patch,mock_open
from pathlib import Path
import json
import hashlib


class RiskTests(unittest.TestCase):
    def test_snapshot_hashes_and_completeness(self):
        root=Path(__file__).resolve().parent/'data'
        manifest=json.loads((root/'manifest.json').read_text())
        for file in manifest['files']:
            data=root/(file['asset']+'.csv')
            self.assertEqual(hashlib.sha256(data.read_bytes()).hexdigest(),file['subset_sha256'])
            rows=load_prices(data)
            self.assertEqual(len(rows),181)
            self.assertEqual(summarize(rows,'2023-01-01','2023-06-30')['missing_calendar_days'],0)

    def test_invalid_prices_rejected(self):
        for value in ['NaN','Infinity','-1','0','not-a-number','']:
            with self.subTest(value=value),patch('builtins.open',mock_open(read_data='date,price_usd\n2023-01-01,'+value+'\n')):
                with self.assertRaises(ValueError):
                    load_prices('unused.csv')

    def test_duplicate_date_rejected(self):
        with patch('builtins.open',mock_open(read_data='date,price_usd\n2023-01-01,1\n2023-01-01,.9\n')):
            with self.assertRaises(ValueError):
                load_prices('unused.csv')

    def test_empty_file_rejected(self):
        with patch('builtins.open',mock_open(read_data='date,price_usd\n')):
            with self.assertRaises(ValueError):
                load_prices('unused.csv')

    def rows(self,values):
        return [(date(2023,1,1)+timedelta(days=i),Decimal(str(value))) for i,value in enumerate(values)]

    def test_par_baseline(self):
        result=summarize(self.rows([1,1,1]),'2023-01-01','2023-01-03')
        self.assertEqual(result['max_absolute_deviation_bps'],0)
        self.assertEqual(result['days_outside_band'],0)

    def test_bps_and_hypothetical_loss(self):
        result=summarize(self.rows([1,.9]),'2023-01-01','2023-01-02')
        self.assertEqual(result['max_absolute_deviation_bps'],1000)
        self.assertEqual(Decimal(result['hypothetical_10000_tokens_max_mark_to_peg_shortfall_usd']),1000)

    def test_missing_not_filled(self):
        result=summarize(self.rows([1,.9]),'2023-01-01','2023-01-03')
        self.assertEqual(result['missing_calendar_days'],1)
        self.assertEqual(result['observed_fraction_outside_band'],.5)

    def test_three_day_confirmation(self):
        result=summarize(self.rows([.9,1,1,1]),'2023-01-01','2023-01-04')
        self.assertEqual(result['recovery_confirmation_date'],'2023-01-04')

    def test_gap_breaks_recovery(self):
        rows=self.rows([.9,1,1,1,1]); rows.pop(2)
        self.assertIsNone(summarize(rows,'2023-01-01','2023-01-05')['recovery_confirmation_date'])

    def test_no_recovery_is_not_zero(self):
        self.assertIsNone(summarize(self.rows([1,.9]),'2023-01-01','2023-01-02')['days_to_three_day_recovery_confirmation'])

    def test_band_equality_inside(self):
        self.assertEqual(summarize(self.rows([.99,1.01]),'2023-01-01','2023-01-02')['days_outside_band'],0)

    def test_wider_band_monotonic(self):
        rows=self.rows([1,.98,.99,1.015])
        a=summarize(rows,'2023-01-01','2023-01-04',50)
        b=summarize(rows,'2023-01-01','2023-01-04',200)
        self.assertGreaterEqual(a['days_outside_band'],b['days_outside_band'])

    def test_alert_does_not_fit_current(self):
        rows=self.rows([1]*30+[.9])
        last=lagged_alerts(rows)[-1]
        self.assertEqual(last['prior_threshold_bps'],0)
        self.assertTrue(last['alert'])

    def test_future_not_change_past(self):
        rows=self.rows([1]*30+[.9,1])
        self.assertEqual(lagged_alerts(rows[:31])[0],lagged_alerts(rows)[0])

    def test_history_gap_skipped(self):
        rows=self.rows([1]*32); rows.pop(10)
        self.assertEqual(lagged_alerts(rows),[])

    def test_empty_interval(self):
        with self.assertRaises(ValueError):
            summarize(self.rows([1]),'2024-01-01','2024-01-02')

    def test_invalid_window(self):
        with self.assertRaises(ValueError):
            lagged_alerts(self.rows([1,1]),1)

    def test_inverted_interval(self):
        with self.assertRaises(ValueError):
            summarize(self.rows([1]),'2023-01-02','2023-01-01')


if __name__=='__main__':
    unittest.main()
