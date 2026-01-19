from flask import Flask, request, jsonify
import os
import re
import numpy as np
import pdfplumber
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from flask_cors import CORS


app = Flask(__name__)
CORS(app)  # allow frontend requests (important)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -----------------------------
# PDF extraction
# -----------------------------
def extract_text_from_pdf(pdf_path: str) -> str:
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            all_text.append(page_text)
    return "\n".join(all_text).strip()


# -----------------------------
# Cleaning
# -----------------------------
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " ", text)
    text = re.sub(r"\+?\d[\d\s().-]{7,}\d", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s+./-]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text).strip()
    return text


def remove_noise_lines(text: str) -> str:
    if not text:
        return ""
    noise_patterns = [
        r"\bdate of birth\b", r"\bdob\b", r"\bgender\b", r"\bnationality\b",
        r"\bmarital status\b", r"\baddress\b", r"\bhobbies\b", r"\binterests\b",
        r"\bdeclaration\b", r"\bi hereby declare\b", r"\breferences?\b"
    ]
    lines = text.split("\n")
    kept = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(re.search(p, line) for p in noise_patterns):
            continue
        kept.append(line)
    return "\n".join(kept)


def preprocess(text: str) -> str:
    return remove_noise_lines(clean_text(text))


# -----------------------------
# Chunking
# -----------------------------
def chunk_text(text: str, min_len: int = 25):
    if not text:
        return []
    raw_lines = [ln.strip() for ln in text.split("\n")]
    chunks = [ln for ln in raw_lines if len(ln) >= min_len]

    if len(chunks) < 3:
        parts = re.split(r"[•\-]\s+|\.\s+", text)
        chunks = [p.strip() for p in parts if len(p.strip()) >= min_len]

    return chunks


# -----------------------------
# Model (load once!)
# -----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")


@app.route("/match", methods=["POST"])
def match_resume():
    try:
        jd_text = request.form.get("jd", "")
        resume_file = request.files.get("resume")

        if not jd_text.strip():
            return jsonify({"error": "JD is missing"}), 400

        if not resume_file:
            return jsonify({"error": "Resume PDF is missing"}), 400

        # Save PDF
        pdf_path = os.path.join(UPLOAD_FOLDER, resume_file.filename)
        resume_file.save(pdf_path)

        # Extract resume text
        resume_text = extract_text_from_pdf(pdf_path)

        if not resume_text.strip():
            return jsonify({"error": "Could not extract text from PDF (maybe scanned PDF)"}), 400

        # Preprocess
        jd_clean = preprocess(jd_text)
        resume_clean = preprocess(resume_text)

        chunks = chunk_text(resume_clean)

        if not chunks:
            return jsonify({"error": "Resume chunking failed"}), 400

        # Embeddings
        jd_emb = model.encode([jd_clean], normalize_embeddings=True)
        chunk_embs = model.encode(chunks, normalize_embeddings=True)

        sims = cosine_similarity(jd_emb, chunk_embs)[0]

        # Top 5 chunks
        top_k = min(5, len(chunks))
        top_indices = np.argsort(sims)[::-1][:top_k]

        top_chunks = []
        for idx in top_indices:
            top_chunks.append({
                "chunk": chunks[idx],
                "similarity": round(float(sims[idx]) * 100, 2)
            })

        filtered_resume = "\n".join([x["chunk"] for x in top_chunks])
        filtered_emb = model.encode([filtered_resume], normalize_embeddings=True)
        final_score = cosine_similarity(jd_emb, filtered_emb)[0][0] * 100

        return jsonify({
            "final_match_score": round(float(final_score), 2),
            "top_chunks": top_chunks,
            "filtered_resume_text": filtered_resume
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
