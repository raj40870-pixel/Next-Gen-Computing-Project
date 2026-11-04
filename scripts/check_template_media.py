import zipfile
import xml.etree.ElementTree as ET

docx_path = r"C:\Users\Kamaljit\Downloads\CA2_Format.docx"

with zipfile.ZipFile(docx_path, 'r') as z:
    file_list = z.namelist()
    media_files = [f for f in file_list if f.startswith('word/media/')]
    print("Media files in original CA2_Format.docx:", media_files)

    doc_xml = z.read('word/document.xml').decode('utf-8')
    print("Does document.xml contain 'drawing' tag?", '<w:drawing>' in doc_xml)
    print("Does document.xml contain 'pict' tag?", '<w:pict>' in doc_xml)
    print("Does document.xml contain 'blip' tag?", '<a:blip' in doc_xml)

    # Let's extract any relationships to media
    if 'word/_rels/document.xml.rels' in file_list:
        rels_xml = z.read('word/_rels/document.xml.rels').decode('utf-8')
        print("Media relationships:")
        root = ET.fromstring(rels_xml)
        for rel in root:
            if 'image' in rel.attrib.get('Type', ''):
                print(rel.attrib)
