"""Read an XLSX glossary with stdlib only; refresh private Sheets via Chrome."""
import hashlib
import json
import posixpath
import re
import subprocess
import time
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def worksheet_rows(path):
    with zipfile.ZipFile(path) as z:
        if sum(x.file_size for x in z.infolist()) > 20_000_000:
            raise ValueError('試算表過大，請使用專用的精簡詞彙表。')
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS)]
        workbook = ET.fromstring(z.read('xl/workbook.xml'))
        rels = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        result = {}
        for sheet in workbook.findall('m:sheets/m:sheet', NS):
            target = rels[sheet.attrib[REL]]
            member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            rows = []
            for row in ET.fromstring(z.read(member)).findall('m:sheetData/m:row', NS):
                cells = {}
                for cell in row.findall('m:c', NS):
                    column = re.match(r'[A-Z]+', cell.attrib.get('r', '')).group()
                    if cell.find('m:f', NS) is not None:
                        value = {'formula': True}
                    elif cell.attrib.get('t') == 's':
                        value = strings[int(cell.findtext('m:v', default='0', namespaces=NS))]
                    elif cell.attrib.get('t') == 'inlineStr':
                        value = ''.join(cell.find('m:is', NS).itertext())
                    else:
                        value = cell.findtext('m:v', default='', namespaces=NS)
                    cells[column] = value
                rows.append((int(row.attrib.get('r', len(rows)+1)), cells))
            result[sheet.attrib['name']] = rows
        return result


def table_rows(rows, headers):
    columns = None
    for number, cells in rows:
        if columns is None:
            lookup = {}
            for k, v in cells.items():
                lookup.setdefault(str(v).strip(), k)
            if all(h in lookup for h in headers):
                columns = {h: lookup[h] for h in headers}
            continue
        values = {h: cells.get(columns[h], '') for h in headers}
        if any(isinstance(v, dict) for v in values.values()):
            raise ValueError(f'第 {number} 列請填純文字，詞彙欄位不使用公式。')
        values = {h: str(v).strip() for h, v in values.items()}
        if any(values.values()):
            yield number, values
    if columns is None:
        raise ValueError('找不到詞彙表欄名。請保留原有分頁名稱與欄名。')


def validate_pairs(pairs):
    accepted = []
    for old, new in pairs:
        if not old or not new or old == new or len(old) < 2:
            raise ValueError('確認替換需有不同的誤辨與正確名稱；誤辨詞至少兩個字。')
        if (old, new) in accepted:
            continue
        if any(old in a or a in old or new in a or b in old for a, b in accepted):
            raise ValueError('確認替換有重疊或連鎖詞彙，請改為「參考」或先移除衝突。')
        accepted.append((old, new))
    return accepted


def read_xlsx_reference(path):
    sheets = worksheet_rows(path)
    if not {'詞彙校正', '背景與規則'}.issubset(sheets):
        raise ValueError('需要「詞彙校正」與「背景與規則」兩個分頁。')
    pairs, vocabulary, context_lines = [], [], []
    for number, row in table_rows(sheets['詞彙校正'], ['類別', '正確名稱', '常見誤辨', '處理方式', '說明']):
        mode = row['處理方式'] or '參考'
        if mode == '停用':
            continue
        if mode not in {'參考', '確認替換'}:
            raise ValueError(f'詞彙校正第 {number} 列的處理方式需為參考、確認替換或停用。')
        name = row['正確名稱']
        if not name:
            raise ValueError(f'詞彙校正第 {number} 列缺少正確名稱。')
        aliases = [s.strip() for s in re.split(r'[\n、；;]+', row['常見誤辨']) if s.strip()]
        if mode == '確認替換':
            if not aliases:
                raise ValueError(f'詞彙校正第 {number} 列選了確認替換，但沒有填誤辨詞。')
            pairs.extend((alias, name) for alias in aliases)
        detail = name + (f"：{row['說明']}" if row['說明'] else '')
        if aliases:
            detail += '（疑似誤辨：' + '、'.join(aliases) + '）'
        vocabulary.append(detail)
    for number, row in table_rows(sheets['背景與規則'], ['類型', '內容']):
        kind = row['類型'] or '背景'
        if kind == '停用' or not row['內容']:
            continue
        if kind not in {'背景', '規則'}:
            raise ValueError(f'背景與規則第 {number} 列的類型需為背景、規則或停用。')
        context_lines.append(kind + '：' + row['內容'])
    pairs = validate_pairs(pairs)
    text = '\n'.join(['正確名稱：'] + vocabulary + context_lines)
    if len(text) > 1000:
        raise ValueError('啟用的詞彙與背景合計超過 1,000 字。請精簡說明，或將暫時不用的列設為停用。')
    return text, text, pairs


def refresh_google_reference(config_path, cache_path):
    config = json.loads(config_path.read_text(encoding='utf-8'))
    sheet_id = config['spreadsheet_id']
    if not re.fullmatch(r'[A-Za-z0-9_-]+', sheet_id):
        raise ValueError('Google 試算表 ID 格式錯誤。')
    downloads = Path(config['download_directory'])
    filename = re.compile(r'^' + re.escape(config['title']) + r'(?: \(\d+\))?\.xlsx$')
    def candidates():
        return [p for p in downloads.iterdir() if p.is_file() and filename.fullmatch(unicodedata.normalize('NFC', p.name))]
    before = {str(p): (p.stat().st_mtime_ns, p.stat().st_size) for p in candidates()}
    authuser = str(config.get('authuser', 0))
    if not authuser.isdigit():
        raise ValueError('Chrome 帳號索引格式錯誤。')
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx&authuser={authuser}'
    print('Chrome 正在下載最新 Google 詞彙表。若出現登入或儲存提示，請完成；不要修改檔名。', flush=True)
    subprocess.run(['/usr/bin/open', '-a', 'Google Chrome', url], check=True)
    deadline = time.monotonic() + config.get('timeout_seconds', 120)
    notice = time.monotonic()
    while time.monotonic() < deadline:
        for path in sorted(candidates(), key=lambda p: p.stat().st_mtime_ns, reverse=True):
            state = (path.stat().st_mtime_ns, path.stat().st_size)
            if before.get(str(path)) == state:
                continue
            try:
                read_xlsx_reference(path)
            except (zipfile.BadZipFile, OSError):
                continue
            raw = path.read_bytes()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = cache_path.with_suffix('.xlsx.tmp')
            temporary.write_bytes(raw)
            temporary.replace(cache_path)
            sync = {'url': config['url'], 'downloaded_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'sha256': hashlib.sha256(raw).hexdigest()}
            cache_path.with_suffix('.同步紀錄.json').write_text(json.dumps(sync, ensure_ascii=False, indent=2), encoding='utf-8')
            # Remove only a new download created by this run, after preserving the cache.
            if str(path) not in before:
                path.unlink()
            print('已取得本次最新表格；不使用舊快取。', flush=True)
            return cache_path
        if time.monotonic() - notice >= 15:
            print('仍在等候下載。請確認 Chrome 已登入正確帳號，下載位置為「下載項目」。', flush=True)
            notice = time.monotonic()
        time.sleep(0.5)
    raise ValueError('沒有收到本次最新表格，已停止。請在 Chrome 登入試算表帳號，確認下載位置，或從 Google 試算表下載 Excel 後明確指定參考檔。')
