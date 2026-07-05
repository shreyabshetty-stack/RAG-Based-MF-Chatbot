/* ── app.js — FundBot Frontend Application Logic ─────────────────────
   Connects the chat UI to POST /api/chat.
   Handles: local storage chat history, previous session reload, delete chats,
            example query chips directly above input, send/receive,
            typing indicators, advisory vs factual rendering, rate-limit toast,
            PII badge display, copy-to-clipboard, clear/new chat.
 ──────────────────────────────────────────────────────────────────────── */

const API_CHAT    = "/api/chat";
const API_HEALTH  = "/api/health";

// Quick example queries (as specified in implementation.md Task 6.2)
const EXAMPLES = [
  { icon: "percent",         text: "What is the exit load of HDFC Mid-Cap?" },
  { icon: "leaderboard",     text: "What is the benchmark of HDFC Large Cap?" },
  { icon: "block",           text: "Can you tell me if I should invest in HDFC Flexi Cap?" },
];

const STORAGE_KEY = "fundbot_chats";

// State
let chatSessions = [];          // Array of { id, title, timestamp, messages: [] }
let activeSessionId = null;
let isLoading    = false;
let typingCounter = 0;

/* ── DOM refs ─────────────────────────────────────────────────────── */
const canvas       = document.getElementById("chat-canvas");
const chatInput    = document.getElementById("chat-input");
const welcomeState = document.getElementById("welcome-state");
const btnSend      = document.getElementById("btn-send");
const toastEl      = document.getElementById("toast-rate-limit");
const sidebarTs    = document.getElementById("sidebar-ts");
const dateLabel    = document.getElementById("date-label");

/* ── Init ─────────────────────────────────────────────────────────── */
(function init() {
  const now = new Date();
  const dateStr = now.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  const timeStr = now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  sidebarTs.textContent = `LAST UPDATED: ${dateStr.toUpperCase()}, ${timeStr}`;
  dateLabel.textContent = "Today";

  loadChats();
  renderChatHistory();
  buildExampleChips();
  buildExamples();
  checkHealth();
})();

/* ── Health check ─────────────────────────────────────────────────── */
async function checkHealth() {
  try {
    const res = await fetch(API_HEALTH);
    const data = await res.json();
    const badge = document.getElementById("status-badge");
    if (badge) {
      if (data.status !== "healthy") {
        const dot = badge.querySelector(".status-dot");
        badge.textContent = " Status: Degraded";
        if (dot) badge.prepend(dot);
        badge.style.color = "var(--amber)";
        badge.style.background = "rgba(229,168,75,0.08)";
        badge.style.borderColor = "rgba(229,168,75,0.25)";
      }
    }
  } catch (_) { /* health endpoint unavailable — no-op */ }
}

/* ── Local Storage Chat Sessions ──────────────────────────────────── */
function loadChats() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    chatSessions = raw ? JSON.parse(raw) : [];
  } catch (e) {
    chatSessions = [];
  }
}

function saveChats() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(chatSessions));
  } catch (e) {}
}

function renderChatHistory() {
  const container = document.getElementById("chat-history-list");
  if (!container) return;
  container.innerHTML = "";

  if (chatSessions.length === 0) {
    container.innerHTML = `<div style="font-size:11px; color:var(--text-dim); padding:12px 8px; text-align:center; font-style:italic;">No previous chats</div>`;
    return;
  }

  chatSessions.forEach(session => {
    const item = document.createElement("div");
    item.className = "history-item" + (session.id === activeSessionId ? " active" : "");
    item.dataset.id = session.id;

    item.addEventListener("click", (e) => {
      if (e.target.classList.contains("history-delete") || e.target.closest(".history-delete")) {
        return;
      }
      loadChatSession(session.id);
    });

    const titleEl = document.createElement("span");
    titleEl.className = "history-title";
    titleEl.innerHTML = `<span class="material-symbols-outlined" style="font-size:16px;">forum</span> ${escHtml(session.title)}`;
    item.appendChild(titleEl);

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "history-delete";
    deleteBtn.title = "Delete Chat";
    deleteBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size:16px;">close</span>`;
    deleteBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      deleteChatSession(session.id);
    });
    item.appendChild(deleteBtn);

    container.appendChild(item);
  });
}

