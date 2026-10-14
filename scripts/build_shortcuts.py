#!/usr/bin/env python3
"""Generate unsigned opening shortcuts; signing/importing is explicit."""
import argparse
import plistlib
import uuid
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--sheet-url',required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
if not args.sheet_url.startswith('https://docs.google.com/spreadsheets/d/'):
    parser.error('Provide your own Sheet URL.')
args.output.mkdir(parents=True,exist_ok=True)
def action(identifier, **parameters):
    return {'WFWorkflowActionIdentifier':identifier,'WFWorkflowActionParameters':{'UUID':str(uuid.uuid4()).upper(),**parameters}}
def app(identifier,name):
    return action('is.workflow.actions.openapp',WFAppIdentifier=identifier,WFSelectedApp={'BundleIdentifier':identifier,'Name':name})
url_id=str(uuid.uuid4()).upper()
url=action('is.workflow.actions.url',WFURLActionURL=args.sheet_url)
url['WFWorkflowActionParameters']['UUID']=url_id
open_url=action('is.workflow.actions.openurl',WFInput={'Value':{'OutputUUID':url_id,'Type':'ActionOutput','OutputName':'URL'},'WFSerializationType':'WFTextTokenAttachment'})
shortcuts={'會議詞彙表':[url,open_url],'Mac錄音入口':[app('com.hyprnote.stable','Anarlog')],'iPhone錄音入口':[app('com.apple.VoiceMemos','Voice Memos')]}
for name,actions in shortcuts.items():
    target=args.output/(name+'.shortcut')
    if target.exists():
        raise SystemExit('Refusing to overwrite an existing definition: '+str(target))
    data={'WFWorkflowName':name,'WFWorkflowClientVersion':'3600.0.2.1','WFWorkflowMinimumClientVersion':900,'WFWorkflowMinimumClientVersionString':'900','WFWorkflowIcon':{'WFWorkflowIconStartColor':4282601983,'WFWorkflowIconGlyphNumber':59511},'WFWorkflowImportQuestions':[],'WFWorkflowTypes':[],'WFWorkflowInputContentItemClasses':[],'WFWorkflowActions':actions}
    target.write_bytes(plistlib.dumps(data,fmt=plistlib.FMT_BINARY))
    print(target)
