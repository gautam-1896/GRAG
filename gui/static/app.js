// ── Global State ──────────────────────────────────────────────────────────────
let currentSources = [];       // stores source arrays per-message for the drawer
let rebuildCheckInterval = null;

// ── DOM Elements ──────────────────────────────────────────────────────────────
const dbStatusDot             = document.getElementById("db-status-dot");
const dbStatusText            = document.getElementById("db-status-text");
const chunkCountEl            = document.getElementById("chunk-count");
const documentListEl          = document.getElementById("document-list");
const rebuildBtn              = document.getElementById("rebuild-btn");
const rebuildProgressContainer = document.getElementById("rebuild-progress-container");
const rebuildProgressMsg      = document.getElementById("rebuild-progress-msg");
const chatForm                = document.getElementById("chat-form");
const queryInput              = document.getElementById("query-input");
const chatMessages            = document.getElementById("chat-messages");
const clearChatBtn            = document.getElementById("clear-chat-btn");
const sourceDrawer            = document.getElementById("source-drawer");
const drawerContent           = document.getElementById("drawer-content");
const closeDrawerBtn          = document.getElementById("close-drawer-btn");

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    fetchSystemStatus();
    setupEventListeners();
});

// ── Event Listeners ───────────────────────────────────────────────────────────
function setupEventListeners() {
    // Form: submit query
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const q = queryInput.value.trim();
        if (q) submitQuery(q);
    });

    // Clear chat
    clearChatBtn.addEventListener("click", () => {
        chatMessages.innerHTML = `
            <div class="message system-msg">
                <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
                <div class="msg-bubble">
                    <p>Chat cleared. Ask me anything about your indexed documents!</p>
                </div>
            </div>
        `;
        // Hide drawer with animation
        sourceDrawer.classList.add("slide-hidden");
    });

    // Close drawer
    closeDrawerBtn.addEventListener("click", () => {
        sourceDrawer.classList.add("slide-hidden");
    });

    // Rebuild index
    rebuildBtn.addEventListener("click", triggerIndexRebuild);

    // Suggestion chips — event delegation
    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("suggestion-chip")) {
            submitQuery(e.target.textContent.trim());
        }
    });
}

// ── Status Polling ────────────────────────────────────────────────────────────
async function fetchSystemStatus() {
    try {
        const response = await fetch("/api/status");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        updateUIWithStatus(data);
    } catch (err) {
        console.error("Status fetch error:", err);
        dbStatusDot.className = "status-dot offline";
        dbStatusText.textContent = "Server Disconnected";
    }
}

function updateUIWithStatus(data) {
    // Vector DB indicator
    if (data.index_exists) {
        dbStatusDot.className = "status-dot online";
        dbStatusText.textContent = "Database Loaded";
    } else {
        dbStatusDot.className = "status-dot offline";
        dbStatusText.textContent = "No Index Built";
    }

    chunkCountEl.textContent = data.chunk_count ?? 0;

    // Render document list with correct file-type icons
    documentListEl.innerHTML = "";
    if (data.documents && data.documents.length > 0) {
        data.documents.forEach(docName => {
            const li = document.createElement("li");
            const icon = getFileIcon(docName);
            li.innerHTML = `${icon} ${escapeHtml(docName)}`;
            li.title = docName;
            documentListEl.appendChild(li);
        });
    } else {
        documentListEl.innerHTML = '<li class="empty-list-msg">No files indexed yet.</li>';
    }

    // Rebuild progress monitoring
    if (data.rebuild && data.rebuild.status === "building") {
        showRebuildProgress(data.rebuild.message);
        if (!rebuildCheckInterval) {
            rebuildCheckInterval = setInterval(fetchSystemStatus, 2000);
        }
    } else if (rebuildCheckInterval) {
        clearInterval(rebuildCheckInterval);
        rebuildCheckInterval = null;
        hideRebuildProgress();
        if (data.rebuild && data.rebuild.status !== "idle") {
            appendSystemMessage(
                `[System] Index rebuild ${data.rebuild.status}. ${data.rebuild.message}`
            );
        }
    }
}

// ── Query Submission ──────────────────────────────────────────────────────────
async function submitQuery(queryText) {
    if (!queryText) return;

    appendUserMessage(queryText);
    queryInput.value = "";
    scrollToBottom();

    const loaderId = appendTypingLoader();
    scrollToBottom();

    try {
        const response = await fetch("/api/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: queryText,
                top_k: 7,  // Optimized for better context
            }),
        });

        removeTypingLoader(loaderId);

        if (!response.ok) {
            let errMsg = `Server error ${response.status}`;
            try {
                const errData = await response.json();
                errMsg = errData.detail || errMsg;
            } catch (_) {}
            throw new Error(errMsg);
        }

        const data = await response.json();
        appendSystemMessage(data.answer, data.sources);

    } catch (err) {
        removeTypingLoader(loaderId);
        console.error("[GRAG] Query error:", err);

        let userFriendlyMsg = err.message;
        if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
            userFriendlyMsg = (
                "⚠️ Cannot reach the GRAG server.\n" +
                "Make sure the server is running:\n" +
                "  python main.py --gui\n" +
                "Then refresh this page."
            );
        }
        appendSystemMessage(userFriendlyMsg);
    }

    scrollToBottom();
}

