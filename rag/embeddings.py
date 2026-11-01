from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed_texts(texts):
    if not texts:
        return []
    model = get_model()
    vecs = model.encode(list(texts), convert_to_numpy=True, normalize_embeddings=True)
    return [v.tolist() for v in vecs]


def embed_query(text):
    return embed_texts([text])[0] if text else []
