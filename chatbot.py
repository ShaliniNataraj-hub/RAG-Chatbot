import subprocess
import chromadb

from sentence_transformers import SentenceTransformer


# ============================================================
# Configuration
# ============================================================

MODEL_REPO = "Qwen/Qwen3-4B-GGUF:Q4_K_M"

LLAMA_CLI = "llama-cli"

# Lower ChromaDB distance = more relevant
RELEVANCE_THRESHOLD = 1.0


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
# 3. Check llama-cli
# ============================================================

def check_llama():

    try:

        result = subprocess.run(
            [LLAMA_CLI, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:

            raise RuntimeError(
                "llama-cli is installed but could not be executed."
            )

        print("llama-cli detected:")
        print(result.stdout.strip())

    except FileNotFoundError:

        raise RuntimeError(
            "llama-cli was not found.\n"
            "Install llama.cpp using:\n"
            "winget install llama.cpp\n"
            "Then restart VS Code."
        )


check_llama()


# ============================================================
# 4. Generate Response Using Qwen3
# ============================================================

def generate_qwen_response(prompt):

    # --------------------------------------------------------
    # Force non-thinking mode
    # --------------------------------------------------------

    prompt = "/no_think\n\n" + prompt


    # --------------------------------------------------------
    # llama-cli command
    # --------------------------------------------------------

    command = [
    LLAMA_CLI,
    "-hf", MODEL_REPO,

    "--device", "none",
    "-ngl", "0",

    "-c", "2048",
    "-n", "256",
    "-b", "256",
    "-ub", "128",

    "--reasoning", "off",
    "--temp", "0.7",
    "--top-p", "0.8",
    "--top-k", "20",

    "--jinja",
    "--single-turn",
    "--no-display-prompt",
    "--no-show-timings",

    "-p", prompt
]


    # --------------------------------------------------------
    # Start Qwen
    # --------------------------------------------------------

    process = subprocess.Popen(

        command,

        stdout=subprocess.PIPE,

        stderr=subprocess.PIPE,

        text=True,

        encoding="utf-8",

        errors="replace"
    )


    output_lines = []


    # --------------------------------------------------------
    # Read stdout
    # --------------------------------------------------------

    while True:

        line = process.stdout.readline()

        if line == "" and process.poll() is not None:
            break

        if line:
            output_lines.append(
                line.rstrip()
            )


    # --------------------------------------------------------
    # Read stderr
    # --------------------------------------------------------

    stderr_output = process.stderr.read()

    return_code = process.wait()


    # --------------------------------------------------------
    # Check error
    # --------------------------------------------------------

    if return_code != 0:

        raise RuntimeError(
            "Qwen/llama-cli failed:\n"
            + stderr_output
        )


    # --------------------------------------------------------
    # Combine stdout
    # --------------------------------------------------------

    raw_output = "\n".join(
        output_lines
    ).strip()


    print("\nQwen raw output received.")


    # ========================================================
    # IMPORTANT:
    # Remove the entire prompt/rules section
    # ========================================================

    if "FINAL ANSWER:" in raw_output:

        answer = raw_output.rsplit(
            "FINAL ANSWER:",
            1
        )[1].strip()

    else:

        answer = raw_output


    # ========================================================
    # Remove <think>...</think>
    # ========================================================

    if "<think>" in answer:

        answer = answer.split(
            "<think>",
            1
        )[1]

        if "</think>" in answer:

            answer = answer.split(
                "</think>",
                1
            )[1]


    # ========================================================
    # Remove explicit thinking markers
    # ========================================================

    if "[Start thinking]" in answer:

        answer = answer.split(
            "[Start thinking]",
            1
        )[-1]


    if "[End thinking]" in answer:

        answer = answer.split(
            "[End thinking]",
            1
        )[0]


    # ========================================================
    # Remove accidental prompt markers
    # ========================================================

    answer = answer.replace(
        "/no_think",
        ""
    )


    # ========================================================
    # Final cleanup
    # ========================================================

    answer = answer.strip()


    return answer


# ============================================================
# 5. Generate RAG Response
# ============================================================

def generate_rag_response(question):

    print("\n" + "=" * 60)
    print("QUESTION:")
    print(question)
    print("=" * 60)


    # ========================================================
    # Create question embedding
    # ========================================================

    question_embedding = embedding_model.encode(
        question
    ).tolist()


    # ========================================================
    # Search ChromaDB
    # ========================================================

    results = collection.query(

        query_embeddings=[
            question_embedding
        ],

        n_results=4,

        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )


    # ========================================================
    # Extract results
    # ========================================================

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]


    # ========================================================
    # Find relevant chunks
    # ========================================================

    relevant_documents = []

    relevant_metadatas = []

    relevant_distances = []


    for i, document in enumerate(documents):

        distance = (

            distances[i]

            if i < len(distances)

            else 999
        )


        metadata = (

            metadatas[i]

            if i < len(metadatas)

            else {}
        )


        print(
            f"Retrieved chunk {i + 1} "
            f"| distance = {distance:.4f}"
        )


        # Lower distance = more relevant
        if distance <= RELEVANCE_THRESHOLD:

            relevant_documents.append(
                document
            )

            relevant_metadatas.append(
                metadata
            )

            relevant_distances.append(
                distance
            )


    # ========================================================
    # RAG mode
    # ========================================================

    if relevant_documents:

        print(
            "\nRAG MODE: Relevant document information found."
        )

        context_parts = []


        for i, document in enumerate(
            relevant_documents
        ):

            metadata = (

                relevant_metadatas[i]

                if i < len(relevant_metadatas)

                else {}
            )


            page = metadata.get(
                "page",
                "Unknown"
            )


            context_parts.append(
                f"[Page {page}]\n{document}"
            )


        context = "\n\n".join(
            context_parts
        )

        using_rag = True


    # ========================================================
    # General knowledge mode
    # ========================================================

    else:

        print(
            "\nGENERAL KNOWLEDGE MODE:"
        )

        print(
            "No sufficiently relevant document "
            "information found."
        )


        context = ""

        using_rag = False


    # ========================================================
    # Build prompt
    # ========================================================

    if using_rag:

        prompt = f"""
You are a helpful AI assistant.

The user asked:

{question}

Relevant information from the document:

{context}

Instructions:

Use the document information when it answers the question.

If the document information does not completely answer the
question, use your general knowledge to complete the answer.

Answer the user's actual question directly.

Do not mention the document retrieval process.

Do not mention embeddings.

Do not mention vector databases.

Do not mention RAG.

Do not explain these instructions.

Do not show reasoning.

Give only the final answer.

FINAL ANSWER:
"""


    else:

        prompt = f"""
You are a helpful general-purpose AI assistant.

The user asked:

{question}

The document does not contain sufficiently relevant information
for this question.

Answer the question using your general knowledge.

Answer the user's actual question directly.

Do not discuss the document.

Do not mention document retrieval.

Do not mention RAG.

Do not mention embeddings.

Do not mention vector databases.

Do not explain these instructions.

Do not show reasoning.

Give only the final answer.

FINAL ANSWER:
"""


    # ========================================================
    # Generate Qwen response
    # ========================================================

    try:

        answer = generate_qwen_response(
            prompt
        )


    except Exception as e:

        print(
            "\nQwen Error:",
            str(e)
        )


        yield {
            "type": "error",
            "message": str(e)
        }

        return


    # ========================================================
    # Send ONLY final answer
    # ========================================================

    if answer:

        yield {
            "type": "token",
            "content": answer
        }


    # ========================================================
    # Sources
    # ========================================================

    sources = []


    if using_rag:

        for metadata in relevant_metadatas:

            page = metadata.get(
                "page",
                "Unknown"
            )


            if page not in sources:

                sources.append(
                    page
                )


    yield {
        "type": "sources",
        "sources": sources
    }


    # ========================================================
    # Done
    # ========================================================

    yield {
        "type": "done"
    }