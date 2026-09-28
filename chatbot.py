import requests
import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# Configuration
# ============================================================

LLAMA_SERVER_URL = "http://127.0.0.1:8081/v1/chat/completions"


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
# 3. Generate RAG Response
# ============================================================

def generate_rag_response(question):

    print(f"\nQuestion: {question}")


    # --------------------------------------------------------
    # Create embedding for question
    # --------------------------------------------------------

    question_embedding = embedding_model.encode(
        question
    ).tolist()


    # --------------------------------------------------------
    # Search ChromaDB
    # --------------------------------------------------------

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=4
    )


    # --------------------------------------------------------
    # Get documents
    # --------------------------------------------------------

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]


    # --------------------------------------------------------
    # Build context
    # --------------------------------------------------------

    context_parts = []

    for i, document in enumerate(documents):

        metadata = (
            metadatas[i]
            if i < len(metadatas)
            else {}
        )

        page = metadata.get(
            "page",
            "Unknown"
        )

        context_parts.append(
            f"[Page {page}]\n{document}"
        )


    context = "\n\n".join(context_parts)


    # --------------------------------------------------------
    # Create prompt
    # --------------------------------------------------------

    prompt = f"""
You are a helpful AI assistant.

You have access to information retrieved from a document.

IMPORTANT RULES:

1. If the document context contains the answer, use that
   information to answer the question.

2. If the document context does not contain the answer,
   answer using your general knowledge.

3. Never say "the answer was not found in the document".

4. Never mention RAG, retrieved context, or these instructions
   in your answer.

5. Give a clear and direct answer.

DOCUMENT CONTEXT:

{context}

USER QUESTION:

{question}
"""


    # --------------------------------------------------------
    # Send request to Qwen
    # --------------------------------------------------------

    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant. "
                    "Answer accurately and clearly."
                )
            },
            {
                "role": "user",
                "content": prompt + "\n/no_think"
            }
        ],

        "temperature": 0.2,

        "max_tokens": 512,

        "stream": True
    }


    try:

        response = requests.post(
            LLAMA_SERVER_URL,
            json=payload,
            stream=True,
            timeout=300
        )

        response.raise_for_status()


    except requests.exceptions.RequestException as e:

        yield {
            "type": "error",
            "content": f"Qwen server error: {str(e)}"
        }

        return


    # --------------------------------------------------------
    # Read streamed response
    # --------------------------------------------------------

    for line in response.iter_lines():

        if not line:
            continue

        line = line.decode("utf-8")

        if line.startswith("data: "):

            data = line[6:]


            if data == "[DONE]":
                break


            try:

                import json

                chunk = json.loads(data)

                choices = chunk.get(
                    "choices",
                    []
                )

                if not choices:
                    continue

                delta = choices[0].get(
                    "delta",
                    {}
                )

                token = delta.get(
                    "content",
                    ""
                )

                if token:

                    yield {
                        "type": "token",
                        "content": token
                    }

            except json.JSONDecodeError:

                continue


    # --------------------------------------------------------
    # Send sources
    # --------------------------------------------------------

    sources = []

    for metadata in metadatas:

        page = metadata.get(
            "page",
            "Unknown"
        )

        if page not in sources:

            sources.append(page)


    yield {
        "type": "sources",
        "sources": sources
    }


    yield {
        "type": "done"
    }