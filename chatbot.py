import chromadb

from sentence_transformers import SentenceTransformer

from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM
)


# ============================================================
# 1. Load Embedding Model
# ============================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Embedding model loaded.")


# ============================================================
# 2. Connect to ChromaDB
# ============================================================

print("Connecting to ChromaDB...")

chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = chroma_client.get_collection(
    name="documents"
)

print("ChromaDB connected.")


# ============================================================
# 3. Load FLAN-T5-Large
# ============================================================

print("Loading FLAN-T5-Large...")

MODEL_NAME = "google/flan-t5-large"


tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)


model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME
)


# CPU only

model = model.to("cpu")

model.eval()


print("FLAN-T5-Large loaded on CPU.")


# ============================================================
# 4. RAG Function
# ============================================================

def generate_rag_response(question):

    # --------------------------------------------------------
    # Create question embedding
    # --------------------------------------------------------

    print("\nSearching documents...")

    question_embedding = embedding_model.encode(
        [question]
    )


    # --------------------------------------------------------
    # Retrieve relevant chunks
    # --------------------------------------------------------

    results = collection.query(
        query_embeddings=question_embedding.tolist(),
        n_results=2
    )


    # --------------------------------------------------------
    # Build context
    # --------------------------------------------------------

    context_parts = []


    for i in range(
        len(results["documents"][0])
    ):

        document = results["documents"][0][i]

        metadata = results["metadatas"][0][i]

        source = metadata["source"]

        page = metadata["page"]


        context_parts.append(
            f"""
SOURCE: {source}
PAGE: {page}

{document}
"""
        )


    context = "\n\n".join(
        context_parts
    )


    # --------------------------------------------------------
    # Send status to frontend
    # --------------------------------------------------------

    yield {
        "type": "status",
        "message": "Generating answer with FLAN-T5-Large..."
    }


    # --------------------------------------------------------
    # Create RAG prompt
    # --------------------------------------------------------

    prompt = f"""
Answer the question using only the context provided below.

If the answer cannot be found in the context,
say that the information was not found in the provided documents.

Context:

{context}

Question:

{question}

Answer:
"""


    # --------------------------------------------------------
    # Tokenize
    # --------------------------------------------------------

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=2048
    )


    # --------------------------------------------------------
    # Generate Answer
    # --------------------------------------------------------

    print(
        "Generating answer using FLAN-T5-Large..."
    )


    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        num_beams=2,
        early_stopping=True
    )


    # --------------------------------------------------------
    # Decode
    # --------------------------------------------------------

    answer = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )


    # --------------------------------------------------------
    # Send answer
    # --------------------------------------------------------

    yield {
        "type": "token",
        "content": answer
    }


    # --------------------------------------------------------
    # Sources
    # --------------------------------------------------------

    sources = []


    for metadata in results["metadatas"][0]:

        sources.append({
            "source": metadata["source"],
            "page": metadata["page"]
        })


    yield {
        "type": "sources",
        "sources": sources
    }


    # --------------------------------------------------------
    # Finished
    # --------------------------------------------------------

    yield {
        "type": "done"
    }