function ensureActiveSession(firstMessageText) {
  if (!activeSessionId) {
    activeSessionId = "session_" + Date.now();
    const title = firstMessageText.length > 28 ? firstMessageText.substring(0, 28) + "..." : firstMessageText;
    const newSession = {
      id: activeSessionId,
      title: title,
      timestamp: Date.now(),
      messages: []
    };
    chatSessions.unshift(newSession);
    saveChats();
    renderChatHistory();
  }
}

function loadChatSession(sessionId) {
  activeSessionId = sessionId;
  canvas.querySelectorAll(".msg-row, .typing-wrap").forEach(el => el.remove());

  const session = chatSessions.find(s => s.id === sessionId);
  if (!session) {
    startNewChat();
    return;
  }

  if (welcomeState) welcomeState.style.display = "none";
  canvas.classList.add("has-messages");

  session.messages.forEach(msg => {
    if (msg.type === "user") {
      appendUserBubble(msg.text, false);
    } else if (msg.type === "bot") {
      appendBotBubble(msg.data, false);
    } else if (msg.type === "advisory") {
      appendAdvisoryBubble(msg.text, msg.sourceUrl, false);
    } else if (msg.type === "error") {
      appendErrorBubble(msg.text, false);
    }
  });

  updateHistoryActiveState();
  canvas.scrollTop = canvas.scrollHeight;
}

function deleteChatSession(id) {
  chatSessions = chatSessions.filter(s => s.id !== id);
  saveChats();
  renderChatHistory();

  if (activeSessionId === id) {
    startNewChat();
  }
}

function updateHistoryActiveState() {
  document.querySelectorAll(".history-item").forEach(el => {
    el.classList.toggle("active", el.dataset.id === activeSessionId);
  });
}

function startNewChat() {
  activeSessionId = null;
  canvas.querySelectorAll(".msg-row, .typing-wrap").forEach(el => el.remove());
  canvas.classList.remove("has-messages");
  if (welcomeState) welcomeState.style.display = "flex";
  updateHistoryActiveState();
}

function clearChat() {
  startNewChat();
}

/* ── Build example chips above input box ──────────────────────────── */
function buildExampleChips() {
  const container = document.getElementById("example-chips");
  if (!container) return;
  container.innerHTML = "";

  EXAMPLES.forEach(ex => {
    const chip = document.createElement("span");
    chip.className = "example-chip";
    chip.innerHTML = `<span class="material-symbols-outlined">${ex.icon}</span>${escHtml(ex.text)}`;
    chip.addEventListener("click", () => fillAndSend(ex.text));
    container.appendChild(chip);
  });
}

/* ── Build welcome-state example query buttons ────────────────────── */
function buildExamples() {
  const container = document.getElementById("quick-examples-list");
  if (!container) return;
  container.innerHTML = "";
  EXAMPLES.forEach(ex => {
    const btn = document.createElement("button");
    btn.className = "quick-example-btn";
    btn.innerHTML = `<span class="material-symbols-outlined">${ex.icon}</span>${escHtml(ex.text)}`;
    btn.addEventListener("click", () => fillAndSend(ex.text));
    container.appendChild(btn);
  });
}

/* Fill input and auto-send */
function fillAndSend(text) {
  chatInput.value = text;
  sendMessage();
}

/* Fill from sidebar example-q clicks */
function fillQuery(el) {
  chatInput.value = el.textContent.replace(/^"|"$/g, "");
  chatInput.focus();
}

/* ── Send / receive ──────────────────────────────────────────────── */
chatInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
btnSend.addEventListener("click", sendMessage);

