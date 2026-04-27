import fitz
def extract_pdf(path, out_path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

extract_pdf("Guide pour calculer le score REBA (1).pdf", "reba_text.txt")
extract_pdf("Guide pour calculer le score RULA (1).pdf", "rula_text.txt")
print("Done")
