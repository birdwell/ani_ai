# utils/retrieval.py
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import faiss
import numpy as np

VECTOR_DB_PATH = "anime_vectors.index"
EMBEDDINGS_FILE = "embeddings_cache.pkl"

def load_faiss_index():
    return faiss.read_index(VECTOR_DB_PATH)

def load_embeddings_and_ids():
    with open(EMBEDDINGS_FILE, "rb") as f:
        data = pickle.load(f)
    return data["ids"], data["embeddings"]

def retrieve_similar_anime(query: str, top_k: int = 20) -> list:
    """
    Converts the query into an embedding and returns the top_k anime IDs from the FAISS index.
    """
    # Use the same model as was used to build the index.
    model = SentenceTransformer("all-mpnet-base-v2")
    query_embedding = model.encode(query, convert_to_numpy=True).astype("float32")
    
    index = load_faiss_index()
    distances, indices = index.search(np.array([query_embedding]), top_k)
    
    ids, _ = load_embeddings_and_ids()
    candidate_ids = []
    for idx in indices[0]:
        if idx < len(ids):
            candidate_ids.append(ids[idx])
    return candidate_ids