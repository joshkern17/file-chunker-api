from flask import Flask, request, jsonify
import pdfplumber
import mammoth

app = Flask(__name__)

def chunk_text(raw_text, paras_per_chunk=3):
    paras = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 40]
    chunks = []
    for i in range(0, len(paras), paras_per_chunk):
        chunks.append("\n\n".join(paras[i : i + paras_per_chunk]))
    return chunks

@app.route("/extract", methods=["POST"])
def extract():
    if "file" not in request.files:
        return jsonify(error="No file part"), 400
    f = request.files["file"]
    mime = f.mimetype

    try:
        if mime == "application/pdf":
            with pdfplumber.open(f.stream) as pdf:
                raw = "\n\n".join(page.extract_text() or "" for page in pdf.pages)
        elif mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            f.stream.seek(0)
            result = mammoth.extract_raw_text(f.stream)
            raw    = result.value
        elif mime.startswith("text/"):
            raw = f.stream.read().decode("utf-8")
        else:
            return jsonify(error=f"Unsupported MIME type {mime}"), 415

        chunks = chunk_text(raw)
        return jsonify(chunk_count=len(chunks), chunks=chunks)
    except Exception as e:
        print("Error parsing:", e)
        return jsonify(error="Parse error"), 500

if __name__ == "__main__":
    # Render gives you the PORT env var automatically
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
