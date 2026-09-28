"""Build a readable index from the collected snapshots; no network access."""
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def link(label, url):
    return f'[{label}]({quote(url, safe=":/?=&%#+")})'


def main():
    data = read('official-awards.json')
    notes = {x['id']: x for x in read('review-notes.json')['records']}
    checks = {x['id']: x for x in read('artifact-checks.json')['checks']}
    out = ['# 2023–2025 공개 수상작 전체 목록', '',
           '확인: 2026-09-28. 공식 아카이브 102건 + 외부 보완 입선 3건. 전체 입선까지 완전 확보했다는 뜻은 아니다. [조사 범위·분석·한계](수상작조사_2023-2025.md)를 함께 읽는다.', '',
           '제목·수상자·소속은 공식 게시 목록 표기를 보존했다. 작품명이 아닌 상격/부문만 제목에 있는 경우도 원문 그대로 두었다. 미디어는 전편 재생 검토를 하지 않았다.', '']
    for page in data['pages']:
        out += [f'## {page["year"]} · {page["category"]} ({page["record_count"]}건)', '',
                link('공식 게시판', page['url']), '']
        if not page['record_count']:
            out += ['2025 포스터 부문은 공식 결과표에 수상작 미선정으로 명시되어 있다.', '']
        for r in data['records']:
            if r['year'] != page['year'] or r['category_code'] != page['category_code']:
                continue
            c = checks[r['id']]
            out += [f'<a id="{r["id"].lower()}"></a>', '',
                    f'### {r["award"]} · {r["title"]}', '',
                    f'- 기록 ID: `{r["id"]}`',
                    f'- 수상자: {r["creator"]} / 소속: {r["affiliation"]}',
                    '- ' + link('공식 원본 열기', r['artifact_urls'][0]) + f' ({c["extension"]}, HTTP {c["http_status"]})']
            if r['id'] in notes:
                n = notes[r['id']]
                out += [f'- 검토 요약: {n["summary"]}']
                if n.get('caution'):
                    out += [f'- 확인 한계: {n["caution"]}']
            else:
                out += ['- 검토 범위: 수상 메타데이터·원본 응답 확인. 작품 내용의 심층 평가는 하지 않음.']
            out += ['']
    out += ['## 공식 아카이브 밖에서 추가 확인한 입선', '']
    for r in read('supplemental-awards.json')['records']:
        out += [f'### {r["year"]} · {r["award"]} · {r["title"]}', '',
                f'- 기록 ID: `{r["id"]}`',
                f'- 수상자: {r["creator"]} / 소속: {r["affiliation"]}',
                '- ' + link('대학·연구실 발표', r['source_url']),
                f'- 확인 내용: {r["finding"]}', '']
    (ROOT / '전체목록.md').write_text('\n'.join(out), encoding='utf-8')


if __name__ == '__main__':
    main()
