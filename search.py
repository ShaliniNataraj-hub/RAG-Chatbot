import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# Load embedding model
# ============================================================

model = SentenceTransformer("all-MiniLM-L6-v2")


# ============================================================
# Connect to ChromaDB
# ============================================================

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_collection(
    name="documents"
)


# ============================================================
# Ask question
# ============================================================

question = input("\nAsk a question: ")


# ============================================================
# Convert question to embedding
# ============================================================

question_embedding = model.encode(
    [question]
)


# ============================================================
# Search database
# ============================================================

results = collection.query(
    query_embeddings=question_embedding.tolist(),
    n_results=3
)


# ============================================================
# Display results
# ============================================================

print("\n" + "=" * 70)
print("RETRIEVED RESULTS")
print("=" * 70)


for i in range(len(results["documents"][0])):

    document = results["documents"][0][i]
    distance = results["distances"][0][i]
    metadata = results["metadatas"][0][i]

    print(f"\n--- Result {i + 1} ---")

    print(f"Distance : {distance:.4f}")

    print(
        f"Source   : {metadata['source']}"
    )

    print(
        f"Page     : {metadata['page']}"
    )

    print(
        f"Chunk    : {metadata['chunk']}"
    )

    print("\nText:")

    print(document)