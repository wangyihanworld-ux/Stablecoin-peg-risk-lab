"""Descriptive stablecoin price-risk analysis; no trading or causal claims."""
import csv
import json
import math
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import mean, pstdev


def load_prices(path):
    result = []
    seen = set()
    with open(path, encoding='utf-8', newline='') as handle:
        for row in csv.DictReader(handle):
            day = date.fromisoformat(row['date'])
            if day in seen:
                raise ValueError('duplicate observation date')
            seen.add(day)
            try:
                price = Decimal(row['price_usd'])
            except InvalidOperation as exc:
                raise ValueError('invalid price') from exc
            if not price.is_finite() or price <= 0:
                raise ValueError('price must be finite and positive')
            result.append((day, price))
    if not result:
        raise ValueError('empty sample')
    return sorted(result)


def summarize(prices, start, end, threshold_bps=100):
    start, end = date.fromisoformat(start), date.fromisoformat(end)
    if end < start or not math.isfinite(threshold_bps) or threshold_bps <= 0:
        raise ValueError('invalid interval or threshold')
    rows = [(day, value) for day, value in prices if start <= day <= end]
    if not rows:
        raise ValueError('no observations in interval')
    deviations = [float((value - 1) * 10000) for _, value in rows]
    missing = (end-start).days+1-len(rows)
    trough_day, trough = min(rows, key=lambda r:r[1])
    band = Decimal(str(threshold_bps)) / 10000
    recovery, streak, previous = None, 0, None
    for day, value in rows:
        if day <= trough_day:
            continue
        if abs(value-1) <= band:
            streak = streak + 1 if previous and day-previous == timedelta(days=1) else 1
        else:
            streak = 0
        previous = day
        if streak == 3:
            recovery = day
            break
    return dict(start=str(start), end=str(end),observations=len(rows),missing_calendar_days=missing,
                min_price_usd=str(trough),trough_date=str(trough_day),
                max_absolute_deviation_bps=max(map(abs,deviations)),
                mean_absolute_deviation_bps=mean(map(abs,deviations)),
                days_outside_band=sum(abs(x)>threshold_bps for x in deviations),
                observed_fraction_outside_band=sum(abs(x)>threshold_bps for x in deviations)/len(rows),
                threshold_bps=threshold_bps,
                recovery_confirmation_date=str(recovery) if recovery else None,
                days_to_three_day_recovery_confirmation=(recovery-trough_day).days if recovery else None,
                hypothetical_10000_tokens_max_mark_to_peg_shortfall_usd=str(max(Decimal(0),(1-trough)*10000)))


def lagged_alerts(prices, window=30):
    """Illustrative alerts: current absolute deviation vs prior-only mean+3 SD.

    Require a full uninterrupted history. This detects current deviation, not
    future deviations. The rule is not calibrated to a verified event label.
    """
    if type(window) is not int or window < 2:
        raise ValueError('window must be integer >=2')
    output=[]
    for index in range(window,len(prices)):
        history=prices[index-window:index]
        day,price=prices[index]
        if (day-history[0][0]).days != window:
            continue
        deviations=[abs(float((value-1)*10000)) for _,value in history]
        limit=mean(deviations)+3*pstdev(deviations)
        current=abs(float((price-1)*10000))
        output.append(dict(date=str(day),prior_threshold_bps=limit,absolute_deviation_bps=current,alert=current>limit))
    return output


def main():
    root=Path(__file__).resolve().parent
    results={}
    for asset in ('usdc','dai'):
        prices=load_prices(root/'data'/f'{asset}.csv')
        results[asset]={'periods':{name:summarize(prices,start,end) for name,start,end in [
            ('pre_selected_event','2023-01-01','2023-02-28'),
            ('selected_stress_month','2023-03-01','2023-03-31'),
            ('after_selected_event','2023-04-01','2023-06-30')]},
            'sensitivity':[summarize(prices,'2023-03-01','2023-03-31',t) for t in (50,100,200)],
            'lagged_alerts':lagged_alerts(prices)}
    output=root/'results'; output.mkdir(exist_ok=True)
    (output/'metrics.json').write_text(json.dumps(results,indent=2,allow_nan=False),encoding='utf-8')
    lines=['# Observed daily stablecoin prices\n',
           'Real public Coin Metrics observations, January–June 2023. This is an intentionally selected historical stress case, not an unbiased forecast evaluation.\n',
           '| Asset | March minimum USD | Date | Days outside ±100 bps | Max deviation bps | Missing days |',
           '|---|---:|---|---:|---:|---:|']
    for asset,result in results.items():
        m=result['periods']['selected_stress_month']
        lines.append(f"| {asset.upper()} | {m['min_price_usd']} | {m['trough_date']} | {m['days_outside_band']} | {m['max_absolute_deviation_bps']:.2f} | {m['missing_calendar_days']} |")
    lines.extend(['\nRecovery is confirmation of three consecutive observed daily prices within the stated band after the sample minimum. It is not proof of redemption availability.',
                  '\nDaily prices do not capture intraday extremes or executable liquidity. Missing values are never filled. The mark-to-peg shortfall for 10,000 tokens is a hypothetical USD valuation scenario, not realized loss or a guaranteed redemption amount.',
                  '\nPrior-30-day alert thresholds never use the target observation in calibration. These alerts detect observed price deviations; there are no verified incident labels, so accuracy, recall and investment returns are not reported.',
                  '\nSource and noncommercial reuse terms: https://github.com/coinmetrics/data (CC BY-NC 4.0); see data/manifest.json for pinned commit and hashes.'])
    (output/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    print('\n'.join(lines[:8]))


if __name__=='__main__':
    main()
