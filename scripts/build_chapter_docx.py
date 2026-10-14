"""Build a chapter review copy using the original document's OOXML styles.

The original file is never modified. No external dependencies are required.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy
import argparse
import re
import xml.etree.ElementTree as ET

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
ET.register_namespace('w', W)


def tag(name):
    return '{' + W + '}' + name


def source_table_for_output(table):
    """Retain source cells and styles, replacing embedded diagrams by slots."""
    result = deepcopy(table)
    for parent in result.iter():
        for child in list(parent):
            if child.tag in (tag('drawing'), tag('pict')):
                index = list(parent).index(child)
                parent.remove(child)
                slot = ET.Element(tag('t'))
                slot.text = '[图示待插入]'
                parent.insert(index, slot)
    return result


def table_markdown(table):
    """Readable companion text; Word retains the source's merged-cell layout."""
    table = source_table_for_output(table)
    rows = [
        [''.join(node.text or '' for node in cell.findall('.//w:t', NS))
         for cell in row.findall('w:tc', NS)]
        for row in table.findall('w:tr', NS)
    ]
    width = max(map(len, rows))
    lines = []
    for index, row in enumerate(rows):
        padded = row + [''] * (width - len(row))
        lines.append('| ' + ' | '.join(value.replace('|', '\\|').replace('\n', '<br>') for value in padded) + ' |')
        if index == 0:
            lines.append('| ' + ' | '.join(['---'] * width) + ' |')
    return '\n'.join(lines)


def parse_markdown_table(block):
    """Read simple prose tables, rejecting inconsistent column counts."""
    lines = block.strip().splitlines()
    if len(lines) < 2 or not all(line.strip().startswith('|') and line.strip().endswith('|') for line in lines):
        return None
    rows = [[cell.strip().replace('\\|', '|') for cell in re.split(r'(?<!\\)\|', line.strip()[1:-1])] for line in lines]
    if not all(re.fullmatch(r':?-{3,}:?', cell) for cell in rows[1]):
        return None
    width = len(rows[0])
    if not all(len(row) == width for row in rows):
        raise ValueError('Inconsistent Markdown table width')
    return [rows[0]] + rows[2:]