// ── Rebuild ───────────────────────────────────────────────────────────────────
async function triggerIndexRebuild() {
    try {
        rebuildBtn.disabled = true;
        const res = await fetch("/api/rebuild", { method: "POST" });
        if (!res.ok) throw new Error("Rebuild request failed");

        showRebuildProgress("Starting background rebuild…");

        if (rebuildCheckInterval) clearInterval(rebuildCheckInterval);
        rebuildCheckInterval = setInterval(fetchSystemStatus, 2000);

    } catch (err) {
        console.error("[GRAG] Rebuild error:", err);
        rebuildBtn.disabled = false;
        appendSystemMessage(`⚠️ Failed to start index rebuild: ${err.message}`);
    }
}

// ── UI Helpers ─────────────────────────────────────────────────────────────────
function showRebuildProgress(msg) {
    rebuildProgressContainer.classList.remove("hidden");
    rebuildProgressMsg.textContent = msg;
    rebuildBtn.disabled = true;
    dbStatusDot.className = "status-dot loading";
    dbStatusText.textContent = "Rebuilding…";
}

function hideRebuildProgress() {
    rebuildProgressContainer.classList.add("hidden");
    rebuildBtn.disabled = false;
}

function appendUserMessage(text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message user-msg";
    msgDiv.innerHTML = `
        <div class="msg-avatar"><i class="fa-solid fa-user"></i></div>
        <div class="msg-bubble">
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    chatMessages.appendChild(msgDiv);
}

function appendSystemMessage(text, sources = []) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message system-msg";

    let sourceBtnHtml = "";
    if (sources && sources.length > 0) {
        const sourceIndex = currentSources.length;
        currentSources.push(sources);
        sourceBtnHtml = `
            <button class="source-btn-inline" onclick="showSources(${sourceIndex})">
                <i class="fa-solid fa-eye"></i> View Sources (${sources.length})
            </button>
        `;
    }

    // Convert newlines to <br> after escaping
    const formattedText = escapeHtml(text).replace(/\n/g, "<br>");

    msgDiv.innerHTML = `
        <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="msg-bubble">
            <p>${formattedText}</p>
            ${sourceBtnHtml}
        </div>
    `;
    chatMessages.appendChild(msgDiv);
}

function appendTypingLoader() {
    const loaderId = "loader-" + Date.now();
    const msgDiv = document.createElement("div");
    msgDiv.className = "message system-msg typing-loader";
    msgDiv.id = loaderId;
    msgDiv.innerHTML = `
        <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="msg-bubble">
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    chatMessages.appendChild(msgDiv);
    return loaderId;
}

function removeTypingLoader(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ── Source Drawer ─────────────────────────────────────────────────────────────
window.showSources = function (index) {
    const sources = currentSources[index];
    if (!sources || sources.length === 0) return;

    drawerContent.innerHTML = "";

    sources.forEach((src, i) => {
        const card = document.createElement("div");
        card.className = "source-card";
        card.innerHTML = `
            <div class="source-meta-bar">
                <span class="source-filename" title="${escapeHtml(src.source)}">
                    ${getFileIcon(src.source)} ${escapeHtml(src.source)}
                </span>
                <span class="source-distance">Dist: ${src.distance.toFixed(4)}</span>
            </div>
            <div class="source-text-chunk">${escapeHtml(src.text)}</div>
        `;
        drawerContent.appendChild(card);
    });

    sourceDrawer.classList.remove("slide-hidden");
};

// ── Utility Functions ─────────────────────────────────────────────────────────
/**
 * Returns an <i> FontAwesome icon element string with the correct colour class
 * based on the file extension.
 */
function getFileIcon(filename) {
    if (!filename) return `<i class="fa-solid fa-file icon-file"></i>`;
    const ext = filename.split(".").pop().toLowerCase();
    const map = {
        pdf:  `<i class="fa-solid fa-file-pdf icon-pdf"></i>`,
        txt:  `<i class="fa-solid fa-file-lines icon-txt"></i>`,
        csv:  `<i class="fa-solid fa-file-csv icon-csv"></i>`,
        docx: `<i class="fa-solid fa-file-word icon-docx"></i>`,
        doc:  `<i class="fa-solid fa-file-word icon-docx"></i>`,
        json: `<i class="fa-solid fa-file-code icon-json"></i>`,
        xlsx: `<i class="fa-solid fa-file-excel icon-csv"></i>`,
    };
    return map[ext] || `<i class="fa-solid fa-file icon-file"></i>`;
}

function escapeHtml(text) {
    if (typeof text !== "string") text = String(text ?? "");
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
