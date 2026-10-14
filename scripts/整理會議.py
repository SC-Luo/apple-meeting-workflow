#!/usr/bin/env python3
"""Read-only Anarlog input; editable project reference; native Apple inference."""
import argparse
import hashlib
import json
import plistlib
import re
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from 試算表參考 import read_xlsx_reference, refresh_google_reference


def read_reference(path):
    if path.suffix.lower() == '.xlsx':
        return read_xlsx_reference(path)
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    pairs = []
    active = False
    for line in text.splitlines():
        if line.startswith('## '):
            active = line.strip() == '## 已確認的逐字稿替換'
        if active and line.strip().startswith('|'):
            cells = [x.strip() for x in line.strip().strip('|').split('|')]
            if len(cells) != 2 or cells[0] == '誤辨字詞' or all(re.fullmatch(r'[-: ]+', x) for x in cells):
                continue
            old, new = cells
            if not old or not new or old == new:
                raise ValueError('替換表需填寫不同且非空白的字詞。')
            if len(old) < 2:
                raise ValueError('為避免誤改，全文替換的誤辨字詞至少需兩個字。')
            if any(old in a or a in old or new in a or b in old for a, b in pairs):
                raise ValueError('替換表有重疊或連鎖字詞，請先拆開，以免重複修正。')
            pairs.append((old, new))
    # AI receives only useful vocabulary/context and owner formatting instructions.
    relevant = text.split('## 正確名稱與背景', 1)[-1]
    relevant = re.sub(r'## 已確認的逐字稿替換.*?(?=## 整理規則|\Z)', '', relevant, flags=re.S)
    relevant = relevant.strip()
    if pairs:
        relevant += '\n已確認的名稱：\n' + '\n'.join(f'{a} → {b}' for a, b in pairs)
    if len(relevant) > 1000:
        raise ValueError('參考名稱、背景與規則合計超過 1,000 字。請先精簡，以符合 Apple 內建模型的短上下文。')
    return text, relevant, pairs


def apply_confirmed(text, pairs):
    changes = []
    # Simultaneous replacement avoids changing a replacement again.
    mapping = dict(pairs)
    if not mapping:
        return text, changes
    def replace(match):
        old = match.group(0)
        return mapping[old]
    for old, new in pairs:
        count = text.count(old)
        if count:
            changes.append({'original': old, 'corrected': new, 'count': count})
    return re.sub('|'.join(re.escape(x) for x in mapping), replace, text), changes


