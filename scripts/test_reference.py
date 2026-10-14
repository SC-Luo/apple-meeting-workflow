#!/usr/bin/env python3
"""Fictitious XLSX fixtures test updates, disabled rows, and stale-cache refusal."""
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.sax.saxutils import escape

from 試算表參考 import read_xlsx_reference, refresh_google_reference, validate_pairs
from 整理會議 import apply_confirmed


def fixture(path, name='王怡君', disabled=False):
    def row(number, values):
        return '<row r="%s">%s</row>' % (number, ''.join(
            f'<c r="{chr(65+i)}{number}" t="inlineStr"><is><t>{escape(v)}</t></is></c>'
            for i,v in enumerate(values)))
    main='<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+row(1,['類別','正確名稱','常見誤辨','處理方式','說明'])+row(2,['人名',name,'王宜軍','停用' if disabled else '確認替換','虛構测试'])+'</sheetData></worksheet>'
    # Duplicate headers to the right must not shadow the actual populated columns.
    context='<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+row(1,['類型','內容','類型','內容'])+row(2,['規則','不得補寫事實'])+'</sheetData></worksheet>'
    workbook='<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="詞彙校正" sheetId="1" r:id="r1"/><sheet name="背景與規則" sheetId="2" r:id="r2"/></sheets></workbook>'
    relationships='<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Target="worksheets/sheet1.xml"/><Relationship Id="r2" Target="/xl/worksheets/sheet2.xml"/></Relationships>'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('xl/workbook.xml',workbook)
        z.writestr('xl/_rels/workbook.xml.rels',relationships)
        z.writestr('xl/worksheets/sheet1.xml',main)
        z.writestr('xl/worksheets/sheet2.xml',context)


class ReferenceTests(unittest.TestCase):
    def test_updates_preserve_original(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'reference.xlsx'
            original='王宜軍週五前交報價。'
            fixture(path)
            _,context,pairs=read_xlsx_reference(path)
            self.assertIn('不得補寫事實',context)
            first,_=apply_confirmed(original,pairs)
            fixture(path,name='王宜鈞')
            _,_,pairs=read_xlsx_reference(path)
            second,_=apply_confirmed(original,pairs)
            self.assertEqual(first,'王怡君週五前交報價。')
            self.assertEqual(second,'王宜鈞週五前交報價。')
            self.assertEqual(original,'王宜軍週五前交報價。')

    def test_disabled_and_conflicting_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'reference.xlsx';fixture(path,disabled=True)
            _,context,pairs=read_xlsx_reference(path)
            self.assertEqual(pairs,[])
            self.assertNotIn('王怡君',context)
        with self.assertRaises(ValueError):
            validate_pairs([('王宜軍','王怡君'),('王宜軍','王宜鈞')])

    def test_no_stale_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);downloads=root/'downloads';downloads.mkdir()
            cache=root/'cache.xlsx';fixture(cache)
            config=root/'config.json'
            config.write_text(json.dumps({'spreadsheet_id':'fictitious_id','title':'Glossary','url':'https://docs.google.com/spreadsheets/d/fictitious_id/edit','download_directory':str(downloads),'timeout_seconds':0.01}))
            before=cache.read_bytes()
            with patch('試算表參考.subprocess.run'):
                with self.assertRaises(ValueError):refresh_google_reference(config,cache)
            self.assertEqual(cache.read_bytes(),before)

    def test_fresh_download_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);downloads=root/'downloads';downloads.mkdir()
            old=downloads/'Glossary.xlsx';fixture(old,name='舊名稱')
            fresh=root/'fixture.xlsx';fixture(fresh,name='新名稱')
            cache=root/'cache.xlsx';config=root/'config.json'
            config.write_text(json.dumps({'spreadsheet_id':'fictitious_id','title':'Glossary','url':'https://docs.google.com/spreadsheets/d/fictitious_id/edit','download_directory':str(downloads),'timeout_seconds':1}))
            def produce(*args,**kwargs):shutil.copy2(fresh,downloads/'Glossary (1).xlsx')
            with patch('試算表參考.subprocess.run',side_effect=produce):refresh_google_reference(config,cache)
            _,_,pairs=read_xlsx_reference(cache)
            self.assertEqual(pairs,[('王宜軍','新名稱')])
            self.assertTrue(old.exists())


if __name__=='__main__':unittest.main()
