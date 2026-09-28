"""Check official artifact links, cache documents, extract their text for research.

Dependencies: requests, pypdf; olefile for legacy HWP (optional).
Videos/audio/images are checked by a streamed prefix, not bulk downloaded.
"""
import hashlib
import json
import re
import struct
import sys
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

ROOT = Path(__file__).resolve().parent
CACHE = ROOT/'cache'
sys.path.insert(0,str(CACHE/'deps'))
sys.stdout.reconfigure(encoding='utf-8')


def inspect(record):
    url = record['artifact_urls'][0]
    ext = Path(parse_qs(urlparse(url).query)['fileName'][0]).suffix.lower()
    result = {'id':record['id'], 'url':url, 'extension':ext}
    try:
        with requests.get(url, timeout=40, stream=True) as response:
            result.update(http_status=response.status_code, content_type=response.headers.get('Content-Type'), content_length=response.headers.get('Content-Length'))
            response.raise_for_status()
            if ext not in ('.pdf','.hwp'):
                prefix=next(response.iter_content(64),b'')
                result.update(check='response_prefix_only_not_full_media_review',prefix_hex=prefix[:16].hex())
                return result
            data=response.content
        path=CACHE/(record['id']+ext)
        path.write_bytes(data)
        result.update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),check='downloaded_document')
        if ext=='.pdf':
            from pypdf import PdfReader
            reader=PdfReader(path)
            text='\n\n'.join(f'PAGE {i+1}\n'+(p.extract_text() or '') for i,p in enumerate(reader.pages))
            result['pages']=len(reader.pages)
        else:
            import olefile
            chunks=[]
            with olefile.OleFileIO(path) as ole:
                compressed=struct.unpack('<I',ole.openstream('FileHeader').read()[36:40])[0]&1
                for stream in sorted(ole.listdir()):
                    if stream[0]!='BodyText' or not stream[-1].startswith('Section'):continue
                    data=ole.openstream(stream).read()
                    if compressed:data=zlib.decompress(data,-15)
                    pos=0
                    while pos+4<=len(data):
                        header=struct.unpack_from('<I',data,pos)[0];pos+=4
                        tag=header&0x3ff;size=header>>20
                        if size==0xfff:size=struct.unpack_from('<I',data,pos)[0];pos+=4
                        payload=data[pos:pos+size];pos+=size
                        if tag==67:
                            chunks.append(payload.decode('utf-16le',errors='replace'))
            text='\n'.join(chunks)
        text=re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]',' ',text)
        (CACHE/(record['id']+'.txt')).write_text(text,encoding='utf-8')
        result['extracted_characters']=len(text)
    except Exception as exc:
        result['error']=f'{type(exc).__name__}: {exc}'
    return result


if __name__=='__main__':
    data=json.loads((ROOT/'official-awards.json').read_text(encoding='utf-8'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        checks=list(pool.map(inspect,data['records']))
    (ROOT/'artifact-checks.json').write_text(json.dumps({'checked_at':data['checked_at'],'checks':checks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for check in checks:
        if check['extension'] in ('.pdf','.hwp') or 'error' in check:print(check['id'],check.get('pages'),check.get('extracted_characters'),check.get('error','OK'))
    print('CHECKS',len(checks),'ERRORS',sum('error' in x for x in checks))
