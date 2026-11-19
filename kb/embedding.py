import numpy as np

MODEL_NAME = "BAAI/bge-m3"      # best quality, about 2 GB. For a weak computer use "intfloat/multilingual-e5-small"
_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
        _model.max_seq_length = 512
    return _model


def encode(texts):
    vecs = get_model().encode(texts, normalize_embeddings=True, batch_size=8)
    return np.asarray(vecs, dtype=np.float32)