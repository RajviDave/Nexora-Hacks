import re
import numpy as np
import pdfplumber
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# -----------------------------
# 1) PDF TEXT EXTRACTION
# -----------------------------
def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a Resume PDF using pdfplumber.
    Works best for text-based PDFs (most resumes).
    """
    all_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            all_text.append(page_text)

    return "\n".join(all_text).strip()


# -----------------------------
# 2) CLEANING PIPELINE
# -----------------------------
def clean_text(text: str) -> str:
    """
    Cleans Resume/JD text by removing noise (emails, phones, links, junk symbols)
    while keeping tech tokens like: c++, node.js, ci/cd, scikit-learn.
    """
    if not text:
        return ""

    text = text.lower()

    # remove emails
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " ", text)

    # remove phone numbers
    text = re.sub(r"\+?\d[\d\s().-]{7,}\d", " ", text)

    # remove urls
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # remove unwanted chars (keep + . / - for tech tokens)
    text = re.sub(r"[^a-z0-9\s+./-]", " ", text)

    # normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text).strip()

    return text


def remove_noise_lines(text: str) -> str:
    """
    Removes common resume fluff lines that don't help matching.
    """
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
    """
    Final preprocessing pipeline for both JD and Resume text.
    """
    return remove_noise_lines(clean_text(text))


# -----------------------------
# 3) RESUME CHUNKING
# -----------------------------
def chunk_text(text: str, min_len: int = 25) -> list:
    """
    Splits resume into meaningful chunks (lines/blocks).
    Keeps only chunks above a minimum length.
    """
    if not text:
        return []

    # split by newline first (best for resumes)
    raw_lines = [ln.strip() for ln in text.split("\n")]

    # keep only meaningful lines
    chunks = [ln for ln in raw_lines if len(ln) >= min_len]

    # fallback: resume may be in one paragraph
    if len(chunks) < 3:
        parts = re.split(r"[•\-]\s+|\.\s+", text)
        chunks = [p.strip() for p in parts if len(p.strip()) >= min_len]

    return chunks


# -----------------------------
# 4) MODEL + MATCHING
# -----------------------------
class JDResumeMatcher:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Loads model once (important for performance).
        """
        self.model = SentenceTransformer(model_name)

    def get_top_k_resume_chunks(self, jd_text: str, resume_text: str, top_k: int = 5) -> dict:
        """
        Steps:
        1) Clean JD & Resume
        2) Chunk resume
        3) Embed JD and each chunk
        4) Similarity scores
        5) Pick Top K chunks
        6) Create filtered resume
        7) Final match score
        """
        jd_clean = preprocess(jd_text)
        resume_clean = preprocess(resume_text)

        chunks = chunk_text(resume_clean)

        if not jd_clean:
            return {"error": "Job Description is empty after preprocessing."}
        if not chunks:
            return {"error": "Resume text is empty or could not be chunked properly."}

        # Embeddings (normalize for cosine similarity)
        jd_emb = self.model.encode([jd_clean], normalize_embeddings=True)
        chunk_embs = self.model.encode(chunks, normalize_embeddings=True)

        # Similarity score for each chunk
        sims = cosine_similarity(jd_emb, chunk_embs)[0]

        # Top K selection
        top_k = min(top_k, len(chunks))
        top_indices = np.argsort(sims)[::-1][:top_k]

        top_chunks = []
        for idx in top_indices:
            top_chunks.append({
                "chunk": chunks[idx],
                "similarity": round(float(sims[idx]) * 100, 2)
            })

        # Filtered resume = top K relevant lines
        filtered_resume = "\n".join([x["chunk"] for x in top_chunks])

        # Final similarity score using filtered resume
        filtered_emb = self.model.encode([filtered_resume], normalize_embeddings=True)
        final_score = cosine_similarity(jd_emb, filtered_emb)[0][0] * 100

        return {
            "final_match_score": round(float(final_score), 2),
            "top_chunks": top_chunks,
            "filtered_resume_text": filtered_resume,
            "jd_clean_text": jd_clean
        }


# -----------------------------
# 5) MAIN EXECUTION
# -----------------------------
if __name__ == "__main__":

    # ✅ 1) Give your resume pdf path here
    RESUME_PDF_PATH = "Rajvi_Resume (2).pdf"  # change this

    # ✅ 2) Paste JD text here (or take input)
    JD_TEXT = """
    We are looking for a frontend developer with experience in React, REST APIs,
    JavaScript, Git, and basic knowledge of Docker and AWS.
    """

    print("✅ Extracting Resume text from PDF...")
    resume_text = extract_text_from_pdf(RESUME_PDF_PATH)

    if not resume_text:
        print("❌ ERROR: Could not extract text from PDF. Maybe it's scanned image PDF.")
        exit()

    print("✅ Running JD-Resume Matching...")

    matcher = JDResumeMatcher()
    result = matcher.get_top_k_resume_chunks(JD_TEXT, resume_text, top_k=5)

    if "error" in result:
        print("❌ ERROR:", result["error"])
        exit()

    print("\n================ FINAL RESULT ================")
    print("✅ Final Match Score:", result["final_match_score"], "%")

    print("\n✅ Top Relevant Resume Chunks:")
    for item in result["top_chunks"]:
        print(f"- {item['similarity']}% | {item['chunk']}")

    print("\n✅ Filtered Resume Text (Most Relevant):\n")
    print(result["filtered_resume_text"])
