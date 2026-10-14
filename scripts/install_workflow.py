#!/usr/bin/env python3
"""Install a user-owned workflow workspace without modifying Anarlog."""
import argparse
import json
import re
import shutil
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--destination', type=Path, required=True)
parser.add_argument('--sheet-url', required=True)
args = parser.parse_args()
match = re.fullmatch(r'https://docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]+)(?:/[^\s]*)?', args.sheet_url)
if not match:
    parser.error('Supply the actual Google Sheets HTTPS URL.')
root = args.destination.expanduser().resolve()
if root.exists() and any(root.iterdir()):
    parser.error('Destination is not empty; preserve its files and choose a new folder.')
package = Path(__file__).resolve().parent.parent
for name in ('01-參考資料', '02-錄音結果', '03-工具'):
    (root/name).mkdir(parents=True, exist_ok=True)
for name in ('整理會議.py','試算表參考.py','ProjectMeetingRefiner.swift','SelectMeetingReference.swift'):
    shutil.copy2(package/'scripts'/name, root/'03-工具'/name)
config = {'spreadsheet_id':match[1], 'title':'會議錄音整理_專案詞彙表',
          'url':args.sheet_url, 'download_directory':str(Path.home()/'Downloads'), 'timeout_seconds':120}
(root/'01-參考資料/Google試算表連結.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(package/'assets/glossary-template.xlsx',root/'01-參考資料/初始範本.xlsx')
launcher = '#!/bin/zsh\nset -u\ntask_dir="$(cd -- "$(dirname -- "$0")" && pwd)"\n/usr/bin/python3 "$task_dir/03-工具/整理會議.py" "$@"\ntask_status=$?\nread -r "?按 Enter 關閉。"\nexit "$task_status"\n'
(root/'開始整理錄音.command').write_text(launcher,encoding='utf-8')
(root/'開始整理錄音.command').chmod(0o755)
(root/'編輯詞彙表.command').write_text('#!/bin/zsh\n/usr/bin/python3 -c \'import json,sys,subprocess; subprocess.run(["/usr/bin/open",json.load(open(sys.argv[1]))["url"]],check=True)\' "$(dirname -- "$0")/01-參考資料/Google試算表連結.json"\n',encoding='utf-8')
(root/'編輯詞彙表.command').chmod(0o755)
print('Installed:',root)
print('Maintain the Google Sheet as master. Use an authenticated fresh export with --reference for the verified route.')
