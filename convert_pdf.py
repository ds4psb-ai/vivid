from pdf2docx import Converter
import sys
import os

pdf_file = '/Users/ted/Desktop/AI 영상 제작 워크플로우 마스터.pdf'
docx_file = '/Users/ted/Desktop/AI 영상 제작 워크플로우 마스터.docx'

try:
    cv = Converter(pdf_file)
    cv.convert(docx_file, start=0, end=None)
    cv.close()
    print(f"Successfully converted {pdf_file} to {docx_file}")
except Exception as e:
    print(f"Error converting file: {e}")
    sys.exit(1)
