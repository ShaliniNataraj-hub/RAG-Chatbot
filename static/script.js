const questionInput = document.getElementById("question");
const chatContainer = document.getElementById("chatContainer");
const sendButton = document.getElementById("sendButton");
const hub = document.getElementById("intelligenceHub");
const hubStateLabel = document.getElementById("hubStateLabel");
const knowledgePanel = document.getElementById("knowledgePanel");
const knowledgeBody = document.getElementById("knowledgeBody");
const knowledgeEmpty = document.getElementById("knowledgeEmpty");
const sourceCountEl = document.getElementById("sourceCount");
const panelToggle = document.getElementById("panelToggle");

let sourceCounter = 0;

// ============================================================
// Hub state
// ============================================================

function setHubState(state, label) {
    hub.dataset.state = state;
    hubStateLabel.textContent = label;
}

// ============================================================
// Send Question
// ============================================================

async function sendQuestion() {

    const question = questionInput.value.trim();
    if (!question) return;

    const welcome = document.getElementById("welcome");
    if (welcome) welcome.remove();

    addUserMessage(question);

    questionInput.value = "";
    questionInput.style.height = "auto";
    sendButton.disabled = true;

    const botMessage = createStreamingBotMessage();
    setHubState("searching", "Searching database…");
    botMessage.setLoadingLabel("Searching documents…");

    try {

        const response = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: question })
        });

        if (!response.ok) {
            throw new Error("Server returned " + response.status);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let tokensStarted = false;

        while (true) {

            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {

                if (!line.trim()) continue;
                const data = JSON.parse(line);

                if (data.type === "status") {
                    botMessage.setLoadingLabel(data.message);
                }

                else if (data.type === "token") {
                    if (!tokensStarted) {
                        tokensStarted = true;
                        botMessage.hideLoading();
                        setHubState("synthesizing", "Synthesizing response…");
                    }
                    botMessage.answer += data.content;
                    botMessage.content.innerHTML = formatAnswer(botMessage.answer);
                    scrollToBottom();
                }

                else if (data.type === "sources") {
                    renderCitations(botMessage, data.sources);
                }

                else if (data.type === "error") {
                    botMessage.hideLoading();
                    botMessage.content.innerHTML = "Error: " + escapeHtml(data.message);
                }

            }

        }

    } catch (error) {
        botMessage.hideLoading();
        botMessage.content.innerHTML =
            "Could not connect to the RAG server.<br><br>" + escapeHtml(error.message);
        console.error(error);
    }

    setHubState("idle", "Ask anything");
    sendButton.disabled = false;
    questionInput.focus();
}

// ============================================================
// Create Bot Message
// ============================================================

function createStreamingBotMessage() {

    const message = document.createElement("div");
    message.className = "message bot-message";

    message.innerHTML = `
        <div class="bot-block">
            <div class="thinking">
                <div class="thinking-dots"><span></span><span></span><span></span></div>
                <div class="thinking-label">Searching documents…</div>
            </div>
            <div class="answer-content"></div>
        </div>
    `;

    chatContainer.appendChild(message);
    scrollToBottom();

    const thinkingEl = message.querySelector(".thinking");
    const labelEl = message.querySelector(".thinking-label");
    const contentEl = message.querySelector(".answer-content");

    return {
        container: message,
        content: contentEl,
        answer: "",

        setLoadingLabel(text) {
            if (labelEl) labelEl.textContent = text;
        },

        hideLoading() {
            if (!thinkingEl || thinkingEl.dataset.hidden) return;
            thinkingEl.dataset.hidden = "true";
            thinkingEl.classList.add("leaving");
            contentEl.classList.add("visible");
            setTimeout(() => thinkingEl.remove(), 250);
        }
    };
}

// ============================================================
// Citations: pills in the message + cards in the Knowledge Panel
// ============================================================

function renderCitations(botMessage, sources) {

    if (!sources || sources.length === 0) return;

    // Clear the empty state once real evidence arrives
    if (knowledgeEmpty) knowledgeEmpty.remove();

    const block = botMessage.container.querySelector(".bot-block");
    const row = document.createElement("div");
    row.className = "citation-row";

    sources.forEach(source => {

        sourceCounter += 1;
        const cardId = "source-card-" + sourceCounter;

        // Pill inside the chat message
        const pill = document.createElement("span");
        pill.className = "citation-pill";
        pill.textContent = escapeHtml(source.source) + " · p" + source.page;
        pill.onclick = () => focusSourceCard(cardId);
        row.appendChild(pill);

        // Card inside the Knowledge Panel
        const card = document.createElement("div");
        card.className = "source-card";
        card.id = cardId;
        card.innerHTML = `
            <div class="source-card-head">
                <span class="source-name">${escapeHtml(source.source)}</span>
                <span class="source-page">p${source.page}</span>
            </div>
        `;
        knowledgeBody.appendChild(card);
    });

    block.appendChild(row);
    sourceCountEl.textContent = sourceCounter;
    scrollToBottom();
}

function focusSourceCard(cardId) {

    if (window.innerWidth <= 900) openKnowledgePanel();

    const card = document.getElementById(cardId);
    if (!card) return;

    document.querySelectorAll(".source-card.highlight")
        .forEach(el => el.classList.remove("highlight"));

    card.classList.add("highlight");
    card.scrollIntoView({ behavior: "smooth", block: "center" });
}

function toggleKnowledgePanel() {
    knowledgePanel.classList.toggle("open");
}

function openKnowledgePanel() {
    knowledgePanel.classList.add("open");
}

// ============================================================
// User Message
// ============================================================

function addUserMessage(text) {

    const message = document.createElement("div");
    message.className = "message user-message";
    message.innerHTML = `<div class="user-bubble">${escapeHtml(text)}</div>`;
    chatContainer.appendChild(message);
    scrollToBottom();
}

// ============================================================
// Suggestion
// ============================================================

function askSuggestion(button) {
    questionInput.value = button.textContent.trim();
    sendQuestion();
}

// ============================================================
// New Chat
// ============================================================

function newChat() {

    chatContainer.innerHTML = `
        <div class="welcome" id="welcome">
            <h1>What's in your documents?</h1>
            <p>Ask a question and I'll retrieve the exact passages behind every answer.</p>
            <div class="prompts">
                <button class="prompt-chip" onclick="askSuggestion(this)">What is SVM?</button>
                <button class="prompt-chip" onclick="askSuggestion(this)">What is the optimization problem for SVM?</button>
                <button class="prompt-chip" onclick="askSuggestion(this)">Explain the SVM margin.</button>
            </div>
        </div>
    `;

    knowledgeBody.innerHTML = `
        <div class="knowledge-empty" id="knowledgeEmpty">
            <div class="constellation">
                <span></span><span></span><span></span><span></span><span></span>
            </div>
            <p>Source passages will appear here as they're retrieved.</p>
        </div>
    `;

    sourceCounter = 0;
    sourceCountEl.textContent = "0";
    setHubState("idle", "Ask anything");
}

// ============================================================
// Enter key + auto-grow textarea
// ============================================================

questionInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendQuestion();
    }
});

questionInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 140) + "px";
});

// ============================================================
// Format Answer
// ============================================================

function formatAnswer(text) {
    return escapeHtml(text)
        .replace(/\n/g, "<br>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
}

// ============================================================
// Escape HTML
// ============================================================

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================
// Scroll
// ============================================================

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}