def call_cli(cli, *args):
    p = subprocess.run([str(cli), '--json', 'meetings', *args], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError('無法讀取 Anarlog。請先開啟 App；CLI 回報：' + p.stderr[:500])
    value = json.loads(p.stdout)
    if 'data' not in value:
        raise RuntimeError('Anarlog 回傳格式異常；未改動原資料。')
    return value


def fetch_transcript(cli, meeting_id):
    pages, texts, offset = [], [], 0
    while True:
        page = call_cli(cli, 'transcript', meeting_id, '--limit', '200', '--offset', str(offset))
        pages.append(page)
        text = page['data'].get('text', '')
        if text:
            texts.append(text)
        next_offset = page.get('pagination', {}).get('next_offset')
        if next_offset is None:
            break
        if not isinstance(next_offset, int) or next_offset <= offset:
            raise RuntimeError('逐字稿分頁無法前進，停止處理以保留原稿。')
        offset = next_offset
    return '\n'.join(texts).strip(), pages


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--meeting-id')
    parser.add_argument('--input', type=Path, help='測試或既有純文字逐字稿')
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--auto-download', action='store_true', help='嘗試 Chrome 自動下載；受瀏覽器設定限制，未通過本機驗收')
    parser.add_argument('--output-root', type=Path, help='指定結果資料夾；預設保存於本工具旁的處理結果')
    parser.add_argument('--no-open', action='store_true')
    args = parser.parse_args()
    tool_dir = Path(__file__).resolve().parent
    root = tool_dir.parent if tool_dir.name == '03-工具' else tool_dir
    if args.reference:
        reference_path = args.reference
    elif args.auto_download:
        reference_path = refresh_google_reference(root / '01-參考資料/Google試算表連結.json', root / '01-參考資料/快取/最新詞彙表.xlsx')
    else:
        cache = Path.home() / 'Library/Caches/MacMeetingTrial'
        cache.mkdir(parents=True, exist_ok=True)
        bundle = cache / 'SelectMeetingReference.app'
        selector = bundle / 'Contents/MacOS/SelectMeetingReference'
        selector.parent.mkdir(parents=True, exist_ok=True)
        info = {'CFBundleIdentifier':'local.apple-meeting.reference-picker','CFBundleName':'詞彙表選擇','CFBundleExecutable':'SelectMeetingReference','CFBundlePackageType':'APPL','CFBundleVersion':'1','NSHighResolutionCapable':True}
        (bundle / 'Contents/Info.plist').write_bytes(plistlib.dumps(info))
        source = tool_dir / 'SelectMeetingReference.swift'
        if not selector.exists() or selector.stat().st_mtime < source.stat().st_mtime:
            subprocess.run(['/usr/bin/xcrun', 'swiftc', str(source), '-o', str(selector)], check=True)
        print('請選擇本次 Google 試算表匯出的 Excel 檔案。也可請已連接 Google 的 AI 直接取得最新版並處理。', flush=True)
        selected_file = cache / ('reference-selection-' + uuid.uuid4().hex + '.txt')
        selected = subprocess.run(['/usr/bin/open', '-W', '-n', str(bundle), '--args', str(selected_file)], capture_output=True, text=True)
        if selected.returncode or not selected_file.exists():
            raise ValueError('已取消選擇詞彙表，原稿不變。')
        reference_path = Path(selected_file.read_text(encoding='utf-8').strip())
        selected_file.unlink()
    reference_text, context, pairs = read_reference(reference_path)
    cli = Path.home() / 'Applications/Anarlog.app/Contents/MacOS/anarlog-cli'
    if args.input:
        original = args.input.read_text(encoding='utf-8').strip()
        meeting = {'id': 'text-input', 'title': args.input.stem}
        pages = []
    else:
        meetings = call_cli(cli, 'list', '--limit', '10')['data']
        if not meetings:
            raise ValueError('Anarlog 尚無錄音，請先錄音並確認逐字稿。')
        if args.meeting_id:
            meeting = call_cli(cli, 'get', args.meeting_id)['data']
        else:
            print('選擇要整理的錄音（直接按 Enter 選最新一筆）：', flush=True)
            for i, m in enumerate(meetings, 1):
                print(f"{i}. {m.get('title') or 'Untitled'}  [{m.get('created_at', '')}]", flush=True)
            selection = input('錄音編號：').strip() or '1'
            if not selection.isdigit() or not 1 <= int(selection) <= len(meetings):
                raise ValueError('請重新開啟工具，輸入清單中的編號。')
            meeting = meetings[int(selection) - 1]
        original, pages = fetch_transcript(cli, meeting['id'])
    if not original:
        raise ValueError('這筆錄音沒有逐字稿。請先確認 Apple Speech 即時文字已產生。')
    corrected, changes = apply_confirmed(original, pairs)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]
    title = re.sub(r'[/\\:\x00-\x1f]', '_', meeting.get('title') or 'Untitled')[:45]
    destination = (args.output_root or root / '02-錄音結果') / datetime.now().strftime('%Y-%m-%d') / (title + '-' + stamp)
    destination.mkdir(parents=True)
    (destination / '原始逐字稿.txt').write_text(original, encoding='utf-8')
    (destination / '依確認詞彙校正.txt').write_text(corrected, encoding='utf-8')
    (destination / '本次參考資料快照.txt').write_text(reference_text, encoding='utf-8')
    if reference_path.suffix.lower() == '.xlsx':
        (destination / '本次詞彙表快照.xlsx').write_bytes(reference_path.read_bytes())
    audit = {'meeting_id': meeting['id'], 'reference_file': str(reference_path),
             'reference_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest(),
             'confirmed_changes': changes, 'transcript_pages': pages,
             'engine': 'Apple FoundationModels / System Language Model'}
    (destination / '來源與修正紀錄.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    payload = destination / '模型輸入.json'
    payload.write_text(json.dumps({'title': meeting.get('title') or 'Untitled', 'reference': context, 'transcript': corrected}, ensure_ascii=False), encoding='utf-8')
    cache = Path.home() / 'Library/Caches/MacMeetingTrial'
    cache.mkdir(parents=True, exist_ok=True)
    binary = cache / 'ProjectMeetingRefiner'
    source = tool_dir / 'ProjectMeetingRefiner.swift'
    if not binary.exists() or binary.stat().st_mtime < source.stat().st_mtime:
        print('首次執行：準備 Apple 內建處理工具…', flush=True)
        subprocess.run(['/usr/bin/xcrun', 'swiftc', '-parse-as-library', str(source), '-o', str(binary)], check=True)
    model_result = destination / 'Apple整理結果.json'
    print(f'已保存原稿；參考文件已重新讀取，確認替換 {sum(c["count"] for c in changes)} 處。', flush=True)
    p = subprocess.run([str(binary), str(payload), str(model_result)])
    result = json.loads(model_result.read_text()) if model_result.exists() else {'summaries': [], 'suggestions': [], 'errors': ['Apple 模型未完成，原稿與確認詞彙校正仍已保存。']}
    lines = ['# ' + (meeting.get('title') or '會議整理'), '',
             '本結果由 Mac 內建 Apple AI 產生，尚需核對。原始音訊、Anarlog 原稿均未改動。',
             '參考文件更新後請重跑；此工具不訓練語音模型。', '', '## 已確認詞彙的替換', '']
    lines += [f"- {c['original']} → {c['corrected']}（{c['count']} 處）" for c in changes] or ['沒有確認替換；原文保持不變。']
    lines += ['', '## AI 名稱建議（待確認，未套用）', '']
    lines += [f"- 第 {s['chunk']} 段：{s['original']} → {s['suggested']}（請聽原音訊確認）" for s in result['suggestions']] or ['沒有可列出的名稱候選；這不代表全部名稱正確。']
    lines += ['', '## 分段摘要', '', '長稿依原文順序分段；不同段的提案、決定或後續撤回，仍需合併核對。', ''] + result['summaries']
    if result['errors'] or p.returncode:
        lines += ['', '## 未完成項目', ''] + ['- ' + e for e in result['errors']]
    lines += ['', '## 依已確認詞彙校正的全文', '', corrected]
    report = destination / '會議整理.md'
    report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('結果：' + str(report), flush=True)
    if not args.no_open:
        subprocess.run(['/usr/bin/open', '-a', 'TextEdit', str(report)], check=True)
    return 0 if not result['errors'] and p.returncode == 0 else 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print('未完成：' + str(error), file=sys.stderr)
        sys.exit(1)