def new_table_from_markdown(rows, template):
    """Use the manuscript's table typography and width for new chapter tables."""
    result = ET.Element(tag('tbl'))
    props = deepcopy(template.find('w:tblPr', NS))
    width = int(props.find('w:tblW', NS).get(tag('w')))
    layout = props.find('w:tblLayout', NS)
    if layout is None:
        layout = ET.SubElement(props, tag('tblLayout'))
    layout.set(tag('type'), 'fixed')
    result.append(props)
    count = len(rows[0])
    widths = [width // count] * count
    widths[-1] += width - sum(widths)
    grid = ET.SubElement(result, tag('tblGrid'))
    for col_width in widths:
        ET.SubElement(grid, tag('gridCol'), {tag('w'): str(col_width)})
    template_rows = template.findall('w:tr', NS)
    for index, row in enumerate(rows):
        tr = ET.SubElement(result, tag('tr'))
        tr_props = ET.SubElement(tr, tag('trPr'))
        if index == 0:
            ET.SubElement(tr_props, tag('tblHeader'))
        ET.SubElement(tr_props, tag('cantSplit'))
        sample = template_rows[0 if index == 0 else 1].findall('w:tc', NS)[1]
        for value, col_width in zip(row, widths):
            cell = ET.SubElement(tr, tag('tc'))
            cell_props = deepcopy(sample.find('w:tcPr', NS))
            cell_props.find('w:tcW', NS).set(tag('w'), str(col_width))
            # Use header/body rules from the same original three-line table.
            borders = cell_props.find('w:tcBorders', NS)
            if index > 1:
                borders.find('w:top', NS).set(tag('val'), 'nil')
            if index == len(rows) - 1:
                bottom = borders.find('w:bottom', NS)
                bottom.set(tag('val'), 'single')
                bottom.set(tag('sz'), '12')
            cell.append(cell_props)
            sample_p = sample.find('w:p', NS)
            p = ET.SubElement(cell, tag('p'))
            p.append(deepcopy(sample_p.find('w:pPr', NS)))
            for segment_index, segment in enumerate(value.split('<br>')):
                run = ET.SubElement(p, tag('r'))
                run_props = sample_p.find('w:r/w:rPr', NS)
                if run_props is not None:
                    run.append(deepcopy(run_props))
                if segment_index:
                    ET.SubElement(run, tag('br'))
                t = ET.SubElement(run, tag('t'))
                t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                t.text = segment
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('markdown')
    parser.add_argument('output')
    args = parser.parse_args()
    with ZipFile(args.source) as archive:
        original = archive.read('word/document.xml')
        # Keep all original namespaces, including those used by mc:Ignorable.
        # Replace only the body's interior in the original XML serialization.
        root = ET.fromstring(original)
        body = root.find('w:body', NS)
        original_paragraphs = body.findall('w:p', NS)
        original_tables = body.findall('w:tbl', NS)
        body_properties = deepcopy(original_paragraphs[85].find('w:pPr', NS))
        section = deepcopy(body.find('w:sectPr', NS))
        children = []
        for block in Path(args.markdown).read_text().strip().split('\n\n'):
            text = block.strip()
            if not text:
                continue
            markdown_rows = parse_markdown_table(text)
            if markdown_rows is not None:
                children.append(ET.tostring(new_table_from_markdown(markdown_rows, original_tables[-1]), encoding='unicode'))
                continue
            table_marker = re.match(r'^<!-- SOURCE_TABLE:(\d+) -->', text)
            if table_marker:
                index = int(table_marker.group(1)) - 1
                if not 0 <= index < len(original_tables):
                    raise ValueError('Invalid source table index')
                companion = text[table_marker.end():].strip()
                if companion and companion != table_markdown(original_tables[index]):
                    raise ValueError('Markdown table differs from source; resolve before building')
                # Preserve cells, merged regions, widths, and source formatting.
                children.append(ET.tostring(source_table_for_output(original_tables[index]), encoding='unicode'))
                continue
            equation_marker = re.fullmatch(r'<!-- SOURCE_EQUATION:(\d+) -->', text)
            if equation_marker:
                index = int(equation_marker.group(1))
                if not 0 <= index < len(original_paragraphs):
                    raise ValueError('Invalid source equation paragraph')
                equation = original_paragraphs[index]
                if equation.find('.//w:object', NS) is None:
                    raise ValueError('Source paragraph does not contain an equation object')
                children.append(ET.tostring(deepcopy(equation), encoding='unicode'))
                continue
            p = ET.Element(tag('p'))
            heading = re.match(r'^(#{1,3})\s+(.+)$', text)
            if heading:
                level = len(heading.group(1))
                text = heading.group(2)
                props = ET.SubElement(p, tag('pPr'))
                ET.SubElement(props, tag('pStyle'), {tag('val'): str(level + 1)})
                # Explicit numbers are already present in the chapter text.
                numbering = ET.SubElement(props, tag('numPr'))
                ET.SubElement(numbering, tag('numId'), {tag('val'): '0'})
            else:
                p.append(deepcopy(body_properties))
            run = ET.SubElement(p, tag('r'))
            t = ET.SubElement(run, tag('t'))
            t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            t.text = text
            children.append(ET.tostring(p, encoding='unicode'))
        children.append(ET.tostring(section, encoding='unicode'))
        source_xml = original.decode('utf-8')
        match = re.search(r'(<w:body\b[^>]*>)(.*?)(</w:body>)', source_xml, re.S)
        if not match:
            raise RuntimeError('Cannot locate original document body')
        new_xml = source_xml[:match.start(2)] + ''.join(children) + source_xml[match.end(2):]
        ET.fromstring(new_xml)
        target = Path(args.output)
        if target.resolve() == Path(args.source).resolve():
            raise RuntimeError('Refusing to overwrite the original manuscript')
        target.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(target, 'w', ZIP_DEFLATED) as out:
            for entry in archive.infolist():
                payload = new_xml.encode('utf-8') if entry.filename == 'word/document.xml' else archive.read(entry.filename)
                out.writestr(entry, payload)
    print(target)


if __name__ == '__main__':
    main()
