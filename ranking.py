import os
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
from sklearn.metrics.pairwise import cosine_similarity       # type: ignore
from text_processing import (
    preprocess_text,
    extract_text_from_pdf,
    extract_text_from_docx,
)


# Function to extract features using TF-IDF Vectorizer
def extract_features(resume_texts):
    vectorizer = TfidfVectorizer()
    features = vectorizer.fit_transform(resume_texts)
    return features


# Function to compute similarity between two texts
def compute_similarity(text1, text2):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
    return similarity


# Function to rank resumes based on similarity to the job description
def rank_resumes(file_paths, job_description):
    print(f"Processing {len(file_paths)} resumes")

    # Preprocess job description once
    job_description_processed = preprocess_text(job_description)

    ranked_resumes = []

    for file_path in file_paths:
        # Extract text by extension
        if file_path.lower().endswith(".pdf"):
            resume_text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(".docx"):
            resume_text = extract_text_from_docx(file_path)
        else:
            # Skip unsupported file types
            continue

        # Preprocess resume text
        resume_text_processed = preprocess_text(resume_text)

        # Build TF-IDF for job description + this resume
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(
            [job_description_processed, resume_text_processed]
        )

        similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
        final_score = round(similarity * 100, 1)

        # Store as tuple: (filename, score)
        ranked_resumes.append((os.path.basename(file_path), final_score))

    # Sort by score (index 1) descending
    ranked_resumes.sort(key=lambda x: x[1], reverse=True)
    return ranked_resumes
