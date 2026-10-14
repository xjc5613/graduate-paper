"""Structural, retention, and source-copy checks for the chapter review artifact."""
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import re
import json
import hashlib
import shutil

SOURCE = Path('论文保留初版-基于动态演化的智能建造领域关键技术识别及预测_副本3.docx')
MD = Path('chapters/01-introduction.md')
OUTPUT = Path('output/docx/第1章_绪论_审阅稿.docx')
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

text = MD.read_text()
original = Path('refs/source-extracts/chapter01-original.txt').read_text()

def citations(value):
    result = set()
    for match in re.findall(r'\[(\d+(?:\s*[-—–,，]\s*\d+)*)\]', value):
        for item in re.split('[,，]', match):
            nums = re.split('[-—–]', item)
            if len(nums) == 2:
                result.update(range(int(nums[0]), int(nums[1]) + 1))
            else:
                result.add(int(nums[0]))
    return result

with ZipFile(SOURCE) as source, ZipFile(OUTPUT) as output:
    assert output.testzip() is None
    for name in output.namelist():
        if name.endswith('.xml') or name.endswith('.rels'):
            ET.fromstring(output.read(name))
    orig_xml = ET.fromstring(source.read('word/document.xml'))
    result_xml = ET.fromstring(output.read('word/document.xml'))
    pars = result_xml.findall('w:body/w:p', NS)
    doc_text = '\n\n'.join(''.join(x.text or '' for x in p.findall('.//w:t', NS)) for p in pars)
    expected_text = re.sub(r'^#{1,3}\s+', '', text.strip(), flags=re.M)
    assert doc_text == expected_text, 'DOCX text differs from Markdown'
    assert source.read('word/styles.xml') == output.read('word/styles.xml'), 'Styles changed'
    old_section = orig_xml.find('w:body/w:sectPr', NS)
    new_section = result_xml.find('w:body/w:sectPr', NS)
    assert ET.tostring(old_section) == ET.tostring(new_section), 'Page settings changed'
    assert not result_xml.findall('.//w:drawing', NS), 'Unexpected embedded figure'
    heading_count = len([p for p in pars if p.find('w:pPr/w:pStyle', NS) is not None])

removed = sorted(citations(original) - citations(text))
retention_numbers = ['6.60%', '6.67%', '168011', '8871', '5.57%', '547630', '15.15%', '81', '1230.1', '4.3%', '24.6%']
report = {
    'han_characters': len(re.findall(r'[\u4e00-\u9fff]', text)),
    'headings': re.findall(r'^#{1,3} .+$', text, re.M),
    'word_heading_count': heading_count,
    'paragraphs': len(pars),
    'missing_original_citation_numbers': removed,
    'authorized_removed_GNN_citations': [31, 32, 33, 34, 35],
    'missing_background_numbers': [x for x in retention_numbers if x not in text.replace(',', '').replace('，', '')],
    'pending_evidence_markers': len(re.findall('待补充', text)),
    'figure_placeholders': re.findall(r'[^\n]*插入位置[^\n]*', text),
    'prohibited_words': [x for x in ['首先', '其次', '最后', '此外', '值得注意的是', '显而易见', '我认为', '用户要求', '请用户', '本章初稿'] if x in text],
    'styles_preserved': True,
    'page_settings_preserved': True,
    'docx_text_equals_markdown': True,
    'original_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'render_available': bool(shutil.which('soffice')),
    'visual_qa': 'not_performed_missing_LibreOffice',
}
Path('plan/review/chapter01-checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
