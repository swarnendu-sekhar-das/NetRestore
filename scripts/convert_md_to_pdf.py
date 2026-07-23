import os
import glob
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def convert_md_to_pdf(md_filepath, pdf_filepath):
    """
    Reads a markdown file and converts its text into a basic PDF.
    This simulates having a PDF version of the SOP in the dataset.
    """
    with open(md_filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create a basic PDF document using reportlab
    doc = SimpleDocTemplate(pdf_filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    Story = []

    # Simple heuristic to chunk paragraphs by empty lines
    paragraphs = content.split('\n\n')
    for p in paragraphs:
        # Clean up Markdown headers for PDF rendering
        p = p.replace('#', '').strip()
        if not p:
            continue
        
        # Reportlab doesn't natively parse markdown natively without advanced extensions,
        # so we inject basic HTML-like breaks for newlines within the paragraph
        p = p.replace('\n', '<br/>')
        
        # Add the paragraph to the PDF
        Story.append(Paragraph(p, styles["Normal"]))
        Story.append(Spacer(1, 12))

    doc.build(Story)
    print(f"Converted {os.path.basename(md_filepath)} -> {os.path.basename(pdf_filepath)}")

def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    
    # Find all existing markdown SOPs in the root of data/
    md_files = glob.glob(os.path.join(data_dir, '*_sop.md')) + glob.glob(os.path.join(data_dir, '*_mop.md'))
    
    if not md_files:
        print("No .md files found to convert.")
        return

    print(f"Found {len(md_files)} Markdown files. Starting conversion to PDF...")
    
    for md_file in md_files:
        filename_base = os.path.splitext(os.path.basename(md_file))[0]
        pdf_file = os.path.join(data_dir, f"{filename_base}.pdf")
        
        try:
            convert_md_to_pdf(md_file, pdf_file)
        except Exception as e:
            print(f"Failed to convert {md_file}: {e}")
            
    print("PDF Conversion Complete!")

if __name__ == "__main__":
    main()
