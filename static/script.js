const questionInput = document.getElementById("question");
const chatContainer = document.getElementById("chatContainer");
const sendButton = document.getElementById("sendButton");


// ============================================================
// Send Question
// ============================================================

async function sendQuestion() {

    const question = questionInput.value.trim();

    if (!question) {
        return;
    }


    // Remove welcome screen

    const welcome = document.getElementById("welcome");

    if (welcome) {
        welcome.remove();
    }


    // Add user message

    addUserMessage(question);


    // Clear input

    questionInput.value = "";

    sendButton.disabled = true;


    // Create bot message

    const botMessage = createStreamingBotMessage();


    try {

        const response = await fetch("/ask", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: question
            })

        });


        if (!response.ok) {

            throw new Error(
                "Server returned " + response.status
            );

        }


        // ----------------------------------------------------
        // Read streaming response
        // ----------------------------------------------------

        const reader = response.body.getReader();

        const decoder = new TextDecoder();

        let buffer = "";


        while (true) {

            const { value, done } =
                await reader.read();


            if (done) {
                break;
            }


            buffer += decoder.decode(
                value,
                { stream: true }
            );


            const lines =
                buffer.split("\n");


            buffer =
                lines.pop();


            for (const line of lines) {

                if (!line.trim()) {
                    continue;
                }


                const data =
                    JSON.parse(line);


                // --------------------------------------------
                // Status
                // --------------------------------------------

                if (data.type === "status") {

                    botMessage.content.innerHTML =
                        escapeHtml(data.message);

                }


                // --------------------------------------------
                // Token
                // --------------------------------------------

                else if (data.type === "token") {

                    botMessage.answer +=
                        data.content;

                    botMessage.content.innerHTML =
                        formatAnswer(
                            botMessage.answer
                        );

                    scrollToBottom();
                }


                // --------------------------------------------
                // Sources
                // --------------------------------------------

                else if (data.type === "sources") {

                    displaySources(
                        botMessage.container,
                        data.sources
                    );

                }


                // --------------------------------------------
                // Error
                // --------------------------------------------

                else if (data.type === "error") {

                    botMessage.content.innerHTML =
                        "Error: " +
                        escapeHtml(data.message);

                }

            }

        }


    } catch (error) {

        botMessage.content.innerHTML =
            "Could not connect to the RAG server.<br><br>" +
            escapeHtml(error.message);

        console.error(error);

    }


    sendButton.disabled = false;

    questionInput.focus();
}



// ============================================================
// Create Bot Message
// ============================================================

function createStreamingBotMessage() {

    const message =
        document.createElement("div");

    message.className =
        "message bot-message";


    message.innerHTML = `

        <div class="bot-icon">
            R
        </div>

        <div class="bot-content">

            <div class="answer-content">
                Searching documents...
            </div>

        </div>

    `;


    chatContainer.appendChild(message);

    scrollToBottom();


    return {

        container: message,

        content:
            message.querySelector(
                ".answer-content"
            ),

        answer: ""

    };
}



// ============================================================
// Display Sources
// ============================================================

function displaySources(
    container,
    sources
) {

    if (
        !sources ||
        sources.length === 0
    ) {
        return;
    }


    const sourcesDiv =
        document.createElement("div");

    sourcesDiv.className =
        "sources";


    sourcesDiv.innerHTML = `

        <div class="sources-title">
            Sources
        </div>

        ${sources.map(source => `

            <div class="source-item">

                ${escapeHtml(source.source)}
                — Page ${source.page}

            </div>

        `).join("")}

    `;


    container
        .querySelector(".bot-content")
        .appendChild(sourcesDiv);


    scrollToBottom();
}



// ============================================================
// User Message
// ============================================================

function addUserMessage(text) {

    const message =
        document.createElement("div");

    message.className =
        "message user-message";


    message.innerHTML = `

        <div class="user-bubble">
            ${escapeHtml(text)}
        </div>

    `;


    chatContainer.appendChild(message);

    scrollToBottom();
}



// ============================================================
// Suggestion
// ============================================================

function askSuggestion(button) {

    questionInput.value =
        button.textContent.trim();

    sendQuestion();
}



// ============================================================
// New Chat
// ============================================================

function newChat() {

    chatContainer.innerHTML = `

        <div class="welcome" id="welcome">

            <div class="welcome-icon">
                R
            </div>

            <h2>
                How can I help you?
            </h2>

            <p>
                Ask a question about your uploaded documents.
            </p>

        </div>

    `;
}



// ============================================================
// Enter Key
// ============================================================

questionInput.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendQuestion();

        }

    }
);



// ============================================================
// Format Answer
// ============================================================

function formatAnswer(text) {

    return escapeHtml(text)
        .replace(
            /\n/g,
            "<br>"
        )
        .replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );

}



// ============================================================
// Escape HTML
// ============================================================

function escapeHtml(text) {

    const div =
        document.createElement("div");

    div.textContent = text;

    return div.innerHTML;

}



// ============================================================
// Scroll
// ============================================================

function scrollToBottom() {

    chatContainer.scrollTop =
        chatContainer.scrollHeight;

}