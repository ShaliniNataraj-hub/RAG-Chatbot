from flask import Flask, render_template, request, Response
import json

from chatbot import generate_rag_response


app = Flask(__name__)


# ============================================================
# Home Page
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# Streaming Chat API
# ============================================================

@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json()

    question = data.get("question", "").strip()

    if not question:
        return Response(
            "Please enter a question.",
            status=400
        )


    def generate():

        try:

            for item in generate_rag_response(question):

                yield json.dumps(item) + "\n"


        except Exception as e:

            print("ERROR:", e)

            yield json.dumps({
                "type": "error",
                "message": str(e)
            }) + "\n"


    return Response(
        generate(),
        mimetype="application/x-ndjson"
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        threaded=True
    )