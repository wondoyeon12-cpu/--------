import fitz
import sys

pdf_path = r"C:\Users\user\Downloads\포스플러스\FOS 서비스 소개 랜딩 페이지 기획_26.02.1１_v4.pdf"
try:
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += f"----- Page {page.number + 1} -----\n"
        text += page.get_text() + "\n"
        
    with open("pdf_extracted.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("done")
except Exception as e:
    print(f"Error: {e}")
