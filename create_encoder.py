# encoder.py
"""
Encoder module for text embeddings and similarity scoring
Used in Resume Screening App
"""

from sentence_transformers import SentenceTransformer, util

# ---------------- Initialize Model ----------------
def load_model(model_name='all-MiniLM-L6-v2', device='cpu'):
    """
    Loads SentenceTransformer model on CPU or GPU.
    Default model: all-MiniLM-L6-v2
    """
    print(f"Loading model: {model_name} on {device}...")
    return SentenceTransformer(model_name, device=device)

# ---------------- Encode Sentences ----------------
def encode_sentences(model, sentences):
    """
    Encodes a list of sentences into embeddings.
    Returns tensor embeddings for similarity calculation.
    """
    if not sentences:
        return []
    return model.encode(sentences, convert_to_tensor=True)

# ---------------- Calculate Similarity ----------------
def calculate_similarity(embeddings1, embeddings2):
    """
    Calculates cosine similarity between two sets of embeddings.
    Returns similarity matrix.
    """
    if embeddings1 is None or embeddings2 is None:
        return None
    return util.cos_sim(embeddings1, embeddings2)

# ---------------- Get Average Similarity Score ----------------
def get_average_similarity(job_sentences, resume_sentences, model):
    """
    Computes average similarity score between job description and resume text.
    Returns:
        avg_score: Average similarity value
        scores: List of (job_sentence, similarity_score)
    """
    job_embeddings = encode_sentences(model, job_sentences)
    resume_embeddings = encode_sentences(model, resume_sentences)

    similarity_matrix = calculate_similarity(job_embeddings, resume_embeddings)

    scores = []
    for i, job_sent in enumerate(job_sentences):
        max_sim = max(similarity_matrix[i]).item()
        scores.append((job_sent, max_sim))

    avg_score = sum(score for _, score in scores) / len(scores) if scores else 0
    return avg_score, scores


# ---------------- Test Script ----------------
if __name__ == "__main__":
    # Quick test
    model = load_model()

    job_desc = ["Strong Python programming skills", "Experience in machine learning"]
    resume = ["Proficient in Python", "Worked on ML projects"]

    avg, score_list = get_average_similarity(job_desc, resume, model)
    print(f"Average Similarity: {avg}")
    print("Scores:", score_list)
