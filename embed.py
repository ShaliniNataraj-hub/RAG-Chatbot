from sentence_transformers import SentenceTransformer


# Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


texts = [
    "The SVM hyperplane separates two classes.",
    "The margin is the distance between the decision boundaries.",
    "The weather is sunny today."
]


# Convert text into embeddings
embeddings = model.encode(texts)


print("Number of texts:", len(texts))
print("Embedding shape:", embeddings.shape)


for i, embedding in enumerate(embeddings):
    print("\nText:", texts[i])
    print("First 10 numbers:", embedding[:10])