"""Download pinned public Coin Metrics data, saving only the selected columns/window."""
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


def fetch(url):
    with urlopen(Request(url,headers={'User-Agent':'educational-peg-risk-lab'}),timeout=60) as response:
        return response.read()


def main():
    root=Path(__file__).resolve().parent/'data'; root.mkdir(exist_ok=True)
    manifest_path=root/'manifest.json'
    # Reuse the original commit on all subsequent runs.
    commit=(json.loads(manifest_path.read_text())['source_commit'] if manifest_path.exists()
            else json.loads(fetch('https://api.github.com/repos/coinmetrics/data/commits/master'))['sha'])
    records=[]
    for asset in ('usdc','dai'):
        url=f'https://raw.githubusercontent.com/coinmetrics/data/{commit}/csv/{asset}.csv'
        raw=fetch(url)
        reader=csv.DictReader(io.StringIO(raw.decode('utf-8')))
        output=io.StringIO(newline=''); writer=csv.writer(output,lineterminator='\n')
        writer.writerow(['date','price_usd'])
        missing=[]; count=0
        for row in reader:
            day=row['time'][:10]
            if '2023-01-01' <= day <= '2023-06-30':
                if not row['PriceUSD']:
                    missing.append(day)
                    continue
                writer.writerow([day,row['PriceUSD']]); count+=1
        encoded=output.getvalue().encode('utf-8')
        if count < 150:
            raise ValueError(f'insufficient actual data for {asset}: {count}')
        (root/f'{asset}.csv').write_bytes(encoded)
        records.append(dict(asset=asset,url=url,rows=count,empty_price_dates=missing,
                            source_sha256=hashlib.sha256(raw).hexdigest(),
                            subset_sha256=hashlib.sha256(encoded).hexdigest()))
    manifest=dict(source='Coin Metrics community data',source_commit=commit,
                  retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                  license='CC BY-NC 4.0',license_url='https://creativecommons.org/licenses/by-nc/4.0/',
                  window=['2023-01-01','2023-06-30'],transform='Select time and PriceUSD; omit and report empty prices; no interpolation.',files=records)
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'source_commit':commit,'files':[(r['asset'],r['rows']) for r in records]}))


if __name__=='__main__':
    main()
