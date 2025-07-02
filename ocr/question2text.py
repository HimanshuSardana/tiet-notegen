import os
import pymupdf

class Question2Text:
    def __init__(self, question_papers_dir, text_files_dir):
        self.question_papers_dir = question_papers_dir
        self.text_files_dir = text_files_dir

    def convert_pdfs_to_text(self):
        """
        Convert all PDF files in the question_papers_dir to text files.
        """
        for filename in os.listdir(self.question_papers_dir):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(self.question_papers_dir, filename)
                text_path = os.path.join(self.text_files_dir, filename.replace('.pdf', '.txt'))

                # Ensure the text directory exists
                os.makedirs(self.text_files_dir, exist_ok=True)
                
                # Convert PDF to text
                self.pdf_to_text(pdf_path, text_path)

    def pdf_to_text(self, pdf_path, text_path):
        doc = pymupdf.open(pdf_path)
        doc_text = ''
        for page in doc:
            doc_text += page.get_text()
            with open(text_path, 'w', encoding='utf-8') as text_file:
                text_file.write(doc_text)
        doc.close()
