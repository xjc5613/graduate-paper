"""Check chapter Word text, styles, section geometry, and writing structure."""
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import argparse
import re
import json
import hashlib
import shutil
from build_chapter_docx import table_markdown, source_table_for_output, parse_markdown_table

parser = argparse.ArgumentParser()
parser.add_argument('chapter', type=int)
parser.add_argument('markdown')
parser.add_argument('docx')
parser.add_argument('--baseline')
parser.add_argument('--report')
args = parser.parse_args()
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
source = Path('论文保留初版-基于动态演化的智能建造领域关键技术识别及预测_副本3.docx')
text = Path(args.markdown).read_text().strip()
blocks = text.split('\n\n')
table_indices = []
table_specs = []
equation_positions = []
paragraph_blocks = []
for block in blocks:
    marker = re.match(r'^<!-- SOURCE_TABLE:(\d+) -->', block)
    if marker:
        table_indices.append(int(marker.group(1)) - 1)
        table_specs.append(('source', int(marker.group(1)) - 1))
    elif parse_markdown_table(block) is not None:
        table_specs.append(('markdown', parse_markdown_table(block)))
    else:
        equation_marker = re.fullmatch(r'<!-- SOURCE_EQUATION:(\d+) -->', block)
        if equation_marker:
            equation_positions.append((len(paragraph_blocks), int(equation_marker.group(1))))
        paragraph_blocks.append(re.sub(r'^#{1,3}\s+', '', block))
with ZipFile(source) as original, ZipFile(args.docx) as result:
    assert result.testzip() is None
    for name in result.namelist():
        if name.endswith(('.xml', '.rels')):
            ET.fromstring(result.read(name))
    root = ET.fromstring(result.read('word/document.xml'))
    original_root = ET.fromstring(original.read('word/document.xml'))
    paragraphs = root.findall('w:body/w:p', ns)
    original_paragraphs = original_root.findall('w:body/w:p', ns)
    for position, source_index in equation_positions:
        source_equation = original_paragraphs[source_index]
        assert ET.tostring(paragraphs[position]) == ET.tostring(source_equation), 'Source equation changed'
        paragraph_blocks[position] = ''.join(n.text or '' for n in source_equation.findall('.//w:t', ns))
    expected = '\n\n'.join(paragraph_blocks)
    actual = '\n\n'.join(''.join(n.text or '' for n in p.findall('.//w:t', ns)) for p in paragraphs)
    assert actual == expected, 'Word text differs from Markdown'
    actual_tables = root.findall('w:body/w:tbl', ns)
    original_tables = original_root.findall('w:body/w:tbl', ns)
    assert len(actual_tables) == len(table_specs), 'Table count differs'
    for table, (kind, spec) in zip(actual_tables, table_specs):
        if kind == 'source':
            assert ET.tostring(table) == ET.tostring(source_table_for_output(original_tables[spec])), 'Source table changed'
        else:
            cells = [[''.join(n.text or '' for n in c.findall('.//w:t', ns)) for c in row.findall('w:tc', ns)] for row in table.findall('w:tr', ns)]
            assert cells == [[c.replace('<br>', '') for c in row] for row in spec], 'New table text differs'
            w = '{'+ns['w']+'}'
            widths = [int(c.get(w+'w')) for c in table.findall('w:tblGrid/w:gridCol', ns)]
            assert sum(widths) == int(table.find('w:tblPr/w:tblW', ns).get(w+'w'))
            for row in table.findall('w:tr', ns):
                assert widths == [int(c.find('w:tcPr/w:tcW', ns).get(w+'w')) for c in row.findall('w:tc', ns)]
            assert table.find('w:tr/w:trPr/w:tblHeader', ns) is not None
    for block in blocks:
        marker = re.match(r'^<!-- SOURCE_TABLE:(\d+) -->', block)
        if marker:
            companion = block[marker.end():].strip()
            assert companion == table_markdown(original_tables[int(marker.group(1)) - 1]), 'Markdown table missing or differs'
    assert original.read('word/styles.xml') == result.read('word/styles.xml')
    assert ET.tostring(original_root.find('w:body/w:sectPr', ns)) == ET.tostring(root.find('w:body/w:sectPr', ns))
    assert not root.findall('.//w:drawing', ns)
    headings = []
    for p in paragraphs:
        style = p.find('w:pPr/w:pStyle', ns)
        if style is not None:
            headings.append({'style_id': style.get('{'+ns['w']+'}val'), 'text': ''.join(n.text or '' for n in p.findall('.//w:t', ns))})

if args.baseline:
    baseline = json.loads(Path(args.baseline).read_text())
    for file, digest in baseline.items():
        assert hashlib.sha256(Path(file).read_bytes()).hexdigest() == digest, 'Protected file changed: '+file

body = '\n'.join(
    line for line in '\n\n'.join(block for block in blocks if not block.startswith('<!-- SOURCE_TABLE:') and parse_markdown_table(block) is None).splitlines()
    if not line.startswith(('#', '[', '材料说明：')) and not re.match(r'^表\d+-\d+\s', line)
)
body = re.sub(r'\[待补充[^\n]*\]', '', body)
report = {
    'chapter': args.chapter,
    'han_characters_total': len(re.findall(r'[\u4e00-\u9fff]', text)),
    'han_characters_body_excluding_headings_and_markers': len(re.findall(r'[\u4e00-\u9fff]', body)),
    'paragraphs': len(paragraphs),
    'headings': headings,
    'figure_placeholders': re.findall(r'^\[图[^\n]*', text, re.M),
    'pending_sources': re.findall(r'\[待补充[^\n]*\]', text),
    'forbidden_words': [w for w in ['首先', '其次', '最后', '此外', '值得注意的是', '显而易见', '我认为', '用户要求', '请用户'] if w in text],
    'body_bullets': re.findall(r'^[-*] .+', text, re.M),
    'text_match': True,
    'source_tables_preserved': [index + 1 for index in table_indices],
    'new_tables_verified': sum(kind == 'markdown' for kind, _ in table_specs),
    'source_equation_paragraphs_preserved': [index for _, index in equation_positions],
    'table_diagram_placeholders': len(root.findall('.//w:tbl//w:t', ns)) and sum((n.text or '') == '[图示待插入]' for n in root.findall('.//w:tbl//w:t', ns)),
    'original_styles_and_section_preserved': True,
    'baseline_files_unchanged': bool(args.baseline),
    'soffice_available': bool(shutil.which('soffice')),
    'visual_qa_performed': False,
}
output = Path(args.report or f'plan/review/chapter{args.chapter:02d}-checks.json')
output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
