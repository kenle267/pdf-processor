from flask import Flask, render_template, request, send_file
import fitz
import re
import os
from werkzeug.utils import secure_filename

from pdf2image import convert_from_path

# from pdf2image import convert_from_path
# from PIL import Image
# from fpdf import FPDF

# Additional Underwriting PDF Process Summarized
# Additional Underwriting requires compiling multiple pages into a single PDF
# 1. California Vehicle Annual Mileage Worksheet (Catgeorized miles)
# 2. Page 2 of ^^^ with customer signature
# 3. Picture of odometer
# 4. Page 1 of Auto Insurance Declaration page
# 5. Page 2 of Auto Insurance Declaration page
# 6. Evidence of Home Insurance OR Utility Bill

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER

# extracts and returns the first page where the search string is located
def extract_declaration_pages(pdf_path, searchStr):
    doc = fitz.open(pdf_path)
    outputPdf = fitz.open()

    pageNum = doc.page_count
    for i in range(pageNum):
        text = doc[i].get_text()
        res = re.search(re.escape(searchStr), text, re.IGNORECASE)
        if text and res:
            print(f"Found on page: {i+1}")
            outputPdf.insert_pdf(doc, from_page=i, to_page=i)
            break
    return outputPdf if len(outputPdf) > 0 else None

@app.route("/" , methods=["GET", "POST"])
def upload_files():
    if request.method == "POST":
        # error handling
        if "auto_pdf" not in request.files or "home_pdf" not in request.files:
            return "Make sure both files are uploaded"

        auto_file = request.files["auto_pdf"]
        home_file = request.files["home_pdf"]

        if auto_file.filename == "" or home_file.filename == "":
            return "Make sure both files are uploaded"

        auto_path = os.path.join(UPLOAD_FOLDER, secure_filename(auto_file.filename))
        home_path = os.path.join(UPLOAD_FOLDER, secure_filename(home_file.filename))

        auto_file.save(auto_path)
        home_file.save(home_path)

        searchStr1 = "Auto Insurance Declaration Page"
        searchStr2 = "Declaration Page (continued)"
        searchStr3 = "Evidence of Insurance for Mortgagee/Other"

        page1 = extract_declaration_pages(auto_path, searchStr1)
        page2 = extract_declaration_pages(auto_path, searchStr2)
        page3 = extract_declaration_pages(home_path, searchStr3)

        outputPdf = fitz.open()
        pages = [page1, page2, page3]
        for page in pages:
            if page:
                outputPdf.insert_pdf(page)
        
        output_pdf_path = os.path.join(app.config["PROCESSED_FOLDER"], "output.pdf")
        outputPdf.save(output_pdf_path)
        
        if len(outputPdf) != 3:
            print("❌ Failed to extract all pages")
        else:
            print("✅ Successfully extracted all pages")
        return send_file(output_pdf_path, as_attachment=True)
        
        #outputPdf.save("/mnt/c/Users/kenny/Downloads/compiled_output.pdf")
    return render_template("index.html")
if __name__ == "__main__":
    app.run(debug=True)