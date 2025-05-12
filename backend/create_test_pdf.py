from fpdf import FPDF
import os

def create_test_pdf():
    # Create PDF object
    pdf = FPDF()
    pdf.add_page()
    
    # Set font
    pdf.set_font("Arial", size=12)
    
    # Read the text file
    with open('data/uploaded_files/test_document.txt', 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Add content to PDF
    pdf.multi_cell(0, 10, content)
    
    # Save the PDF
    pdf_path = 'data/uploaded_files/test_document.pdf'
    pdf.output(pdf_path)
    print(f"PDF created at: {pdf_path}")

if __name__ == "__main__":
    create_test_pdf() 