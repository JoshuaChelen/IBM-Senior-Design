// AI-Generated Code — Claude Sonnet 4.6 (Anthropic, claude.ai)
// Reviewed and tested by the development team.

/**
 * stress_test_script.js
 *
 * NLIP client for the Performance Stress Testing Agent.
 * Handles sending messages to the NLIP server, parsing responses,
 * rendering analysis results, and managing the sidebar.
 *
 * Uses NLIPClient, NLIPFactory, and AllowedFormats from nlip.js (nlip_web repo).
 *
 * Two response types are handled:
 *   - analysis_result: structured JSON submessage containing the full pipeline output
 *   - plain text: follow-up answers and error messages
 */

import { NLIPClient, NLIPFactory, AllowedFormats } from "./nlip.js";

const client  = new NLIPClient(window.location.origin);
const form    = document.getElementById("chat-form");
const input   = document.getElementById("user-input");
const chatBox = document.getElementById("chat-box");
const sidebar = document.getElementById("result-panel");
const dlBtn   = document.getElementById("dl-btn");
const badge   = document.getElementById("state-badge");

let currentResult = null;
let sessionState  = "AWAITING_DESCRIPTION";

// ── Send ─────────────────────────────────────────────────────────────────────
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  appendUserBubble(message);
  input.value = "";
  setInputEnabled(false);
  const botBox = appendBotPlaceholder();

  try {
    // Build NLIP message, attaching correlator token for session continuity
    const msg = NLIPFactory.createText(message);
    if (client.correlator != null) msg.addConversationToken(client.correlator);
    const raw = await client.send(msg);
    console.log("RAW NLIP RESPONSE:", raw);

    let respMsg    = null;
    let text       = "";
    let submessages = [];

    try {
      respMsg     = NLIPFactory.createMessageFromJSON(raw);
      client.correlator = respMsg.extractConversationToken(); // persist for next turn
      text        = respMsg.extractText();
      submessages = respMsg.submessages || [];
    } catch (parseErr) {
      // Fallback if NLIP parsing fails — extract content directly from raw response
      console.warn("Could not parse response with NLIPFactory. Falling back to raw response.", parseErr);
      text        = raw?.content || raw?.message || raw?.response || JSON.stringify(raw, null, 2);
      submessages = raw?.submessages || [];
    }

    // Check for analysis_result submessage — present after pipeline completes
    const jsonSubmsg = submessages.find(
      (sm) =>
        (sm.format === AllowedFormats.structured || sm.format === "structured") &&
        sm.label === "analysis_result",
    );

    if (jsonSubmsg) {
      // Parse and render the full analysis result
      currentResult =
        typeof jsonSubmsg.content === "string"
          ? JSON.parse(jsonSubmsg.content)
          : jsonSubmsg.content;

      sessionState = "AWAITING_FOLLOWUP";
      botBox.innerHTML = formatSummaryText(text);
      renderSidebar(currentResult);
      input.placeholder = "Ask a follow-up, or type 'no' to end...";
    } else {
      // Plain text response (follow-up answer, error, or status message)
      botBox.innerHTML = formatSummaryText(text || "No response");
    }

    updateBadge(sessionState);
  } catch (err) {
    botBox.textContent = `Frontend error: ${err.message || err}`;
    console.error(err);
  }

  setInputEnabled(true);
  input.focus();
});

// ── DOM helpers ──────────────────────────────────────────────────────────────

/** Appends a right-aligned user message bubble to the chat. */
function appendUserBubble(text) {
  const pair   = document.createElement("div");
  pair.className = "message-pair";
  const bubble = document.createElement("div");
  bubble.className = "user-bubble";
  bubble.textContent = text;
  pair.appendChild(bubble);
  chatBox.appendChild(pair);
  chatBox.scrollTop = chatBox.scrollHeight;
}

/** Appends a left-aligned agent placeholder with a typing indicator, returns the box element. */
function appendBotPlaceholder() {
  const pair = document.createElement("div");
  pair.className = "message-pair";
  const box  = document.createElement("div");
  box.className = "bot-box";
  box.innerHTML = '<span class="typing">...</span>';
  pair.appendChild(box);
  chatBox.appendChild(pair);
  chatBox.scrollTop = chatBox.scrollHeight;
  return box;
}

/**
 * Escapes HTML and converts newlines to <br> tags.
 * Also wraps Unicode block characters (bar fill/empty) in styled spans.
 */
function formatSummaryText(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>")
    .replace(/(█+)(░+)/g, '<span class="bar-fill">$1</span><span class="bar-empty">$2</span>');
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

/**
 * Renders the analysis summary panel in the sidebar.
 * Shows bottleneck, max lambda, and utilization bars for baseline and what-if scenarios.
 * Color coding: green (<60%), yellow (60-85%), red (>85%).
 */
function renderSidebar(result) {
  const r = result?.result || result || {};
  sidebar.style.display = "flex";

  let html = `<div class="panel-label">ANALYSIS SUMMARY</div>`;

  if (r.bottleneck) {
    html += `
      <div class="metric-row">
        <span class="metric-key">Bottleneck</span>
        <span class="metric-val hot">${r.bottleneck}</span>
      </div>`;
  }
  if (r.max_lambda != null) {
    html += `
      <div class="metric-row">
        <span class="metric-key">Max safe λ</span>
        <span class="metric-val">${Number(r.max_lambda).toFixed(4)}</span>
      </div>`;
  }

  const baseUtils = r.baseline?.utilizations || {};
  if (Object.keys(baseUtils).length) {
    html += `<div class="panel-section">Baseline ρ</div>`;
    for (const [q, v] of Object.entries(baseUtils)) {
      html += utilBar(q, v);
    }
  }

  const whatIfUtils = r.what_if?.utilizations || {};
  if (Object.keys(whatIfUtils).length) {
    html += `<div class="panel-section">What-if ρ</div>`;
    for (const [q, v] of Object.entries(whatIfUtils)) {
      html += utilBar(q, v);
    }
  }

  sidebar.innerHTML = html;
  dlBtn.style.display = "block";
}

/** Builds a single utilization bar row with color-coded fill. */
function utilBar(name, value) {
  const pct   = Math.min(value * 100, 100);
  const color = pct > 85 ? "#ff6b35" : pct > 60 ? "#ffd166" : "#06d6a0";
  return `
    <div class="util-row">
      <span class="util-name" title="${name}">${name}</span>
      <div class="util-track">
        <div class="util-fill" style="width:${pct}%;background:${color}"></div>
      </div>
      <span class="util-pct" style="color:${color}">${pct.toFixed(1)}%</span>
    </div>`;
}

// ── Download ──────────────────────────────────────────────────────────────────

/** Downloads the current analysis result as a timestamped JSON file. */
dlBtn.addEventListener("click", () => {
  if (!currentResult) return;
  const blob = new Blob([JSON.stringify(currentResult, null, 2)], { type: "application/json" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = `stress-test-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
});

// ── Misc ──────────────────────────────────────────────────────────────────────

/** Enables or disables the input and send button. */
function setInputEnabled(on) {
  input.disabled = !on;
  form.querySelector("button").disabled = !on;
}

/** Updates the session state badge in the header. */
function updateBadge(state) {
  badge.textContent = state.replace(/_/g, " ");
  badge.className   = "state-badge " + (state === "AWAITING_FOLLOWUP" ? "ready" : "waiting");
}

// Enter submits, Shift+Enter inserts a newline
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});