async function sendMessage() {
  const query = chatInput.value.trim();
  if (!query || isLoading) return;
  isLoading = true;
  chatInput.value = "";

  // Hide welcome state on first message
  if (welcomeState) welcomeState.style.display = "none";
  canvas.classList.add("has-messages");

  appendUserBubble(query);

  const typingId = appendTyping();
  canvas.scrollTop = canvas.scrollHeight;

  try {
    const res = await fetch(API_CHAT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: query, fund_filter: null }),
    });

    removeTyping(typingId);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      appendErrorBubble(err.detail || `Server error (${res.status}). Please try again.`);
    } else {
      const data = await res.json();
      if (data.intent === "ADVISORY") {
        appendAdvisoryBubble(data.answer, data.source_url);
      } else if (data.intent === "ERROR") {
        showToast();
        appendErrorBubble(data.answer);
      } else {
        appendBotBubble(data);
      }
    }
  } catch (err) {
    removeTyping(typingId);
    showToast();
    appendErrorBubble("Could not reach the FundBot server. Make sure it is running on port 8000.");
  } finally {
    isLoading = false;
    canvas.scrollTop = canvas.scrollHeight;
  }
}

/* ── DOM builders ────────────────────────────────────────────────── */
function appendUserBubble(text, save = true) {
  const row = document.createElement("div");
  row.className = "msg-row user-row";
  row.innerHTML = `<div class="user-bubble">${escHtml(text)}</div>`;
  canvas.appendChild(row);

  if (save) {
    ensureActiveSession(text);
    const session = chatSessions.find(s => s.id === activeSessionId);
    if (session) {
      session.messages.push({ type: "user", text });
      saveChats();
    }
  }
}

