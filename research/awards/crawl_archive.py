"""Collect public award metadata from the official archive (no submissions/login).

Run from the repository root: python research/awards/crawl_archive.py
Raw HTML is cached locally and excluded from Git; published records link to originals.
"""
import csv
import hashlib
import html
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parent
BASE = 'https://greenremodeling.or.kr/n1/challenge/chal7000.asp'
CACHE = ROOT / 'cache'
CACHE.mkdir(exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8')


def clean(value):
    return ' '.join(html.unescape(re.sub('<[^>]+>', ' ', value)).split())


def fetch(url, filename):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    response.encoding = 'utf-8' if 'utf-8' in response.text[:1000].lower() else response.apparent_encoding
    text = response.text
    (CACHE / filename).write_text(text, encoding='utf-8')
    return text, hashlib.sha256(response.content).hexdigest()


def main():
    checked = datetime.now(timezone(timedelta(hours=9))).isoformat(timespec='seconds')
    records, pages = [], []
    for year in (2023, 2024, 2025):
        first, _ = fetch(f'{BASE}?workyy={year}', f'{year}-index.html')
        select = re.search(r'<select[^>]+name="chal_part"[^>]*>(.*?)</select>', first, re.S).group(1)
        categories = [(code, clean(name)) for code, name in re.findall(r'<option value="(\d+)"[^>]*>(.*?)</option>', select, re.S)]
        for code, category in categories:
            url = f'{BASE}?workyy={year}&chal_part={code}'
            body, digest = fetch(url, f'{year}-{code}.html')
            section = body.split('<!-- list start -->', 1)[1].split('<!-- list end -->', 1)[0]
            section = re.sub(r'<!--.*?-->', '', section, flags=re.S)
            before = len(records)
            for award, items in re.findall(r'<div class="con-ti ti3">(.*?)</div>\s*<ul[^>]*>(.*?)</ul>', section, re.S):
                for item in re.findall(r'<li\b[^>]*>(.*?)</li>', items, re.S):
                    ps = re.findall(r'<p\b[^>]*>(.*?)</p>', item, re.S)
                    texts = [clean(p) for p in ps if clean(p)]
                    links = list(dict.fromkeys(urljoin(url, html.unescape(link)) for link in re.findall(r'(?:href|src)="([^"]+)"', item) if 'folderName=chal_win' in link))
                    record = {'id': f'GR{year}-{code}-{len(records)-before+1:02d}', 'year': year, 'edition': year-2020, 'category_code': code, 'category': category, 'award': clean(award), 'title': texts[0] if texts else '', 'creator': texts[1] if len(texts)>1 else '', 'affiliation': texts[2] if len(texts)>2 else '', 'archive_url': url, 'artifact_urls': links, 'checked_at': checked}
                    records.append(record)
            pages.append({'year':year, 'category_code':code, 'category':category, 'url':url, 'record_count':len(records)-before, 'response_sha256':digest})
            print(year, category, len(records)-before)
    data = {'checked_at':checked, 'scope':'Official archive entries for 2023–2025; archive publication completeness is not independently assumed.', 'pages':pages, 'records':records}
    (ROOT/'official-awards.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fields = ['id','year','edition','category','award','title','creator','affiliation','archive_url','artifact_urls']
    with (ROOT/'official-awards.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for record in records:
            writer.writerow({key:' | '.join(record[key]) if key=='artifact_urls' else record[key] for key in fields})
    print('TOTAL', len(records), dict(Counter(r['year'] for r in records)))


if __name__=='__main__':
    main()
