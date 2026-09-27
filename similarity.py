from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


model = SentenceTransformer("all-MiniLM-L6-v2")


texts = [
    "The SVM hyperplane separates two classes.",
    "The margin is the distance between the decision boundaries.",
    "The weather is sunny today."
]


question = "How is the SVM margin calculated?"


# Create embeddings
text_embeddings = model.encode(texts)
question_embedding = model.encode([question])


# Calculate cosine similarity
similarities = cosine_similarity(
    question_embedding,
    text_embeddings
)[0]


print("\nQuestion:")
print(question)

print("\nSimilarity scores:")

for text, score in zip(texts, similarities):
    print(f"{score:.4f}  →  {text}")