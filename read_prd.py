from docx import Document
import sys

try:
    doc = Document(r'c:\Users\Administrator\Desktop\BAM\BAM_PRD_MVP1_AntiGravity.docx')
    text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
    with open(r'c:\Users\Administrator\Desktop\BAM\PRD.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Done writing to PRD.txt")
except Exception as e:
    print("Error:", e)