function appendTyping() {
  const id = "typing-" + (++typingCounter);
  const el = document.createElement("div");
  el.className = "typing-wrap";
  el.id = id;
  el.innerHTML = `
    <div class="bot-avatar">
      <span class="material-symbols-outlined icon-filled" style="font-size:18px;">auto_awesome</span>
    </div>
    <div class="typing-bubble">
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    </div>`;
  canvas.appendChild(el);
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function appendBotBubble(data, save = true) {
  const { answer, source_url, updated_date, pii_detected, validation_warnings } = data;
  const shortUrl = source_url
    ? source_url.replace("https://groww.in/mutual-funds/", "groww.in/…/")
    : null;

  const piiHtml = pii_detected
    ? `<span class="pii-badge"><span class="material-symbols-outlined" style="font-size:11px;">shield</span>PII Redacted</span>`
    : "";

  const warningsHtml = validation_warnings && validation_warnings.length
    ? `<div class="bot-note">Note: ${escHtml(validation_warnings.join(" | "))}</div>`
    : "";

  const sourceHtml = source_url
    ? `<div class="sources-section">
        <div class="sources-label">Sources</div>
        <div class="source-chips">
          <a class="source-chip" href="${escHtml(source_url)}" target="_blank" rel="noopener">
            <span class="material-symbols-outlined">link</span>
            ${escHtml(shortUrl)}
            <span class="material-symbols-outlined ext-icon">open_in_new</span>
          </a>
          <div class="verified-count">
            <span class="material-symbols-outlined icon-filled">verified</span>
            Verified from official source
          </div>
        </div>
      </div>` : "";

  const row = document.createElement("div");
  row.className = "msg-row";
  row.innerHTML = `
    <div class="bot-avatar">
      <span class="material-symbols-outlined icon-filled" style="font-size:18px;">auto_awesome</span>
    </div>
    <div class="bot-bubble-wrap">
      <div class="bot-bubble">
        <div class="verified-header">
          <span class="material-symbols-outlined icon-filled">check_circle</span>
          Verified Answer ${piiHtml}
        </div>
        <div class="answer-body">${formatAnswer(answer)}</div>
        ${warningsHtml}
        ${sourceHtml}
      </div>
      <div class="response-footer">Last updated from sources: ${escHtml(updated_date)}. Source: groww.in</div>
      <div class="interaction-bar">
        <button class="interact-btn" title="Helpful"><span class="material-symbols-outlined">thumb_up</span></button>
        <button class="interact-btn" title="Not helpful"><span class="material-symbols-outlined">thumb_down</span></button>
        <button class="interact-btn" title="Copy" onclick="copyText(this, this.closest('.bot-bubble-wrap').querySelector('.answer-body').innerText)">
          <span class="material-symbols-outlined">content_copy</span>
        </button>
        <button class="interact-btn" title="Share"><span class="material-symbols-outlined">share</span></button>
      </div>
    </div>`;
  canvas.appendChild(row);

  if (save) {
    const session = chatSessions.find(s => s.id === activeSessionId);
    if (session) {
      session.messages.push({ type: "bot", data });
      saveChats();
    }
  }
}

function appendAdvisoryBubble(answer, sourceUrl, save = true) {
  const row = document.createElement("div");
  row.className = "msg-row";
  row.innerHTML = `
    <div class="bot-avatar">
      <span class="material-symbols-outlined icon-filled" style="font-size:18px;">auto_awesome</span>
    </div>
    <div class="bot-bubble-wrap">
      <div class="advisory-bubble">
        <div class="advisory-header">
          <span class="material-symbols-outlined icon-filled">shield</span>
          Advisory Query Detected
        </div>
        <p>${escHtml(answer)}</p>
        <a class="advisory-link" href="${escHtml(sourceUrl || 'https://www.amfiindia.com/investor-corner/investor-education')}" target="_blank" rel="noopener">
          <span class="material-symbols-outlined">school</span>
          Visit AMFI Investor Education →
        </a>
      </div>
      <div class="interaction-bar">
        <button class="interact-btn" title="Helpful"><span class="material-symbols-outlined">thumb_up</span></button>
        <button class="interact-btn" title="Not helpful"><span class="material-symbols-outlined">thumb_down</span></button>
      </div>
    </div>`;
  canvas.appendChild(row);

  if (save) {
    const session = chatSessions.find(s => s.id === activeSessionId);
    if (session) {
      session.messages.push({ type: "advisory", text: answer, sourceUrl });
      saveChats();
    }
  }
}

function appendErrorBubble(message, save = true) {
  const row = document.createElement("div");
  row.className = "msg-row";
  row.innerHTML = `
    <div class="bot-avatar" style="border-color:rgba(255,100,100,0.3); background:rgba(255,100,100,0.07); color:#ff6b6b;">
      <span class="material-symbols-outlined" style="font-size:18px;">error</span>
    </div>
    <div class="bot-bubble-wrap">
      <div class="error-bubble">${escHtml(message)}</div>
    </div>`;
  canvas.appendChild(row);

  if (save) {
    const session = chatSessions.find(s => s.id === activeSessionId);
    if (session) {
      session.messages.push({ type: "error", text: message });
      saveChats();
    }
  }
}

/* ── Helpers ─────────────────────────────────────────────────────── */
function formatAnswer(text) {
  return escHtml(text)
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
}

function escHtml(s) {
  if (!s) return "";
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function copyText(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    const icon = btn.querySelector(".material-symbols-outlined");
    icon.textContent = "check";
    icon.style.color = "var(--primary)";
    setTimeout(() => { icon.textContent = "content_copy"; icon.style.color = ""; }, 1800);
  }).catch(() => {});
}

/* ── Rate limit toast ────────────────────────────────────────────── */
function showToast(msg) {
  toastEl.querySelector(".toast-msg").textContent =
    msg || "High demand detected — retrying Groq API…";
  toastEl.classList.add("visible");
  setTimeout(hideToast, 6000);
}
function hideToast() { toastEl.classList.remove("visible"); }
