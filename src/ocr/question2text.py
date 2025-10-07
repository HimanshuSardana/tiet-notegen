import os
import pymupdf
from PIL import Image
import pytesseract
import io


class Question2Text:
    def __init__(self, question_papers_dir, text_files_dir, ocr=True):
        self.question_papers_dir = question_papers_dir
        self.text_files_dir = text_files_dir
        self.use_ocr = ocr

    def convert_pdfs_to_text(self):
        """
        Convert all PDF files in the question_papers_dir to text files.
        """
        os.makedirs(self.text_files_dir, exist_ok=True)

        for filename in os.listdir(self.question_papers_dir):
            if filename.lower().endswith(".pdf"):
                pdf_path = os.path.join(self.question_papers_dir, filename)
                text_path = os.path.join(
                    self.text_files_dir, filename.replace(".pdf", ".txt")
                )
                self.pdf_to_text(pdf_path, text_path)

    def pdf_to_text(self, pdf_path, text_path):
        doc = pymupdf.open(pdf_path)
        doc_text = ""

        for i, page in enumerate(doc):
            text = page.get_text("text")

            # If no text or mostly empty → try OCR
            if self.use_ocr and len(text.strip()) < 30:
                print(f" - Page {i + 1}: No extractable text found, running OCR...")
                pix = page.get_pixmap(dpi=300)  # render page to image
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img)

            doc_text += text + "\n"

        with open(text_path, "w", encoding="utf-8") as f:
            f.write(doc_text)

        doc.close()
